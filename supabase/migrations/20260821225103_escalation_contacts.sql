-- External escalation contacts. Configurable, not hardcoded.

CREATE TABLE public.escalation_contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  role_label TEXT NOT NULL,
  contact_email TEXT,
  contact_phone TEXT,
  active BOOLEAN DEFAULT TRUE
);
