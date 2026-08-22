-- RLS is a backstop. The FastAPI service role is the load-bearing access path.
-- anon and authenticated have no direct access except authenticated SELECT of
-- the caller's own admins row (profile read). Writes and cross-admin reads
-- stay in the backend so admin_permissions is enforced in one place.

ALTER TABLE public.admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.escalation_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rate_limit_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.internal_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.escalations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suggestion_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.archived_reports ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE
  public.admins,
  public.admin_permissions,
  public.categories,
  public.escalation_contacts,
  public.rate_limit_entries,
  public.reports,
  public.report_categories,
  public.attachments,
  public.messages,
  public.internal_notes,
  public.escalations,
  public.audit_log,
  public.suggestion_votes,
  public.archived_reports
FROM PUBLIC, anon, authenticated;

GRANT ALL ON TABLE
  public.admins,
  public.admin_permissions,
  public.categories,
  public.escalation_contacts,
  public.rate_limit_entries,
  public.reports,
  public.report_categories,
  public.attachments,
  public.messages,
  public.internal_notes,
  public.escalations,
  public.audit_log,
  public.suggestion_votes,
  public.archived_reports
TO service_role;

GRANT SELECT ON TABLE public.admins TO authenticated;

-- Reporter-facing tables: deny all direct client access.
CREATE POLICY reports_deny_client
  ON public.reports
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY messages_deny_client
  ON public.messages
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY attachments_deny_client
  ON public.attachments
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY suggestion_votes_deny_client
  ON public.suggestion_votes
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

-- Remaining tables: deny all direct client access.
CREATE POLICY admin_permissions_deny_client
  ON public.admin_permissions
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY categories_deny_client
  ON public.categories
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY report_categories_deny_client
  ON public.report_categories
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY escalation_contacts_deny_client
  ON public.escalation_contacts
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY rate_limit_entries_deny_client
  ON public.rate_limit_entries
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY internal_notes_deny_client
  ON public.internal_notes
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY escalations_deny_client
  ON public.escalations
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY audit_log_deny_client
  ON public.audit_log
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY archived_reports_deny_client
  ON public.archived_reports
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

-- Admins: anon denied. authenticated may read only their own row. No writes.
CREATE POLICY admins_deny_anon
  ON public.admins
  FOR ALL
  TO anon
  USING (false)
  WITH CHECK (false);

CREATE POLICY admins_select_own
  ON public.admins
  FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = id);

CREATE POLICY admins_deny_authenticated_insert
  ON public.admins
  FOR INSERT
  TO authenticated
  WITH CHECK (false);

CREATE POLICY admins_deny_authenticated_update
  ON public.admins
  FOR UPDATE
  TO authenticated
  USING (false)
  WITH CHECK (false);

CREATE POLICY admins_deny_authenticated_delete
  ON public.admins
  FOR DELETE
  TO authenticated
  USING (false);
