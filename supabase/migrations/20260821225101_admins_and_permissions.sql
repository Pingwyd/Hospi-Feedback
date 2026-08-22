-- Admins and per-admin permissions.
-- admins.id matches auth.users(id). Inserts must pass the Auth user id;
-- DEFAULT gen_random_uuid() is unused on the real create path because the
-- row cannot exist without a matching auth.users row.
-- telegram_chat_id_encrypted is reversible app-level encryption for sendMessage.
-- It is not a one-way hash. Do not store reporter Telegram identifiers here.

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

CREATE TABLE public.admins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid()
    REFERENCES auth.users (id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  role TEXT CHECK (role IN (
    'hoh',
    'asst_head',
    'gen_sec',
    'fin_sec',
    'subunit_head',
    'subunit_asst',
    'custom'
  )),
  subunit TEXT NULL,
  aliases TEXT[] DEFAULT '{}',
  telegram_chat_id_encrypted TEXT NULL,
  notification_pref TEXT CHECK (notification_pref IN (
    'instant',
    'hourly',
    'daily'
  )) DEFAULT 'instant',
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.admin_permissions (
  admin_id UUID NOT NULL REFERENCES public.admins (id) ON DELETE CASCADE,
  permission TEXT NOT NULL CHECK (permission IN (
    'view',
    'respond',
    'assign',
    'close',
    'export',
    'manage_categories',
    'manage_admins',
    'manage_escalation_contacts'
  )),
  PRIMARY KEY (admin_id, permission)
);

COMMENT ON COLUMN public.admins.telegram_chat_id_encrypted IS
  'Reversible symmetric encryption for admin Telegram sendMessage. Not a hash. Never used for reporters.';

COMMENT ON COLUMN public.admins.aliases IS
  'Known nicknames for recusal fuzzy-match warnings. Not reporter identity.';
