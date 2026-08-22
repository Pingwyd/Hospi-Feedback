# Hospi Feedback System — Master Execution Plan

**Purpose:** This is the build sequence for an AI coding agent (OpenCode) to follow, derived from `hospi-feedback-spec-v2.md`. It is a companion document, not a replacement — the spec is the source of truth for *what* to build; this document is the *order and dependency graph* for building it.

**How to use this doc:** Work top to bottom. Do not skip ahead to a later phase's tasks even if they look easy — most later phases assume earlier ones are done and tested. Each phase has a **Definition of Done** — do not mark a phase complete until every item in it is true. Testing is not a separate phase at the end; it's threaded into every phase below (see the "Test" line in each phase).

**Before starting anything:** read `hospi-feedback-spec-v2.md` in full, once, start to finish. Do not begin coding from a partial read.

---

## Phase 0 — Repo & Tooling Scaffold

**Goal:** A running, empty skeleton that lints, type-checks, and deploys — before a single feature exists.

**Tasks:**
1. Create monorepo structure:
   ```
   hospi-feedback/
   ├── apps/web/          # Next.js (App Router, TypeScript)
   ├── apps/api/          # FastAPI
   ├── apps/bot/          # python-telegram-bot
   ├── packages/shared-types/
   ├── infra/docker/
   ├── infra/supabase/migrations/
   ├── .github/workflows/
   └── docker-compose.yml
   ```
2. `apps/api`: FastAPI app with a single `GET /health` endpoint returning `{"status": "ok"}`. Add `ruff` + `mypy` config.
3. `apps/web`: Next.js app, TypeScript, App Router, single placeholder home page. Add `eslint` + `tsc --noEmit` script.
4. `apps/bot`: bot skeleton with `/start` echoing "bot alive" — no real logic yet.
5. `docker-compose.yml`: local Postgres + `api` + `bot`, hot-reload mounted.
6. Two Supabase projects created (staging, production) — empty, no schema yet.
7. `.env.example` at repo root covering every variable referenced anywhere in the spec (Supabase URL/keys, Telegram bot token, `X-Internal-Job-Secret`, JWT signing secret for the access-code session, encryption key for `telegram_chat_id_encrypted`). Real values go in Vercel/Render/GitHub Actions secret stores, never committed.
8. GitHub Actions workflow: on every PR, run lint + type-check + (empty) test suite for both `apps/api` and `apps/web`.
9. Vercel project pointed at `apps/web` (build root override). Render web service pointed at `apps/api`. Render background worker pointed at `apps/bot` — **but do not enable auto-deploy for the bot service yet** (see spec §6 operational note — bot testing is local-polling until Phase 6).
10. Branch strategy: `main` → production, `staging` → staging. Protect `main` (require passing CI).

**Test:** `docker-compose up` boots cleanly; `GET /health` returns 200 locally and on the deployed Render staging URL; CI passes on an empty PR.

**Definition of Done:**
- [ ] Repo pushed, CI green
- [ ] Vercel + Render staging deploys succeed on push to `staging`
- [ ] Both Supabase projects exist and are reachable
- [ ] `.env.example` is exhaustive against the spec (re-check after every later phase — this file drifts fast)

---

## Phase 1 — Database Layer

**Goal:** Full schema from spec §4 exists in both Supabase projects, as versioned migrations, with nothing hand-clicked in the dashboard.

**Tasks:**
1. Write every table in spec §4 as sequential SQL files in `infra/supabase/migrations/` (one migration per logical table group: reports, categories/attachments, messages/notes, admins/permissions, escalations, audit_log, suggestion_votes, archived_reports).
2. Apply migrations to **staging** first, verify, then production.
3. Set up Row Level Security (RLS) policies in Supabase:
   - Public tables (`reports`, `messages`, `attachments`, `suggestion_votes`) — no direct client access; **all access goes through the FastAPI backend using the service role key**, never the anon key from the frontend. This matters because ticket-code and access-code auth logic (spec §3) lives in the API layer, not in Postgres policies.
   - Admin tables — Supabase Auth used only for the admin dashboard login (spec §5 `/api/admin/login`), still proxied through the backend for permission checks (`admin_permissions`), not raw client-to-Postgres.
4. Seed script: a handful of default `categories` rows and one bootstrap HOH admin record for local dev.
5. Write the encryption helper for `admins.telegram_chat_id_encrypted` now (even though nothing uses it until Phase 4/6) — symmetric encryption (e.g. Fernet/AES-GCM), key from env, encrypt/decrypt functions unit-tested in isolation.

