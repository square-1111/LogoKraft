-- Create generated_assets table
CREATE TABLE generated_assets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id UUID REFERENCES brand_projects(id) ON DELETE CASCADE NOT NULL,
    parent_asset_id UUID REFERENCES generated_assets(id) ON DELETE SET NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('logo_concept', 'mockup_business_card', 'variation', 'edit')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
    asset_url TEXT,
    generation_prompt TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_generated_assets_project_id ON generated_assets(project_id);
CREATE INDEX idx_generated_assets_parent_asset_id ON generated_assets(parent_asset_id);
CREATE INDEX idx_generated_assets_status ON generated_assets(status);

-- Create updated_at trigger for generated_assets
CREATE TRIGGER update_generated_assets_updated_at 
    BEFORE UPDATE ON generated_assets 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE generated_assets ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for generated_assets
CREATE POLICY "Users can view assets from their own projects" ON generated_assets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM brand_projects 
            WHERE brand_projects.id = generated_assets.project_id 
            AND brand_projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert assets to their own projects" ON generated_assets
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM brand_projects 
            WHERE brand_projects.id = generated_assets.project_id 
            AND brand_projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update assets from their own projects" ON generated_assets
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM brand_projects 
            WHERE brand_projects.id = generated_assets.project_id 
            AND brand_projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete assets from their own projects" ON generated_assets
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM brand_projects 
            WHERE brand_projects.id = generated_assets.project_id 
            AND brand_projects.user_id = auth.uid()
        )
    );