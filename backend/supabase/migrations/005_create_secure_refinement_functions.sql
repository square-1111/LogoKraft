-- Migration: Create secure RPC functions for refinement operations
-- These functions enforce Row-Level Security and provide atomic operations

-- Function to create multiple refinement assets in a batch with security validation
CREATE OR REPLACE FUNCTION create_refinement_assets_batch(
    p_user_id UUID,
    p_original_asset_id UUID,
    p_variations JSONB
) RETURNS TABLE (
    asset_id UUID,
    asset_type TEXT,
    status TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Verify user owns the original asset by checking project ownership
    IF NOT EXISTS (
        SELECT 1 FROM generated_assets ga
        JOIN brand_projects bp ON ga.project_id = bp.id
        WHERE ga.id = p_original_asset_id AND bp.user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'Access denied: User does not own the original asset';
    END IF;

    -- Create refinement assets batch
    RETURN QUERY
    INSERT INTO generated_assets (
        project_id,
        parent_asset_id,
        asset_type,
        status,
        generation_prompt,
        refinement_metadata,
        created_at,
        updated_at
    )
    SELECT 
        (SELECT project_id FROM generated_assets WHERE id = p_original_asset_id),
        p_original_asset_id,
        'simple_refinement'::TEXT,
        'generating'::TEXT,
        (variation->>'prompt')::TEXT,
        variation,
        NOW(),
        NOW()
    FROM jsonb_array_elements(p_variations) AS variation
    RETURNING id AS asset_id, asset_type, status;
END;
$$;

-- Function to check if user has sufficient credits
CREATE OR REPLACE FUNCTION check_user_credits(
    p_user_id UUID,
    p_required_credits INTEGER
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    current_credits INTEGER;
BEGIN
    -- Get current credit balance
    SELECT COALESCE(credits, 0) INTO current_credits
    FROM user_credits 
    WHERE user_id = p_user_id;

    -- Return true if user has sufficient credits
    RETURN current_credits >= p_required_credits;
END;
$$;

-- Function to deduct credits atomically with audit trail
CREATE OR REPLACE FUNCTION deduct_user_credits(
    p_user_id UUID,
    p_credits INTEGER,
    p_reason TEXT,
    p_asset_id UUID DEFAULT NULL
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    current_credits INTEGER;
    transaction_id UUID;
BEGIN
    -- Get current credit balance with row lock
    SELECT COALESCE(credits, 0) INTO current_credits
    FROM user_credits 
    WHERE user_id = p_user_id
    FOR UPDATE;

    -- Check if sufficient credits (for positive deductions)
    IF p_credits > 0 AND current_credits < p_credits THEN
        RETURN FALSE;
    END IF;

    -- Generate transaction ID
    transaction_id := gen_random_uuid();

    -- Insert credit transaction record
    INSERT INTO credit_transactions (
        id,
        user_id,
        credits,
        transaction_type,
        reason,
        asset_id,
        created_at
    ) VALUES (
        transaction_id,
        p_user_id,
        -p_credits, -- Negative for deductions, positive for refunds
        CASE WHEN p_credits > 0 THEN 'deduction' ELSE 'refund' END,
        p_reason,
        p_asset_id,
        NOW()
    );

    -- Update user credits
    INSERT INTO user_credits (user_id, credits, updated_at)
    VALUES (p_user_id, current_credits - p_credits, NOW())
    ON CONFLICT (user_id) 
    DO UPDATE SET 
        credits = user_credits.credits - p_credits,
        updated_at = NOW();

    RETURN TRUE;
END;
$$;

-- Create credit-related tables if they don't exist

-- User credits table
CREATE TABLE IF NOT EXISTS user_credits (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    credits INTEGER NOT NULL DEFAULT 100, -- Start users with 100 credits
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credit transactions table for audit trail
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    credits INTEGER NOT NULL, -- Positive for additions, negative for deductions
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('deduction', 'refund', 'purchase', 'bonus')),
    reason TEXT NOT NULL,
    asset_id UUID REFERENCES generated_assets(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on new tables
ALTER TABLE user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

-- RLS policies for user_credits (users can only see their own credits)
CREATE POLICY user_credits_select_own ON user_credits
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY user_credits_update_own ON user_credits
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS policies for credit_transactions (users can only see their own transactions)
CREATE POLICY credit_transactions_select_own ON credit_transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION create_refinement_assets_batch(UUID, UUID, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION check_user_credits(UUID, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION deduct_user_credits(UUID, INTEGER, TEXT, UUID) TO authenticated;

-- Add helpful comments
COMMENT ON FUNCTION create_refinement_assets_batch IS 'Securely create multiple refinement assets with ownership validation';
COMMENT ON FUNCTION check_user_credits IS 'Check if user has sufficient credits for an operation';
COMMENT ON FUNCTION deduct_user_credits IS 'Atomically deduct credits with audit trail (use negative values for refunds)';

COMMENT ON TABLE user_credits IS 'User credit balances with RLS protection';
COMMENT ON TABLE credit_transactions IS 'Audit trail of all credit transactions with RLS protection';