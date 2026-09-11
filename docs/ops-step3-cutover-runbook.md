# Step 3: Production Cutover Runbook (DO NOT EXECUTE UNTIL APPROVED)

This runbook is prep only. Steps 1 and 2 (internal jobs) can merge without running this.

## External gates (all required)

- [ ] Admin dashboard merged to `dev` and signed off (done: PRs #6-#8)
- [ ] Explicit user approval: "go for production cutover"
- [ ] User confirms: no local polling session is running against the production Telegram token

## Pre-cutover checks

1. Stop any local `python -m bot.main` using the production token.
2. Call Telegram `getWebhookInfo` and confirm no active webhook (or note current URL for rollback).
3. Confirm staging `X_INTERNAL_JOB_SECRET` differs from production (never commit either value).
4. Apply migration `20260912120000_system_alerts_and_escalation_exports_bucket.sql` on production Supabase.

## Cutover sequence (one-time)

1. Deploy `hospi-api` from `infra/render/render.yaml` with production env vars.
2. Verify `GET /health` returns 200.
3. Manually trigger `POST /internal/jobs/purge-cycle` with production secret against a test/staging project first if possible.
4. Deploy `hospi-bot` with `BOT_MODE=webhook` and `WEBHOOK_BASE_URL` set to the public bot service URL.
5. Confirm Telegram `setWebhook` succeeded (no 409 conflict).
6. Send a test report via production bot; confirm it appears in the production admin dashboard.
7. Enable Render cron jobs (purge-cycle, escalation-export purge, duplicate-scan, keep-warm).

## Post-cutover local dev

- Local bot development uses **polling only** against staging Supabase.
- Never run local polling against the production token after cutover.
- Use a disposable test token for local bot work if needed.

## Rollback

1. Stop Render bot service or set webhook to empty URL.
2. Re-run local polling against staging only (not production token).
3. Disable cron jobs if API is rolled back.
