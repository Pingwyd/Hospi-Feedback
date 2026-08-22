-- Post-purge metadata for both scheduled purge and HOH admin delete.
-- original_report_id and handled_by_admin_id have no foreign keys on purpose.

CREATE TABLE public.archived_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_report_id UUID,
  ticket_code_hash TEXT,
  categories TEXT[],
  status_history JSONB,
  resolution_summary TEXT,
  handled_by_admin_id UUID,
  archive_reason TEXT NOT NULL CHECK (archive_reason IN (
    'scheduled_purge',
    'admin_deleted'
  )),
  deleted_by_admin_id UUID NULL REFERENCES public.admins (id) ON DELETE SET NULL,
  delete_reason TEXT NULL,
  created_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT archived_reports_admin_delete_requires_reason
    CHECK (archive_reason <> 'admin_deleted' OR delete_reason IS NOT NULL)
);

COMMENT ON COLUMN public.archived_reports.ticket_code_hash IS
  'One-way hash copied from the original report. Never plaintext.';

COMMENT ON COLUMN public.archived_reports.archive_reason IS
  'Single archive path: scheduled_purge or admin_deleted.';
