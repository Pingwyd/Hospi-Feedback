-- Reports. ticket_code_hash is one-way; never store the plaintext ticket code.
-- reported_member_admin_id is optional and set only by manual triage.

CREATE TABLE public.reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_code_hash TEXT UNIQUE NOT NULL,
  source TEXT CHECK (source IN ('web', 'telegram')),
  report_type TEXT CHECK (report_type IN (
    'complaint',
    'suggestion',
    'recognition'
  )),
  reported_member_name TEXT,
  reported_member_admin_id UUID REFERENCES public.admins (id) ON DELETE SET NULL,
  description TEXT NOT NULL,
  incident_date DATE,
  incident_location TEXT,
  severity TEXT CHECK (severity IN ('low', 'medium', 'high')) NULL,
  status TEXT CHECK (status IN (
    'new',
    'under_review',
    'assigned',
    'in_progress',
    'resolved',
    'escalated',
    'closed',
    'marked_false'
  )) DEFAULT 'new',
  assigned_admin_id UUID REFERENCES public.admins (id) ON DELETE SET NULL,
  publish_shoutout BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  possible_duplicate_of UUID REFERENCES public.reports (id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reports_set_updated_at
  BEFORE UPDATE ON public.reports
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();

COMMENT ON COLUMN public.reports.ticket_code_hash IS
  'One-way hash of the ticket code. Plaintext must never be stored.';

COMMENT ON COLUMN public.reports.reported_member_admin_id IS
  'Optional manual triage link for recusal. Null until an admin confirms the match.';
