-- Dashboard-visible system alerts (e.g. purge PDF delivery failures).
-- Escalation export files live in a separate, stricter-access bucket.

CREATE TABLE public.system_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_type TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  dismissed_at TIMESTAMPTZ
);

COMMENT ON TABLE public.system_alerts IS
  'Operational alerts surfaced on the admin dashboard. Not report content.';

CREATE INDEX idx_system_alerts_active
  ON public.system_alerts (created_at DESC)
  WHERE dismissed_at IS NULL;

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'escalation-exports',
  'escalation-exports',
  false,
  10485760,
  ARRAY['application/pdf']
)
ON CONFLICT (id) DO UPDATE SET
  public = EXCLUDED.public,
  file_size_limit = EXCLUDED.file_size_limit,
  allowed_mime_types = EXCLUDED.allowed_mime_types;

CREATE POLICY escalation_exports_deny_anon
  ON storage.objects
  FOR ALL
  TO anon
  USING (bucket_id <> 'escalation-exports')
  WITH CHECK (bucket_id <> 'escalation-exports');

CREATE POLICY escalation_exports_deny_authenticated
  ON storage.objects
  FOR ALL
  TO authenticated
  USING (bucket_id <> 'escalation-exports')
  WITH CHECK (bucket_id <> 'escalation-exports');
