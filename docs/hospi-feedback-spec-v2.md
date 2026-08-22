# Hospi Anonymous Feedback & Reports System — Full Specification

## 1. Overview

An anonymous reporting and feedback platform for the Hospitality Unit, accessible via a **website** and a **Telegram bot**, both reading from and writing to the same backend so admins see a unified inbox regardless of which channel a report came in on.

Core principle: **reporters never have accounts**. Anonymity is preserved by design, not by policy — the system architecturally cannot trace a report back to a person (with the reporter-side Telegram caveat detailed in §3, and the operational bot-token note in §6).

---

## 2. Architecture

```
┌─────────────────┐        ┌──────────────────┐
│   Website        │        │   Telegram Bot    │
│  (Vercel)         │        │  (Render, Python) │
│  - Public report   │       │  - python-telegram │
│    form            │       │    -bot, webhook   │
│  - Ticket status    │       │  - Admin commands  │
│    lookup           │       │                    │
│  - Admin dashboard   │       │                    │
│    (React/Next)      │       │                    │
└─────────┬─────────┘        └─────────┬──────────┘
          │  REST + WebSocket           │  REST (internal)
          └───────────────┬─────────────┘
                           ▼
                 ┌──────────────────────┐
                 │   FastAPI Backend      │
                 │      (Render)           │
                 │  - Auth (admin only)      │
                 │  - Reports/Chat API         │
                 │  - Notification service       │
                 │  - Export/Archive jobs          │
                 │  - Rate limiting                  │
                 └──────────┬───────────────────────┘
                            ▼
                 ┌──────────────────────┐
                 │      Supabase           │
                 │  - Postgres DB            │
                 │  - Auth (admins only)       │
                 │  - Storage (attachments)      │
                 └──────────────────────┘
```

**Hosting split:**
- Frontend (public form + admin dashboard): **Vercel**
- FastAPI backend + Telegram bot (as a background worker/webhook receiver): **Render**, free tier, kept warm via external cron ping (cron-job.org / UptimeRobot every ~10–14 min)
- Database, Auth, File Storage: **Supabase**
- Environments: separate **staging** and **production** Supabase projects + Render services

---

## 3. Anonymity Model

- **Reporter identity**: never captured, never stored. No login, no email required.
- **Access gate**: a shared access code (e.g. `HOSPI2026`) required once per browser session / once per Telegram bot interaction. This filters out randoms who aren't in the unit — it is not identity verification and does not compromise anonymity.
  - **Mechanism**: `POST /api/access/verify` checks the submitted code and, on success, issues a short-lived signed session token (e.g. JWT, ~24h expiry, no PII in payload — just an issued-at timestamp and a random session id). Web stores this as an httpOnly, secure cookie; the Telegram bot holds it in memory for the duration of the conversation and re-verifies on `/start` if expired. **All public endpoints in §5 require a valid session token**, not just a UI-layer gate — the API itself rejects requests without one, so someone hitting the API directly (bypassing the frontend) still can't submit or read reports without the code.
- **Ticket code**: generated at submission (high-entropy random string, e.g. 12+ chars), shown once. This is the reporter's only way to access their report's chat thread later. No recovery if lost — this is a deliberate anonymity/security tradeoff.
- **Ticket status link**: alongside the raw code, the confirmation screen also shows a direct clickable link (`yoursite.com/status/{ticket_code}`) the reporter can bookmark, save, or open in a new tab, instead of retyping the code later. Confirmation screen includes a brief note recommending a private/incognito tab if they're on a shared device, since the code is embedded in the URL and could otherwise sit in browser history.
- **Reporter chat thread**: reporter and admin can exchange messages tied to the ticket code, with no PII logged. When admin marks the case **Closed**, the code stops working for the reporter (read access revoked), but admins retain the full thread as case record.
- **Telegram caveat — reporter side**: Telegram inherently ties messages to a `chat_id`. This is hashed immediately on receipt and used **only** for rate-limiting/abuse detection — never shown to admins, never linked to report content, purged on the same cycle as report data. This is disclosed transparently to users (see §9). During an *active* bot conversation (the guided report flow, or a live `/status` session), the bot uses the real chat_id **ephemerally, in memory only**, to route that session's messages — it is never written to the database in reversible form. Practical consequence: if an admin replies to a Telegram-sourced ticket **after** the reporter's session has ended (e.g. hours later from the web dashboard), the bot has no way to proactively notify that reporter — there is no reversible chat_id to message. The reporter must re-run `/status <code>` to see the reply. This is an intentional anonymity tradeoff and should be stated plainly in the bot's `/status` response and in the privacy notice (§9), not left implicit.
- **Telegram caveat — admin side**: this is a *different* case from the reporter caveat above and must **not** reuse a one-way hash. Admins are known, consenting unit members who need to actually *receive* push notifications, which requires the backend to call Telegram's `sendMessage` with their real `chat_id`. See §4 — `admins.telegram_chat_id` is stored **encrypted (reversible)**, not hashed, scoped to that single purpose.
- **Ticket-code exposure in Telegram history**: `/status <code>` puts the plaintext code into the reporter's Telegram chat history, the same risk the web incognito-tab note addresses for browser history. Mitigation: immediately after the bot sends the code (at submission, and on each `/status` lookup), it also sends an inline "🗑️ Delete this message" button that calls Telegram's `deleteMessage` API on tap (bots can delete their own messages up to 48h after sending).
- **Rate limiting**: per browser fingerprint (web) and per hashed Telegram ID (bot) to prevent spam, without blocking legitimate use.

