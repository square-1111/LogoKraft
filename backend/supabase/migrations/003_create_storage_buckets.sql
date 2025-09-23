-- Create storage buckets for file uploads
INSERT INTO storage.buckets (id, name, public) VALUES ('inspiration-images', 'inspiration-images', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('generated-assets', 'generated-assets', false);

-- Create storage policies for inspiration-images bucket
CREATE POLICY "Users can upload their own inspiration images" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'inspiration-images' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can view their own inspiration images" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'inspiration-images' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can update their own inspiration images" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'inspiration-images' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own inspiration images" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'inspiration-images' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Create storage policies for generated-assets bucket
CREATE POLICY "Users can upload to their own generated assets" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'generated-assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can view their own generated assets" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'generated-assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can update their own generated assets" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'generated-assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own generated assets" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'generated-assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );