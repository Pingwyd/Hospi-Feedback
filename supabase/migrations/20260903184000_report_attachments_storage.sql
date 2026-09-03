-- Private bucket for reporter image attachments.
-- anon and authenticated cannot read or write objects here; the FastAPI
-- service_role key is the only load-bearing upload/download path.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'report-attachments',
  'report-attachments',
  false,
  5242880,
  ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET
  public = EXCLUDED.public,
  file_size_limit = EXCLUDED.file_size_limit,
  allowed_mime_types = EXCLUDED.allowed_mime_types;

CREATE POLICY report_attachments_deny_anon
  ON storage.objects
  FOR ALL
  TO anon
  USING (bucket_id <> 'report-attachments')
  WITH CHECK (bucket_id <> 'report-attachments');

CREATE POLICY report_attachments_deny_authenticated
  ON storage.objects
  FOR ALL
  TO authenticated
  USING (bucket_id <> 'report-attachments')
  WITH CHECK (bucket_id <> 'report-attachments');