---

## 4. Database Schema (Postgres / Supabase)

```sql
-- Reports
reports (
  id UUID PRIMARY KEY,
  ticket_code_hash TEXT UNIQUE NOT NULL,   -- hashed, never store plaintext
  source TEXT CHECK (source IN ('web','telegram')),
  report_type TEXT CHECK (report_type IN ('complaint','suggestion','recognition')),
  reported_member_name TEXT,               -- free text, optional
  reported_member_admin_id UUID REFERENCES admins(id) NULL,  -- optional link, confirmed manually at triage; recusal check (§9) runs against this
  description TEXT NOT NULL,
  incident_date DATE,
  incident_location TEXT,
  severity TEXT CHECK (severity IN ('low','medium','high')) NULL, -- reporter-set, optional
  status TEXT CHECK (status IN (
    'new','under_review','assigned','in_progress',
    'resolved','escalated','closed','marked_false'
  )) DEFAULT 'new',
  assigned_admin_id UUID REFERENCES admins(id),
  publish_shoutout BOOLEAN DEFAULT FALSE,  -- only relevant if report_type = recognition
  is_public BOOLEAN DEFAULT FALSE,          -- admin-toggled per shoutout
  possible_duplicate_of UUID REFERENCES reports(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
)

-- Categories (admin-managed, multi-select via join table)
categories (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  active BOOLEAN DEFAULT TRUE     -- soft delete
)
report_categories (
  report_id UUID REFERENCES reports(id),
  category_id UUID REFERENCES categories(id),
  PRIMARY KEY (report_id, category_id)
)

-- Attachments
attachments (
  id UUID PRIMARY KEY,
  report_id UUID REFERENCES reports(id),
  storage_path TEXT NOT NULL,     -- Supabase Storage, EXIF stripped before save
  file_type TEXT,                 -- restricted to image types
  uploaded_at TIMESTAMPTZ DEFAULT now()
)

-- Reporter <-> Admin chat thread (per ticket)
messages (
  id UUID PRIMARY KEY,
  report_id UUID REFERENCES reports(id),
  sender_type TEXT CHECK (sender_type IN ('reporter','admin')),
  sender_admin_id UUID REFERENCES admins(id) NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Internal admin-only notes (never visible to reporter)
internal_notes (
  id UUID PRIMARY KEY,
  report_id UUID REFERENCES reports(id),
  admin_id UUID REFERENCES admins(id),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Admins & roles
admins (
  id UUID PRIMARY KEY,               -- linked to Supabase Auth user
  full_name TEXT NOT NULL,
  role TEXT CHECK (role IN (
    'hoh','asst_head','gen_sec','fin_sec',
    'subunit_head','subunit_asst','custom'
  )),                                 -- sets sensible default permissions at creation time; admin_permissions below is what's actually enforced at request time (source of truth)
  subunit TEXT NULL,                 -- protocol / welfare / creative_writers / follow_up / pr
  aliases TEXT[] DEFAULT '{}',        -- known nicknames/short forms, used for soft fuzzy-match warnings on recusal (see §9)
  telegram_chat_id_encrypted TEXT NULL,  -- set via one-time linking flow; symmetrically encrypted at rest (app-level key, NOT the reporter-side hash model), decrypted server-side only when calling Telegram sendMessage
  notification_pref TEXT CHECK (notification_pref IN ('instant','hourly','daily')) DEFAULT 'instant',
  active BOOLEAN DEFAULT TRUE,        -- for offboarding
  created_at TIMESTAMPTZ DEFAULT now()
)
admin_permissions (
  admin_id UUID REFERENCES admins(id),
  permission TEXT CHECK (permission IN (
    'view','respond','assign','close','export',
    'manage_categories','manage_admins','manage_escalation_contacts'
  )),
  PRIMARY KEY (admin_id, permission)
)

-- External escalation contacts (configurable, not hardcoded)
escalation_contacts (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  role_label TEXT NOT NULL,    -- e.g. "Chaplain (Female)"
  contact_email TEXT,
  contact_phone TEXT,
  active BOOLEAN DEFAULT TRUE
)
escalations (
  id UUID PRIMARY KEY,
  report_id UUID REFERENCES reports(id),
  escalation_contact_id UUID REFERENCES escalation_contacts(id),
  escalated_by_admin_id UUID REFERENCES admins(id),
  exported_file_path TEXT,     -- redacted PDF/DOCX generated at escalation time, stored in a separate, stricter-access Supabase Storage bucket than attachments
  export_retention_until TIMESTAMPTZ,  -- exempt from the 30-day report purge cycle (§10) since it's already been shared externally; independently purged on its own retention window (default 1 year, configurable)
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Audit log (anti-admin-abuse mechanism)
audit_log (
  id UUID PRIMARY KEY,
  admin_id UUID REFERENCES admins(id),
  report_id UUID REFERENCES reports(id),
  action TEXT CHECK (action IN (
    'viewed','status_changed','assigned','message_sent','note_added',
    'exported','escalated','closed','marked_false','deleted','other'
  )) NOT NULL,                 -- constrained for consistency with rest of schema; 'other' + detail JSONB as escape hatch for anything unforeseen
  detail JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Suggestion upvotes (one vote per device, tracked by hashed fingerprint)
suggestion_votes (
  report_id UUID REFERENCES reports(id),
  voter_fingerprint_hash TEXT NOT NULL,
  PRIMARY KEY (report_id, voter_fingerprint_hash)
)

-- Archive (post-purge metadata retention)
-- Single archive path for BOTH the scheduled 30-day purge job AND admin-initiated delete (§5 DELETE /api/admin/reports/{id}).
-- Admin delete is simply an early, manual trigger into this same archive-then-remove routine, not a separate mechanism —
-- distinguished only by archive_reason below, so there is exactly one code path to maintain and audit.
archived_reports (
  id UUID PRIMARY KEY,
  original_report_id UUID,
  ticket_code_hash TEXT,
  categories TEXT[],
  status_history JSONB,
  resolution_summary TEXT,
  handled_by_admin_id UUID,
  archive_reason TEXT CHECK (archive_reason IN ('scheduled_purge','admin_deleted')) NOT NULL,
  deleted_by_admin_id UUID NULL REFERENCES admins(id),  -- set only when archive_reason = 'admin_deleted'; HOH only per §5
  delete_reason TEXT NULL,                              -- short required justification, shown in audit_log detail too
  created_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ DEFAULT now()
)
```