**Test:** Migrations apply cleanly to a fresh empty database (test this — not just to an already-migrated one). Round-trip test on the encryption helper (encrypt → decrypt → matches original).

**Definition of Done:**
- [ ] Schema matches spec §4 exactly, including the recusal (`reported_member_admin_id`, `aliases`), archive-unification (`archive_reason`), and escalation-retention (`export_retention_until`) fields from the v2 revision
- [ ] RLS confirmed to block direct anon-key access to sensitive tables
- [ ] Migrations are reproducible from scratch on both staging and prod

---

## Phase 2 — Backend Core: Auth & Session Layer

**Goal:** The access-code session mechanism (spec §3) and admin auth (Supabase Auth + 2FA) both work, before anything that depends on them is built.

**Tasks:**
1. `POST /api/access/verify` — validates the shared access code, issues the short-lived signed session token (JWT, ~24h, no PII payload). Set as httpOnly secure cookie for web.
2. Middleware/dependency in FastAPI that every public route in Phase 3 will use: reject requests without a valid session token. Build this now as a reusable dependency, not duplicated per-route later.
3. `POST /api/admin/login` — Supabase Auth email/password + 2FA enforcement. Reject login if 2FA isn't set up (spec §12 checklist item).
4. Admin auth middleware/dependency: resolves the authenticated admin, loads their `admin_permissions`, and exposes a `require_permission("...")` decorator for later admin routes.
5. Recusal-check helper function (spec §9): given an admin and a report, returns `blocked` (linked match), `warn` (fuzzy text match), or `clear`. Build and unit-test this now in isolation — Phase 4 will just call it.

**Test:** Unit tests for token issuance/expiry/rejection. Integration test: wrong access code → 401; expired token → 401; valid flow → 200 + cookie set. Same pattern for admin login + 2FA + permission checks. Recusal helper tested against linked-match, fuzzy-match, and no-match cases explicitly.

**Definition of Done:**
- [ ] No route in later phases needs to reinvent auth — both dependencies exist and are documented
- [ ] Recusal helper is a pure, tested function ready to be wired into status-change endpoints

---

## Phase 3 — Backend: Public Reporter API

**Goal:** A reporter can, entirely anonymously, submit a report, get a ticket code, check status, chat, and upload an attachment. This is the critical path — nothing else in the product matters if this doesn't work.

