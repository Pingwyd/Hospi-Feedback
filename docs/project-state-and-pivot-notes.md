# Project State and Pivot Notes

Living notes for schema and operational decisions that extend beyond the original Phase 1 spec. Read this before assuming the database matches `hospi-feedback-spec-v2.md` section 4 alone.

## Schema additions (post Phase 1)

### `rate_limit_entries` (Phase 2)

- **Migration:** `supabase/migrations/20260821225104_rate_limit_entries.sql`
- **Why:** API-side rate limiting counters for web fingerprints and hashed Telegram IDs. Not in the original spec prose but required by section 3 abuse prevention.
- **Access:** Service role only (RLS deny for anon/authenticated).

### `system_alerts` (Phase 5 / retention jobs, Step 1)

- **Migration:** `supabase/migrations/20260912120000_system_alerts_and_escalation_exports_bucket.sql`
- **Why:** Operational alerts that must survive page refresh and surface on the admin dashboard. Introduced for purge-cycle PDF delivery failures: when HOH has no linked Telegram, a log line alone would be a silent failure on unattended retention machinery.
- **Columns:** `alert_type`, `message`, `created_at`, `dismissed_at` (null = active).
- **First use:** `purge_pdf_undelivered` when scheduled purge summary PDF cannot be sent via Telegram.
- **Access:** Service role only (no client RLS policies; API reads via service role for dashboard stats).

### `escalation-exports` storage bucket (Phase 5 / retention jobs, Step 1)

- **Migration:** same file as `system_alerts` above.
- **Why:** Spec section 10 requires escalation export files in a separate, stricter-access bucket, independent of report-content purge.
- **Access:** Service role only (deny policies for anon/authenticated, same pattern as `report-attachments`).