---

## 5. API Endpoints (FastAPI)

### Public (access-code session required — see §3)
```
POST   /api/access/verify                        Exchange access code for short-lived session token
POST   /api/reports                               Submit a new report -> returns ticket_code (once)
GET    /api/reports/ticket/{code}                 Fetch report status + chat thread
POST   /api/reports/ticket/{code}/message         Reporter sends chat message
POST   /api/reports/ticket/{code}/attachments     Upload image attachment (moved under ticket_code, not raw report id —
                                                    a leaked internal UUID must not be enough to attach files to someone
                                                    else's report; ticket code is the only credential that should matter)
GET    /api/suggestions/public                    List public suggestions for upvoting
POST   /api/suggestions/{id}/upvote               Upvote (device-fingerprint limited)
GET    /api/shoutouts/public                      List published shoutouts
```
All of the above additionally require the session token issued by `/api/access/verify` (cookie for web, in-memory for bot) — the access code gate is enforced at the API layer, not just the UI.

### Admin (Supabase Auth + 2FA required)
```
POST   /api/admin/login
GET    /api/admin/reports              List + filter (category, status, subunit, date, keyword)
GET    /api/admin/reports/{id}
PATCH  /api/admin/reports/{id}/status
PATCH  /api/admin/reports/{id}/assign
PATCH  /api/admin/reports/{id}/link-member    Confirm reported_member_name -> reported_member_admin_id (triage step, §9 recusal)
POST   /api/admin/reports/{id}/notes
POST   /api/admin/reports/{id}/message
POST   /api/admin/reports/{id}/escalate
POST   /api/admin/reports/{id}/mark-false
DELETE /api/admin/reports/{id}          (HOH only — soft delete + archive)

GET    /api/admin/categories
POST   /api/admin/categories
PATCH  /api/admin/categories/{id}       (soft delete via active=false)

GET    /api/admin/escalation-contacts
POST   /api/admin/escalation-contacts
PATCH  /api/admin/escalation-contacts/{id}

GET    /api/admin/admins                (HOH only)
POST   /api/admin/admins
PATCH  /api/admin/admins/{id}/permissions
PATCH  /api/admin/admins/{id}/deactivate

GET    /api/admin/dashboard/stats       Pie/time-series/category/heatmap data
GET    /api/admin/export                Filtered on-demand PDF/DOCX export
GET    /api/admin/audit-log             (HOH/Asst Head only)

POST   /api/admin/telegram/link-code    Generate one-time code to link Telegram account
WS     /api/admin/ws                    Real-time report/notification updates
```

