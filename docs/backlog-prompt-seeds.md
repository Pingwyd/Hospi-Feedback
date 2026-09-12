# Backlog: Prompt Seeds

Structured work items for generating one-at-a-time agent prompts. Each item is scoped to a single PR-sized task. Do not combine items unless explicitly requested.

**How to use:** Copy one item block into Claude (or another planner) and ask it to produce a full implementation prompt for Cursor Agent, including acceptance criteria, file hints, and test plan.

**Branch baseline:** `dev` (or latest merged feature branch at time of work).

**Design tokens (web):** ink `#16241F`, paper `#F3EFE6`, brass `#A6803C`, sage `#6B8F71`. Icons: `lucide-react` only. No emojis in UI.

---



## BL-001: Photo preview in follow-up messages (web + Telegram)

**Problem:** When a reporter sends a photo as a follow-up message (after initial report), the image does not display on the user side in the web app or in Telegram. Users cannot see what they sent.

**Scope:** Web reporter status/chat UI, Telegram bot reporter status flow, API if attachment URLs are not returned in message/thread payloads.

**Likely files:**

- `apps/web/src/components/status/StatusPanel.tsx`
- `apps/web/src/lib/api/reports.ts`
- `apps/api/app/services/reporter_reports.py`
- `apps/api/app/integrations/reports_store.py`
- `apps/bot/bot/handlers/status.py`

**Acceptance criteria:**

- After uploading a follow-up photo on web, the conversation thread shows an inline preview (thumbnail or full image) for that message.
- Existing messages with attachments render previews on page load, not only immediately after upload.
- Telegram `/status` flow and chat replies show sent photos to the reporter (inline photo or link, per Telegram API constraints).
- Attachments remain access-controlled (session/ticket code for reporters; no leaked internal UUIDs).
- Empty/error states if an attachment fails to load (broken image fallback, not a silent gap).

**Notes:** Initial report photo on submit may work differently from follow-up attachments; verify both paths. Check whether messages API returns attachment metadata and signed URLs.

---



## BL-002: App-wide URL-based live search with debounce and caching

**Problem:** Search/filter behavior should be consistent across the app: driven by URL query params, update live as the user types (debounced), and use sensible client-side caching to avoid redundant API calls.

**Scope:** Web admin (inbox at minimum; extend to audit log and settings lists if applicable).

**Likely files:**

- `apps/web/src/components/admin/ReportInbox.tsx`
- `apps/web/src/lib/api/admin-reports.ts`
- `apps/web/src/app/admin/reports/page.tsx`
- Consider `nuqs` or Next.js `useSearchParams` pattern project-wide
- TanStack Query if already in stack; otherwise document chosen approach

**Acceptance criteria:**

- Inbox filters (status, keyword, date range when added) sync to URL (`?status=...&q=...`).
- Changing filters updates the URL without full page reload; back/forward restores filter state.
- Keyword search debounces (suggest 300-400ms; justify in code comment).
- Repeated identical searches within a session hit cache (TanStack Query or equivalent), not duplicate network calls.
- Shareable/bookmarkable filtered inbox URLs work after paste in new tab.
- No submit button required for keyword search (live), unless user explicitly wants retain submit for accessibility (document choice).

**Notes:** Spec §5 lists category/subunit/date filters on admin reports; API supports `created_from`/`created_to` but UI may not. This task focuses on search UX pattern; category/subunit filters can be a follow-up or included if small.

---



## BL-003: Wire Telegram `/stats` to admin dashboard API

**Problem:** Bot `/stats` returns a TODO stub. Spec §6 and §8 require condensed dashboard stats via bot, ideally image-rendered charts.

**Scope:** Bot only initially; uses existing `GET /api/admin/dashboard/stats`.

**Likely files:**

- `apps/bot/bot/handlers/admin.py`
- `apps/bot/bot/api_client.py`
- `apps/api/app/services/admin_dashboard.py` (read-only; extend response if bot needs fields)

**Acceptance criteria:**

- Linked admin running `/stats` receives a useful summary (status counts, oldest unresolved, submission trend summary at minimum).
- Unlinked or non-admin users get a clear error, not a TODO message.
- Prefer image-rendered chart(s) if feasible without heavy new dependencies; otherwise structured text summary is acceptable for v1 with a note for chart follow-up.
- Uses admin auth path appropriate for bot (service secret + linked chat id, matching existing bot admin patterns).

**Notes:** `STATS_UNAVAILABLE` string in `admin.py` is the current stub.

---



## BL-004: Telegram inline keyboard / main menu

**Problem:** Telegram bot needs inline keyboard and main menu UX per spec §6 (`/start` menu: Report Concern / Suggest Something / Shoutout / Check Ticket Status / Help).

**Scope:** Bot handlers, keyboards, callbacks.

**Likely files:**

- `apps/bot/bot/handlers/menu.py`
- `apps/bot/bot/handlers/start.py`
- `apps/bot/bot/keyboards.py`
- `apps/bot/bot/handlers/callbacks.py`
- `apps/bot/bot/main.py`

**Acceptance criteria:**

