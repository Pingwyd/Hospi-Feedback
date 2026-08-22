-- Admin action audit trail. detail JSONB is the escape hatch via action=other.
-- Do not put plaintext ticket codes or Telegram identifiers in detail.

CREATE TABLE public.audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID REFERENCES public.admins (id) ON DELETE SET NULL,
  report_id UUID REFERENCES public.reports (id) ON DELETE CASCADE,
  action TEXT NOT NULL CHECK (action IN (
    'viewed',
    'status_changed',
    'assigned',
    'message_sent',
    'note_added',
    'exported',
    'escalated',
    'closed',
    'marked_false',
    'deleted',
    'other'
  )),
  detail JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
