-- Abuse-prevention counters for web fingerprints and Telegram chat ids.
-- identifier_hash is a one-way hash only, same family as reports.ticket_code_hash.
-- No foreign keys: correlating these rows with reports or admins is forbidden.

CREATE TABLE public.rate_limit_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel TEXT NOT NULL CHECK (channel IN ('web', 'telegram')),
  identifier_hash TEXT NOT NULL,
  window_start TIMESTAMPTZ NOT NULL DEFAULT now(),
  request_count INT NOT NULL DEFAULT 1,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rate_limit_entries_channel_identifier_hash
  ON public.rate_limit_entries (channel, identifier_hash);

COMMENT ON COLUMN public.rate_limit_entries.identifier_hash IS
  'One-way hash of a web fingerprint or Telegram chat id. Never store plaintext. Never join to reports.';