- `/start` after access verification shows persistent or re-callable main menu with inline buttons.
- Each menu action routes to the correct flow (complaint/suggestion/recognition report, status check, help text).
- Callback handlers answer queries and edit/update messages appropriately (no orphaned loading states).
- Menu remains usable mid-conversation where spec allows (e.g. cancel/back).
- Matches existing bot auth gate (`ensure_session_or_prompt`).

**Notes:** Partial menu exists in `keyboards.py`; audit gaps vs spec labels (Shoutout vs Recognition).

---



## BL-005: Admin report detail status picker shows current status

**Problem:** In admin report detail, the status control does not clearly show which status is currently selected/active. Admins cannot see at a glance what state the ticket is in from the picker itself.

**Scope:** Web admin UI only.

**Likely files:**

- `apps/web/src/components/admin/ReportDetailPanel.tsx`

**Acceptance criteria:**

- Current report status is visually distinct in the status control (selected state, badge, or controlled select showing current value).
- Status is readable without scanning separate summary text only.
- Permission-gated actions unchanged (only admins with correct permissions see actionable statuses).
- Accessible: current status announced to screen readers (`aria-current` or label association).

**Notes:** Today status appears in summary text and as a row of equal-weight buttons with no selected styling.

---



## BL-006: Delete report validation error when reason is empty

**Problem:** When an admin tries to delete a ticket without entering a delete reason, there is no visible error message (or it is easy to miss).

**Scope:** Web admin UI.

**Likely files:**

- `apps/web/src/components/admin/ReportDetailPanel.tsx`

**Acceptance criteria:**

- Submitting delete with empty/whitespace reason shows an inline field-level error and/or modal alert (not only a generic banner far from the input).
- Error uses `role="alert"` or `aria-describedby` on the reason field.
- Focus moves to the reason field on validation failure.
- Successful delete still requires non-empty reason and HOH permission.

**Notes:** `handleDelete` already sets `setActionError("Delete reason is required.")` but UX may hide it inside a modal or below the fold; fix visibility and field association.

---



## BL-007: Fix full-page reload when tabbing back into the site

**Problem:** Every time the user tabs back into the website, the entire page reloads (admin shell shows skeleton again). Bad UX and loses scroll/state.

**Scope:** Web admin session handling.

**Likely files:**

- `apps/web/src/components/admin/AdminSessionProvider.tsx`
- `apps/web/src/components/admin/AdminLayoutClient.tsx`

**Acceptance criteria:**

- Tab focus / visibility change does not set global `loading=true` and unmount the admin shell if a valid session already exists.
- Background token/profile refresh is silent (stale-while-revalidate) unless auth actually failed (401), then redirect to login.
- No full-page skeleton flash on ordinary tab switch.
- Session invalidation still works (logout in another tab, expired token).

**Notes:** Root cause is likely `refreshProfile()` on `window.focus` always calling `setLoading(true)`, and `AdminLayoutClient` rendering `SkeletonCard` whenever `loading` is true.

---



## BL-008: Page-specific skeleton loading layouts

**Problem:** Loading states use a generic skeleton card everywhere instead of layouts that mirror each page's actual structure.

**Scope:** Web (public + admin pages).

**Likely files:**

- `apps/web/src/components/admin/SkeletonBlock.tsx`
- `apps/web/src/components/admin/DashboardOverview.tsx`
- `apps/web/src/components/admin/ReportInbox.tsx`
- `apps/web/src/components/admin/ReportDetailPanel.tsx`
- `apps/web/src/app/admin/settings/_components/*Panel.tsx`
- `apps/web/src/components/status/StatusPanel.tsx`
- `apps/web/src/app/admin/audit/page.tsx`

**Acceptance criteria:**

- Dashboard skeleton mimics chart cards + alert banner placeholders.
- Inbox skeleton mimics filter bar + table rows.
- Report detail skeleton mimics summary + action panels + thread.
- Settings panels skeleton mimics table/form layout per tab.
- Audit log skeleton mimics log table.
- Status/ticket public page skeleton mimics ticket header + conversation.
- Shimmer animation retained per project design rules.

---



## BL-009: Auto status transitions + closed confirmation modal

**Problem:** Status should update automatically when triage actions occur (assign → assigned, escalate → escalated, etc.). Closing a report should require a confirmation modal.

**Scope:** Web admin UI; optionally align API if status is not already set on assign/escalate (check backend first).

**Likely files:**

- `apps/web/src/components/admin/ReportDetailPanel.tsx`
- `apps/api/app/services/admin_reports.py` (verify assign/escalate already patch status)
- New confirm modal component (reuse `SettingsConfirmModal` / `RecusalConfirmModal` patterns)

**Acceptance criteria:**

- Assign action results in status `assigned` without a separate manual status click (if API already does this, UI reflects it immediately).
- Escalate → `escalated`, mark-false → `marked_false`, etc., consistent with backend.
- UI refreshes to show new status after each action without stale state.
- Transition to `closed` (and optionally `resolved` if product decision) opens a themed confirmation modal before API call.
- Modal follows app theme, keyboard trap, focus return on cancel.