### Internal (system jobs)
```
POST   /internal/jobs/purge-cycle       Scheduled 30-day archive + batch PDF to HOH
POST   /internal/jobs/duplicate-scan    Flags possible-duplicate reports
```
**Auth**: not public-facing by intent, but must be enforced, not assumed. Both endpoints require a static shared-secret header (`X-Internal-Job-Secret`, stored in Render env vars, rotated periodically) checked before any work runs. Where Render's networking allows it, additionally restrict these routes to internal/private networking or an IP allowlist as defense-in-depth — the shared secret alone is the load-bearing control, the network restriction is a backstop.

---

## 6. Telegram Bot Flow

**Reporter side:**
- `/start` → access code prompt (once) → main menu: Report Concern / Suggest Something / Shoutout / Check Ticket Status / Help
- Report flow: guided multi-step conversation (category → description → optional named member → optional severity → optional photo → confirm) → returns ticket code
- `/status <code>` → shows current status + lets them send/receive chat messages

**Admin side:**
- Admin links account once via `/link <one-time-code>` (code generated from dashboard); on success the bot resolves and stores the admin's real `chat_id`, **encrypted** (see §4 — not the reporter's one-way hash), so pushes can actually be sent later
- Receives push notifications per their configured frequency (instant/hourly/daily digest)
- Can view, comment, reassign, and change status directly from bot commands/inline buttons
- `/stats` → condensed dashboard (image-rendered charts)
- Being `@mentioned` on a report triggers an instant push regardless of digest setting

**Operational note — single bot token:** Telegram allows only one active webhook per bot token at a time, so there is a single bot (one token) rather than separate staging/production bots. Production runs as a webhook on Render, pointed at the production Supabase project. Staging/testing runs the **same** bot code **locally in polling mode** (not webhook), pointed at the staging Supabase project — polling and an active webhook cannot run concurrently on the same token (Telegram returns a 409 conflict), so a local test session must be stopped before it, and the deployed production webhook, would both try to receive updates at once. Consequently the CI/CD pipeline does not auto-deploy the bot to any staging Render service; bot changes are exercised locally before merging to `main`.

---

## 7. Admin Roles & Permissions

| Role | Scope |
|---|---|
| Head of Hospi (HOH) | Full access, manages admins, escalation contacts, permanent delete |
| Assistant Heads / Gen Sec / Fin Sec | Full visibility, scoped auto-tagging (e.g. Fin Sec on financial category) |
| Sub-unit Heads/Assistants (Protocol, Welfare, Creative Writers, Follow-up, PR) | Reports tagged to their subunit; can escalate upward |
| Custom roles | Granular permission flags per admin |

Auto-suggested routing based on category, confirmed manually during triage (not fully automatic) to avoid mis-tag errors.

