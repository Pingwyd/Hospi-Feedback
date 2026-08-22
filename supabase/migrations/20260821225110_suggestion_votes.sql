-- One upvote per hashed device fingerprint per suggestion report.

CREATE TABLE public.suggestion_votes (
  report_id UUID NOT NULL REFERENCES public.reports (id) ON DELETE CASCADE,
  voter_fingerprint_hash TEXT NOT NULL,
  PRIMARY KEY (report_id, voter_fingerprint_hash)
);

COMMENT ON COLUMN public.suggestion_votes.voter_fingerprint_hash IS
  'One-way hash of a device fingerprint. Never store plaintext.';