**Notes:** Backend `assign_report` already sets `status: assigned` and escalate sets `escalated`; this may be primarily UI sync + closed modal + removing redundant manual status steps.

---



## BL-010: On-demand filtered export (API + admin UI)

**Problem:** Spec §5/§8/§10 requires `GET /api/admin/export` for filtered PDF/DOCX export for meetings/reviews. Not implemented (only phase-2 ping route and escalation PDF on escalate exist). No admin UI trigger.

**Scope:** API + web admin UI.

**Likely files:**

- New route e.g. `apps/api/app/api/routes/admin_export.py`
- `apps/api/app/core/pdf_builder.py` (extend or sibling DOCX builder)
- `apps/web/src/lib/api/admin-export.ts` (new)
- Admin dashboard or inbox export panel/button
- `apps/api/app/api/routes/phase2.py` (reference only; replace with real route)

**Acceptance criteria:**

- `GET /api/admin/export` accepts same filters as report list (status, keyword, date range; category when available).
- Requires `export` permission.
- Returns PDF or DOCX (query param or Accept header); document choice in prompt spec.
- Admin UI: export button with filter awareness ("Export current view" or explicit filter form).
- Download filename includes date range or "all" indicator.
- Tests: permission denied, empty result set, happy path generation.
- Audit log entry on export (`exported` action exists in audit types).

**Notes:** Escalation export is PDF-only today; spec mentions DOCX for on-demand export explicitly.

---



## BL-011: Light / dark mode toggle

**Problem:** App needs a user-toggleable light/dark mode following the existing colour theme (ink, paper, brass, sage).

**Scope:** Web app (public + admin).

**Likely files:**

- `apps/web/src/app/layout.tsx`
- `apps/web/src/lib/design-tokens.ts`
- Tailwind config / CSS variables
- `apps/web/src/components/admin/AdminShell.tsx` (toggle placement)
- New theme provider (Context or `next-themes` if approved dependency)

**Acceptance criteria:**

- Toggle control accessible from main layout (admin shell + public header or settings area).
- Colours derive from design tokens; dark mode is not generic gray but themed (ink/paper/brass/sage inverted thoughtfully).
- Preference persists across sessions (`localStorage` or cookie; document choice).
- Respects `prefers-color-scheme` on first visit before explicit choice.
- No flash of wrong theme on load (FOUC mitigation).
- All major pages readable (contrast WCAG AA).

**Notes:** Ask user to confirm dark palette mapping before implementation if not specified in prompt. Do not assume generic Tailwind `dark:` grays alone.

---



## BL-012: Light-mode status badge contrast (WCAG AA)

**Problem:** Several light-mode status badge combinations fail WCAG AA normal-text contrast (4.5:1 minimum). Discovered during BL-011 dark-palette audit with measured ratios, not visual guesswork.

**Measured failures (light mode, current tokens):**

- Brass text on `bg-brass/15`: **2.72:1** (`#A6803C` on blended `#e7decc`)
- Sage text on `bg-sage/15`: **2.71:1** (`#6B8F71` on blended `#dee0d4`)

Both fail the 4.5:1 threshold for normal text at badge sizes (`text-xs` in inbox and settings lists).

**Scope:** Web admin badge styling only (do not change dark-mode values; dark mode already passes at 6.16:1 and 6.56:1 respectively with BL-011 palette).

**Likely files:**

- `apps/web/src/components/admin/ReportInbox.tsx` (`statusBadgeClass`)
- `apps/web/src/app/admin/settings/_components/EscalationContactsPanel.tsx` (`statusBadgeClass`)
- Any shared badge utility if extracted during fix

**Acceptance criteria:**

- Brass and sage badge text/background pairs in **light mode** meet WCAG AA 4.5:1 for normal text, verified with measured contrast ratios reported in PR.
- Semantic meaning preserved: brass still reads as warning/escalated, sage still reads as new/positive/active.
- Dark-mode badge appearance unchanged from BL-011 implementation.
- No regression to BL-005 status-picker highlight or BL-009 confirm modals.

**Notes:** Separate from BL-011 because fixing light-mode badge colors changes appearance for all existing light-mode users; BL-011 only adds dark mode. Do not bundle into theme-toggle PR.

---



## Index


| ID     | Title                                    | Area            |
| ------ | ---------------------------------------- | --------------- |
| BL-001 | Photo preview in follow-up messages      | Web + Bot + API |
| BL-002 | URL-based live search + debounce + cache | Web             |
| BL-003 | Telegram `/stats` command                | Bot             |
| BL-004 | Telegram inline keyboard / menu          | Bot             |
| BL-005 | Status picker shows current status       | Web admin       |
| BL-006 | Delete reason validation error UX        | Web admin       |
| BL-007 | Tab focus full-page reload fix           | Web admin       |
| BL-008 | Page-specific skeleton loaders           | Web             |
| BL-009 | Auto status transitions + closed modal   | Web admin       |
| BL-010 | On-demand filtered export                | API + Web       |
| BL-011 | Light / dark mode toggle                 | Web             |
| BL-012 | Light-mode status badge contrast (AA)    | Web admin       |


