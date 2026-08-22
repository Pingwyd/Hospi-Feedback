-- Reporter-admin ticket thread, and admin-only internal notes.
-- sender_admin_id is null for reporter messages.

CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID REFERENCES public.reports (id) ON DELETE CASCADE,
  sender_type TEXT CHECK (sender_type IN ('reporter', 'admin')),
  sender_admin_id UUID REFERENCES public.admins (id) ON DELETE SET NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.internal_notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID REFERENCES public.reports (id) ON DELETE CASCADE,
  admin_id UUID REFERENCES public.admins (id) ON DELETE SET NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
