-- Keep audit_log rows when a report is archived and removed.
-- Admin delete writes the deleted audit row before archive_report() removes the report.

ALTER TABLE public.audit_log
  DROP CONSTRAINT IF EXISTS audit_log_report_id_fkey;

ALTER TABLE public.audit_log
  ADD CONSTRAINT audit_log_report_id_fkey
  FOREIGN KEY (report_id)
  REFERENCES public.reports (id)
  ON DELETE SET NULL;