---

## 8. Notifications & Dashboard

- Real-time in-app via WebSocket; Telegram push for away-from-desk; configurable digest frequency per admin
- Dashboard charts: resolved/unresolved/escalated pie, submissions over time (day/month/year), category breakdown, average resolution time, oldest unresolved flag, per-subunit volume, day/hour heatmap
- Same condensed stats available via bot `/stats`
- Filtered on-demand export (PDF/DOCX) — independent of the purge cycle, usable any time for unit meetings/reviews

---

## 9. Abuse Prevention & Trust

- Rate limiting (device fingerprint / hashed Telegram ID), no CAPTCHA in v1
- Flag-not-block on sensitive language — never auto-suppress a real complaint
- `marked_false` status distinct from `closed`, for tracking bad-faith patterns
- **Recusal rule**: an admin cannot close/dismiss/mark-false a report naming themselves. Enforcement is two-tiered since `reported_member_name` is free text (§4):
  - **Hard block**: if `reported_member_admin_id` is set (linked during triage — see below), the backend rejects any status-change or mark-false action from that admin outright, no override.
  - **Soft warning**: if unlinked, the backend runs a case-insensitive substring match of the current admin's `full_name` and `aliases` (§4) against `reported_member_name`. A match doesn't block the action but surfaces a confirmation prompt ("this report may name you — proceed anyway?") and logs the override attempt to `audit_log` regardless of the admin's answer, so HOH/Assistant Heads can review it.
  - Linking `reported_member_admin_id` itself is a manual triage step (any admin with `assign` permission can confirm the match) — deliberately not automatic, to avoid mis-tagging someone who shares a name with an admin.
- Full **audit log** of all admin actions, visible only to HOH/Assistant Heads
- A clear, honest **privacy notice** shown before submission, explaining exactly what is and isn't tracked (builds trust in the anonymity claim), including the Telegram admin-vs-reporter chat_id distinction from §3 and the async-reply limitation for Telegram-sourced reports
- Duplicate/pattern flagging: reports sharing named member + overlapping category + close time window are soft-flagged as "possibly related," without unmasking anyone

---

## 10. Data Retention

- 30-day configurable auto-purge: report content + chat archived to `archived_reports` (metadata only), batch PDF sent to HOH, then original content deleted
- **Admin-initiated delete** (`DELETE /api/admin/reports/{id}`, HOH only) calls the **same** archive-then-remove routine as the scheduled purge, just triggered early — see `archived_reports.archive_reason` in §4. There is one archive mechanism, not two; admin delete is distinguished only by `deleted_by_admin_id` and a required `delete_reason`, both logged to `audit_log`.
- **Escalation exports** (`escalations.exported_file_path`) are explicitly **exempt** from the 30-day report purge, since by the time an escalation happens the file has already been shared with an external contact (e.g. chaplain) and deleting it from the system wouldn't un-share it. Instead they're retained in a separate, stricter-access storage bucket under their own independent retention window (`export_retention_until`, default 1 year, configurable by HOH), then purged on that schedule.
- Separate **on-demand filtered export** tool, independent of purge cycle — for reporting/meeting purposes
- File uploads: image-only, size-capped, validated (not just by extension)

---

## 11. Explicitly Deferred to Later Versions

- Formal in-system field for a named member's response to an accusation (v1: handled informally via internal notes)
- Multi-language support
- CAPTCHA / stronger anti-spam (add only if spam becomes a real problem)
- Optional Telegram-linked push notifications for web reporters (nice-to-have, not core — the direct status link partially covers this need already)

---

## 12. Pre-Launch Checklist

- [ ] Informal heads-up to a teacher-in-charge/school contact that the system exists, given its potential to surface serious safety issues
- [ ] Distribution plan for the access code (unit group chat, onboarding sheet, etc.)
- [ ] Staging environment tested end-to-end before going live on production Supabase/Render
- [ ] External cron configured to keep Render bot service warm
- [ ] Admin 2FA enforced before first real report is accepted
- [ ] Supabase automated backups confirmed enabled on production project, and a restore has been test-run at least once before go-live (given the sensitivity of report data, "backups exist but were never tested" is not an acceptable state)
- [ ] Confirm production and local-polling staging bot sessions are never run simultaneously against the same Telegram token (see §6 operational note)
