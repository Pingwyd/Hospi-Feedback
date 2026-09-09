-- One-time codes for linking an admin Telegram chat id to an admins row.
-- Plaintext codes never touch storage; only code_hash is stored.

CREATE TABLE public.telegram_link_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID NOT NULL REFERENCES public.admins (id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_telegram_link_codes_code_hash
  ON public.telegram_link_codes (code_hash);

CREATE INDEX idx_telegram_link_codes_admin_id
  ON public.telegram_link_codes (admin_id);

COMMENT ON TABLE public.telegram_link_codes IS
  'Single-use, short-lived codes for POST /api/admin/telegram/link from the bot.';

ALTER TABLE public.telegram_link_codes ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.telegram_link_codes FROM PUBLIC, anon, authenticated;

GRANT ALL ON TABLE public.telegram_link_codes TO service_role;

CREATE POLICY telegram_link_codes_deny_client
  ON public.telegram_link_codes
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);
