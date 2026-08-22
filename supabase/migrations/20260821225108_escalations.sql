-- Escalation records. exported_file_path lives in a stricter Storage bucket.
-- export_retention_until is independent of the 30-day report purge window.
-- report_id SET NULL (not CASCADE) so deleting a report keeps the export retention row.

CREATE TABLE public.escalations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID REFERENCES public.reports (id) ON DELETE SET NULL,
  escalation_contact_id UUID REFERENCES public.escalation_contacts (id),
  escalated_by_admin_id UUID REFERENCES public.admins (id) ON DELETE SET NULL,
  exported_file_path TEXT,
  export_retention_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON COLUMN public.escalations.export_retention_until IS
  'Independent retention for files already shared externally. Not the 30-day report purge.';