**Tasks (build in this order — each depends on the last):**
1. `POST /api/reports` — validates input, generates high-entropy ticket code, stores only `ticket_code_hash`, returns the raw code once. Enforce access-code session dependency from Phase 2.
2. `GET /api/reports/ticket/{code}` — hash the incoming code, look up, return status + chat thread. Return 404 (not 403) on wrong code — don't leak whether a code format is "close."
3. `POST /api/reports/ticket/{code}/message` — reporter chat message, `sender_type='reporter'`. Reject if report status is `closed` (spec §3 — code stops working once closed).
4. `POST /api/reports/ticket/{code}/attachments` — image-only, size-capped, validated by actual file content not extension, EXIF stripped before storage (spec §4). **Confirm this is scoped by ticket_code, not report UUID** — this was the critical fix from the v2 spec review; write a specific test asserting a valid-but-wrong ticket code cannot attach to a different report.
5. `GET /api/suggestions/public` + `POST /api/suggestions/{id}/upvote` — fingerprint-limited, one vote per device per report.
6. `GET /api/shoutouts/public` — only where `is_public = true`.
7. Rate limiting middleware: browser fingerprint for web routes, applied at this layer (Telegram-side rate limiting happens in Phase 6 against the bot's own traffic).

**Test:** Full submit → status-check → chat → close → verify-locked-out flow, end to end, as an integration test. Attachment ownership-boundary test (above) is non-negotiable — this was a flagged security issue, don't skip it.

**Definition of Done:**
- [ ] A reporter can complete the entire lifecycle via API calls alone (Postman/curl), no frontend needed yet
- [ ] Ticket code is never retrievable or loggable in plaintext anywhere except the single response at creation

---

## Phase 4 — Backend: Admin API

**Goal:** Admins can triage, respond to, and resolve reports, with permissions and the recusal rule enforced.

**Tasks:**
1. `GET /api/admin/reports` (filterable) and `GET /api/admin/reports/{id}` — permission-gated by `require_permission("view")`.
2. `PATCH /api/admin/reports/{id}/status`, `/assign`, `/mark-false` — each calls the Phase 2 recusal helper first; hard-block on `blocked`, prompt-and-log on `warn`.
3. `PATCH /api/admin/reports/{id}/link-member` — the new v2 endpoint; confirms `reported_member_name` → `reported_member_admin_id`. Requires `assign` permission.
4. `POST /api/admin/reports/{id}/notes` (internal, never reporter-visible) and `/message` (reporter-visible, mirrors Phase 3's reporter-side chat).
5. `POST /api/admin/reports/{id}/escalate` — generates redacted PDF/DOCX, stores in the separate stricter-access bucket (spec §10 v2), sets `export_retention_until`.
6. `DELETE /api/admin/reports/{id}` — HOH-only, calls the **unified** archive routine (build this routine now — Phase 9's scheduled purge job will reuse it rather than duplicating logic).
7. Categories, escalation-contacts, admins CRUD endpoints — straightforward permission-gated CRUD, build last in this phase since nothing else depends on them.
8. `GET /api/admin/audit-log` — HOH/Asst Head only. Every mutating action above must write an `audit_log` row as it's built, not retrofitted — bake this into a shared "log this action" helper used by every write endpoint in this phase.

**Test:** Recusal hard-block and soft-warn cases as integration tests against the real endpoints (not just the Phase 2 unit test). Confirm every mutating endpoint produces exactly one correctly-typed `audit_log` row. Confirm `DELETE` and the (not-yet-built) scheduled purge will share code — write the delete endpoint as a thin wrapper around a shared `archive_report(report_id, reason, admin_id=None)` function.

**Definition of Done:**
- [ ] Every admin endpoint from spec §5 exists and is permission-gated
- [ ] `archive_report()` shared function exists and is what Phase 9's purge job will call
- [ ] Audit log has full coverage — spot-check by attempting every endpoint and checking the log

---

## Phase 5 — Backend: Background Jobs & Notifications

**Goal:** Purge cycle, duplicate scan, and the notification dispatch layer exist and are callable, before the frontend/bot need to trigger or display them.

**Tasks:**
1. `POST /internal/jobs/purge-cycle` — calls the shared `archive_report()` from Phase 4 for every report older than the retention window, batches results into a PDF, emails/sends to HOH. Gated by `X-Internal-Job-Secret` (spec §5 v2 fix).
2. `POST /internal/jobs/duplicate-scan` — flags `possible_duplicate_of` based on named member + category + time-window overlap. Same auth gate.
3. Escalation-export purge job (separate from report purge, per spec §10 v2) — purges files past `export_retention_until` from the stricter-access bucket.
4. Notification dispatch service: given a report event (new report, new message, escalation), determines which admins to notify based on subunit/category routing (spec §7) and their `notification_pref` (instant/hourly/daily). This is the shared function both the WebSocket layer (Phase 4/8) and the bot (Phase 6) will call — build it once, here.
5. Configure Render cron (or an internal scheduler) to hit `purge-cycle` daily and `duplicate-scan` on report creation or a short interval.

**Test:** Purge job run against seeded test data — confirm archived content matches original, confirm original is actually deleted, confirm escalation exports are *not* touched by the report purge. Auth-secret rejection test (missing/wrong header → 401/403, job does not run).

**Definition of Done:**
- [ ] Purge and duplicate-scan jobs are idempotent and safe to re-run
- [ ] Notification dispatch is a single reusable function, not duplicated between web and bot paths later

---

## Phase 6 — Telegram Bot (Full Implementation)

**Goal:** Bot replicates the full reporter and admin flows from spec §6, on top of the API built in Phases 3–5 — the bot should be a thin client, not a second implementation of business logic.

**Tasks:**
1. `/start` → access code prompt → calls `POST /api/access/verify` the same way the web frontend will (Phase 7) — no bot-specific auth shortcut.
2. Report flow (category → description → optional member → severity → photo → confirm) → calls `POST /api/reports` and the attachment endpoint. Show ticket code once, with the "🗑️ Delete this message" inline button (spec §3 v2 fix) wired to `deleteMessage`.
3. `/status <code>` → calls the ticket status/message endpoints. During an active session, hold `chat_id` in memory only for real-time relay — confirm nothing persists it in reversible form on the reporter side (this is the anonymity-critical boundary from spec §3, re-verify it explicitly in code review).
4. `/link <one-time-code>` (admin) → calls `POST /api/admin/telegram/link-code` flow, stores `telegram_chat_id_encrypted` via the Phase 1 encryption helper.
5. Admin inline commands (view/comment/reassign/status change) → thin wrappers around the Phase 4 admin API, with the admin's linked Telegram identity resolved to their `admin_id` server-side.
6. `/stats` → calls `GET /api/admin/dashboard/stats`, renders as an image (matplotlib or similar) rather than raw JSON.
7. Push notifications: bot subscribes to the Phase 5 notification dispatch service's output and calls `sendMessage` using the decrypted `chat_id`.
8. Run locally in **polling mode** against staging throughout this phase (spec §6 operational note) — do not deploy to any Render bot service yet.

**Test:** Full reporter flow via bot against staging API. Full admin flow via bot. Explicit test: send a report via bot, close the session, have an admin reply from the (not-yet-built, so simulate via API call) admin side — confirm the bot does *not* push a notification to that reporter, matching the documented limitation.

**Definition of Done:**
- [ ] Bot has zero duplicated business logic — every action is a call to an existing API endpoint
- [ ] Local polling works end-to-end against staging without ever conflicting with a production webhook (there shouldn't be one yet)

---

## Phase 7 — Frontend: Public Website

**Goal:** Reporter-facing web flows, mirroring the bot's capabilities, built on the same Phase 3 API.

**Tasks:**
1. Access-code entry screen → calls `/api/access/verify`, sets session cookie.
2. Public report form (category, description, optional member, severity, photo upload) → `POST /api/reports`. Confirmation screen shows ticket code once + the direct status link + the incognito-tab note (spec §3).
3. `/status/{ticket_code}` page — status + chat thread, polling or WebSocket for live updates while open.
4. Public suggestions list with upvote, public shoutouts list.
5. Privacy notice component (spec §9) — shown before submission, must actually contain the Telegram admin-vs-reporter distinction and the async-reply limitation, not generic boilerplate.

**Test:** Full submit → confirmation → status-check flow in the browser (Playwright/Cypress e2e). Confirm the ticket code never appears in a URL query string or gets logged by any analytics/error-tracking script that might be added in Phase 10.

**Definition of Done:**
- [ ] A non-technical reporter can complete a report and check on it without instructions
- [ ] No ticket code or session token appears in browser history in a way that contradicts the incognito-tab guidance already given to users

---

## Phase 8 — Frontend: Admin Dashboard

**Goal:** Full admin experience — the last major feature surface before the system is feature-complete.

**Tasks:**
1. Admin login + 2FA setup/enforcement flow.
2. Report inbox: list + filters (category, status, subunit, date, keyword) against `GET /api/admin/reports`.
3. Report detail view: status changes, assignment, notes, reporter chat, escalation trigger, member-linking (Phase 4's `link-member` endpoint) — including the recusal warn/block UI when it fires.
4. Dashboard charts (spec §8): pie, time-series, category breakdown, heatmap, resolution time, oldest-unresolved flag, per-subunit volume — via `GET /api/admin/dashboard/stats`.
5. Admin management (HOH only): admins CRUD, permissions, deactivation.
6. Escalation-contacts and categories management screens.
7. Audit log viewer (HOH/Asst Head only).
8. Real-time updates via `WS /api/admin/ws` — new report/message notifications without refresh.
9. Filtered export (PDF/DOCX) trigger UI.
10. Telegram link-code generation UI (feeds Phase 6's `/link` bot command).

**Test:** e2e test covering the full triage lifecycle of one report from an admin's perspective: view → assign → chat with reporter → escalate → close. Recusal block/warn scenario tested explicitly in the UI, not just the API.

**Definition of Done:**
- [ ] Every admin API endpoint from Phase 4 has a corresponding UI surface — no orphaned backend functionality
- [ ] Permission-gating is enforced in the UI (hidden/disabled) *and* still enforced server-side (never trust the UI alone)

---

## Phase 9 — Production Cutover for Bot + Scheduled Jobs

**Goal:** Move the bot from local-polling to production webhook, and turn on the real cron schedule — deliberately sequenced late so it happens once, correctly, against a feature-complete system.

**Tasks:**
1. Deploy bot to Render as a webhook receiver, pointed at production Supabase, using the single production token.
2. Confirm the webhook registration replaces any local polling — verify no 409 conflicts, and that local dev from here on uses a *second, disposable* local test flow only if truly needed (re-read spec §6 — this is intentionally awkward, don't try to "fix" it with a second bot).
3. Enable Render cron / external cron (cron-job.org / UptimeRobot) hitting `/internal/jobs/purge-cycle` and the keep-warm ping (spec §2 hosting split) on production.
4. Confirm `X-Internal-Job-Secret` is set correctly in production env and jobs actually run, not just return 200 on a misconfigured no-op.

**Test:** Send a real (test) report via the production bot, confirm it lands in the production admin dashboard. Manually trigger a purge-cycle dry run against a seeded old report, confirm archival + PDF delivery to HOH.

**Definition of Done:**
- [ ] Production bot is live and is the *only* thing holding the webhook
- [ ] Scheduled jobs run on their real cadence, not just callable on demand

---

## Phase 10 — Testing Hardening Pass

**Goal:** This isn't "write tests now" — tests should already exist from every phase above. This phase is specifically for the tests that only make sense once the whole system exists: cross-cutting and adversarial cases.

**Tasks:**
1. End-to-end anonymity audit: attempt to trace a specific submitted report back to a reporter using only what's in the database and logs. This should be impossible except via the documented Telegram rate-limiting hash, which itself should not be reversible.
2. Permission-boundary fuzzing: attempt every admin action as every role, confirm only intended roles succeed.
3. Recusal bypass attempts: try to close a self-named report via every available route (API, bot, dashboard).
4. Load/rate-limit test on public submission endpoints.
5. Confirm the purge cycle doesn't silently fail on edge cases: a report with no messages, a report with attachments, a report already escalated.
6. Security review of the attachment upload path specifically (the flagged issue from spec review) — confirm content-type validation can't be bypassed by a renamed file.

**Definition of Done:**
- [ ] No open finding from the spec review (§3/§9's flagged risks) is reproducible against the live staging system

---

## Phase 11 — Monitoring & Observability

**Goal:** Visibility from day one of real usage, not bolted on after an incident.

**Tasks:**
1. Error tracking (e.g. Sentry) on `apps/api`, `apps/web`, and `apps/bot` — confirm no PII (ticket codes, report content, reporter identifiers) ever lands in an error payload; scrub before it's wired up, not after.
2. Uptime checks on the public health endpoint and the bot webhook.
3. Basic APM/logging on the purge cycle and duplicate-scan jobs specifically — these run unattended and a silent failure is the worst-case outcome for a data-retention promise.
4. Alerting: purge-cycle failure, webhook downtime, Render service cold-start/spin-down (free tier) impacting response time.

**Definition of Done:**
- [ ] An on-call person (even if that's just you) would find out about a broken purge cycle within a day, not a month

---

## Phase 12 — Pre-Launch Checklist (spec §12, execute literally)

Work through spec §12 v2 item by item, in order, as actual tasks — not a soft checklist:
- [ ] Heads-up to teacher-in-charge/school contact
- [ ] Access-code distribution plan executed
- [ ] Full staging end-to-end test (this master plan's Phase 10, formally signed off)
- [ ] External cron confirmed live against production
- [ ] Admin 2FA enforced — attempt to create an admin without it and confirm it's rejected
- [ ] Supabase backup restore test-run, not just "enabled" — actually restore into a scratch project and verify
- [ ] Confirm no local bot polling session is running before flipping production webhook live (should already be true from Phase 9, re-verify)

**Only after every item above is checked does the access code go out to real users.**

---

## Phase 13 — Maintenance (Ongoing, Post-Launch)

Not a one-time phase — carries forward indefinitely:
- Dependency/security updates on a regular cadence (monthly minimum)
- Monitor Render free-tier limits as usage grows; budget for upgrade if the unit's report volume outgrows cold-start tolerance
- Revisit spec §11 deferred items (multi-language, CAPTCHA, formal accused-response field) only if real usage data justifies them — don't build ahead of need
- Periodic audit-log review by HOH/Assistant Heads (spec §9) as an actual recurring calendar task, not just a feature that exists

---

## Dependency Graph (quick reference)

```
Phase 0 (scaffold)
  └─> Phase 1 (database)
        └─> Phase 2 (auth/session)
              └─> Phase 3 (public API) ──┐
              └─> Phase 4 (admin API) ───┼─> Phase 5 (jobs/notifications)
                                          │         └─> Phase 6 (bot)
                                          │         └─> Phase 7 (public web)
                                          │         └─> Phase 8 (admin web)
                                          │               └─> Phase 9 (bot cutover)
                                          │                     └─> Phase 10 (hardening)
                                          │                           └─> Phase 11 (monitoring)
                                          │                                 └─> Phase 12 (launch checklist)
                                          └─────────────────────────────────────> Phase 13 (maintenance)
```

Phases 6, 7, and 8 can run in parallel once Phase 5 is done, since they're independent clients of the same API. Do not parallelize anything before Phase 3/4 are solid — every later phase is a client of that core.
