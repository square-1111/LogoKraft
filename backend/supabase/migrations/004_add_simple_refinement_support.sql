-- Migration: Add simple refinement support to generated_assets table
-- Adds new asset type and metadata field for simple refinement tracking

-- Add 'simple_refinement' to the asset_type constraint
ALTER TABLE generated_assets DROP CONSTRAINT IF EXISTS generated_assets_asset_type_check;
ALTER TABLE generated_assets ADD CONSTRAINT generated_assets_asset_type_check 
    CHECK (asset_type IN ('logo_concept', 'mockup_business_card', 'variation', 'edit', 'simple_refinement'));

-- Add refinement_metadata column to store refinement-specific data
ALTER TABLE generated_assets ADD COLUMN IF NOT EXISTS refinement_metadata JSONB;

-- Create index on refinement_metadata for better query performance
CREATE INDEX IF NOT EXISTS idx_generated_assets_refinement_metadata 
    ON generated_assets USING GIN (refinement_metadata);

-- Add comment explaining the new fields
COMMENT ON COLUMN generated_assets.refinement_metadata IS 
    'JSON metadata for refinements: {user_prompt, variation_index, refinement_method, original_asset_id}';

-- Add sample data structure comment for future reference
/*
refinement_metadata structure for simple_refinement:
{
    "user_prompt": "make it more modern",
    "variation_index": 1,
    "refinement_method": "simple",
    "original_asset_id": "uuid-of-original-asset"
}
*/