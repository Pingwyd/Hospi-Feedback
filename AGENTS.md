# Project Rules

## Emoji Policy

**NEVER use emojis in code unless they are part of a UI/UX design (e.g., mood scale indicators like 😢😟😐🙂😄 that represent user-selectable emotional states).**

### Rules:
- All UI icons must use `lucide-react` components
- Never use emoji characters for: navigation, buttons, badges, labels, empty states, search icons, close buttons, status indicators, or any other UI element
- The only exception is semantic content where emojis are meaningful data (e.g., fruit size comparisons for pregnancy weeks, mood scale selections)
- Always import icons from `lucide-react` and render them as JSX components with appropriate `size` props

### Common Lucide Icon Mappings:
| Use Case | Lucide Icon |
|----------|-------------|
| Home | `Home` |
| Notifications | `Bell` |
| Search | `Search` |
| Close/Cancel | `X` |
| Check/Complete | `Check` |
| Share | `Share2` |
| Edit | `Pencil` |
| Delete/Remove | `Trash2` |
| Warning | `AlertTriangle` |
| Emergency | `AlertOctagon` |
| Phone | `Phone` |
| Email | `Mail` |
| Calendar | `Calendar` |
| Clock/Time | `Clock` |
| Fire/Streak | `Flame` |
| Hospital | `Building2` |
| Medication | `Pill` |
| Lab/Test | `TestTube` |
| Vaccination | `Syringe` |
| Export/Download | `FileDown` |
| Document/Log | `FileText` |
| Clipboard | `ClipboardList` |
| Chat/Message | `MessageCircle` |
| User/Profile | `User` |
| Settings | `Settings` |
| Filter | `Filter` |
| Arrow/Navigation | `ArrowRight`, `ArrowLeft` |
| Check Circle | `CheckCircle2` |
| Info | `Info` |
| Alert | `AlertCircle` |
| Heart | `Heart` |

## Communication Rules

**NEVER make assumptions about user intent, requirements, or preferences.**

### Rules:
- Always ask clarifying questions when requirements are ambiguous or incomplete
- Do not assume implementation details, design choices, or technical approaches without confirmation
- When in doubt, ask for clarification rather than making educated guesses
- Seek explicit confirmation before making significant changes or decisions
- Clearly state what information is missing and what assumptions would need to be made

## Em-Dash Policy

**NEVER use em-dashes (—) in code, UI text, or comments.**

### Rules:
- Do not use em-dashes for: punctuation, separators, placeholders, or any other purpose
- Replace em-dashes with: commas, colons, hyphens, or restructure the sentence
- For "no data" fallback values, use "N/A" instead of "—"
- For code comments, use hyphens or commas instead of em-dashes
- For title/heading separators, use colons (:) or hyphens (-)

## Task Management

**Break down large tasks into smaller, manageable steps and wait for confirmation before proceeding.**

### Rules:
- When given a large list of tasks, break them into smaller, discrete steps
- Complete one step at a time before moving to the next
- Wait for explicit user confirmation (e.g., "next step", "continue", "proceed") before moving to the next task
- Provide a clear summary of what was completed and what will be done next
- If a step fails or encounters issues, stop and report the problem before continuing

## Design Principles

**Build responsive, well-designed websites that follow professional design standards.**

### Rules:
- Always follow a responsive-first approach - websites must work on all devices and viewports
- Apply proper design principles: visual hierarchy, consistency, alignment, contrast, whitespace, and typography
- Avoid the typical generic AI-generated styling (e.g., centered everything, oversized padding, rounded everything, generic gradients, default card layouts)
- Study real-world professional websites for inspiration rather than defaulting to common AI patterns
- Ensure proper spacing, grid systems, and layout structure
- Use intentional color schemes and typography that match the app's purpose
- Use Sans Serif font types (e.g., Inter, Roboto, Open Sans, Lato) for formal web application design settings
- Keep text uniform for label types and header types across the application
- Every modal creation should follow the app theme with proper UI/UX design principles related to the app
- Every dropdown should follow the app theme and not use the default look (regular dropdowns, calendar, time, etc.)
- Always use skeleton loading cards with shimmer animation for loading page content or modal content when retrieval time is not instant
- Ensure uniform and good spacing between objects and elements throughout the entire application, especially for elements enclosed in a div, nav, main, section, header, aside, footer, aside classes/elements, following good and industry standard design principles
- Always follow the design theme specified by the user; if not specified, ask for it without making assumptions or leaving ambiguity
- Always ask for color palette with complementing colours if not specified by the user; do not assume or make decisions without explicit confirmation

## Development Standards

**Follow industry best practices for quality, efficiency, and maintainability.**

### Rules:
- Build using industry standards and established patterns for the technology stack
- Find the most efficient and effective solution for each problem
- Plan and architect solutions in the most efficient way possible
- Ensure modular code design with clear separation of concerns
- Write proper documentation for complex logic, APIs, and architectural decisions
- Always write tests to ensure code reliability and prevent regressions
- Follow DRY (Don't Repeat Yourself), SOLID, and KISS principles
- Use meaningful naming conventions for variables, functions, and components

## Performance-Conscious Implementation

**For operations that run frequently or scale with collection size, choose data structures and algorithms that match the access pattern.**

### Rules:
- State the access pattern (e.g. "lookup by id", "membership check", "ordered iteration") and expected scale in a comment before implementing
- Choose data structures that match the pattern: dict for O(1) lookup, set for membership, sorted containers for ordered access
- Prefer built-in language/framework mechanisms over hand-rolled equivalents
- Justify non-obvious choices in docstrings so they aren't silently regressed later

### Python (Flask/FastAPI):
- Prevent N+1 queries using SQLAlchemy eager loading (`joinedload`, `selectinload`)
- Use caching (Redis or in-memory) for repeated expensive queries
- Use async/await for I/O-bound operations in FastAPI
- Configure database connection pooling for production workloads

### Python (PyQt):
- Never block the UI thread - use QThread or QRunnable for heavy operations
- Use model/view pattern (QListView, QTableView) instead of creating 1000+ widgets
- Emit signals for cross-thread communication instead of shared state

### React/Next.js:
- Memoize expensive computations with useMemo/useCallback
- Use lazy() and Suspense for code splitting large components
- Use virtual scrolling (react-window, react-virtualized) for lists >100 items
- Optimize images with next/image and proper sizing
- Avoid unnecessary re-renders by stabilizing props and state

## SEO Considerations

**Choose rendering strategy based on content type and SEO requirements.**

### Rendering Strategy Rules:
- Use SSR (Server-Side Rendering) for dynamic content that needs indexing (e.g., user profiles, search results, personalized pages)
- Use SSG (Static Site Generation) for content that rarely changes (e.g., marketing pages, blog posts, documentation)
- Use CSR (Client-Side Rendering) only for authenticated dashboards, admin panels, or apps where SEO doesn't matter
- In Next.js, use getServerSideProps for real-time data, getStaticProps for static content, and ISR (Incremental Static Regeneration) for content that updates periodically

### Technical SEO Rules:
- Implement canonical URLs to prevent duplicate content penalties
- Add hreflang tags for multilingual sites
- Handle redirects properly (301 for permanent, 302 for temporary)
- Use clean, descriptive URL structure (avoid query strings for content)
- Avoid duplicate content across pages
- Implement proper 404/error page handling
- Configure robots.txt to control crawling behavior
- Generate XML sitemaps with lastmod dates
- Handle pagination properly (rel="next/prev" or load-more patterns)
- Consider AMP pages for news/blog content when performance is critical

### On-Page SEO Rules:
- Include structured data (JSON-LD) for rich snippets (Article, Product, FAQ, etc.)
- Add Open Graph and Twitter Card meta tags for social sharing
- Maintain proper heading hierarchy (single H1, logical H2-H6 structure)
- Build internal linking strategy for content discovery
- Include breadcrumbs for navigation and schema markup
- Add descriptive alt text to all images
- Preload critical resources (fonts, hero images)
- Implement DNS prefetching for third-party domains

### Performance SEO Rules:
- Ensure Core Web Vitals pass (LCP, FID/INP, CLS)
- Implement mobile-first responsive design
- Optimize images (WebP format, proper sizing, lazy loading)
- Minimize render-blocking resources (CSS, JS)
- Configure proper caching headers (Cache-Control, ETag)
- Use CDN for static asset delivery

### Content SEO Rules:
- Write unique title tags per page (50-60 characters)
- Create compelling meta descriptions (150-160 characters)
- Use semantic HTML (proper landmarks, ARIA labels)
- Ensure proper alt text for all images
- Implement schema markup for relevant content types

## Real-Time Communication

**Use WebSockets (or Socket.io) for all live/real-time communication in web applications.**

### Rules:
- Use WebSockets or Socket.io for any feature requiring real-time data exchange (e.g., chat, live notifications, real-time dashboards, collaborative editing, live status updates)
- Do not use polling (setInterval, setTimeout with fetch) for live data - use persistent socket connections instead
- Prefer Socket.io for its built-in reconnection, room/namespace support, and fallback mechanisms
- Use plain WebSockets only when Socket.io's overhead is unnecessary or when a lightweight solution is required
- Ensure socket connections include proper authentication and authorization middleware
- Handle connection state changes (connect, disconnect, reconnect) gracefully on the client side
- Implement proper error handling and cleanup for socket connections to prevent memory leaks

## Security

**Implement defense-in-depth security across all layers of the application.**

### Authentication & Session Management:
- MFA by default (TOTP minimum, WebAuthn/passkeys preferred for sensitive data)
- Passwords: bcrypt/argon2id with tuned work factor (never MD5/SHA1)
- JWT: RS256/ES256 (asymmetric), short-lived (15-60min), validate iss/aud/exp/nbf claims
- Session cookies: HttpOnly + Secure + SameSite=Strict (or Lax), never store tokens in localStorage
- Rotate session IDs after privilege escalation
- Implement idle timeout (15-30min) and absolute timeout (8-24h)
- Brute-force protection: exponential backoff after 5 failures, not hard account lockout

### Access Control:
- Server-side enforcement on EVERY endpoint (not just hiding UI elements)
- RBAC/ABAC defined and evaluated server-side
- Principle of least privilege for database users and IAM roles
- Deny-by-default authorization

### Input Validation & Injection Prevention:
- Parameterized queries everywhere (ORM query builder preferred)
- Allowlist validation (not blocklist) at API boundary
- Contextual output encoding (HTML, JS, URL contexts require different encoding)
- Validate file uploads by magic bytes, not just MIME type/extension
- Content Security Policy with nonce-based scripts, block unsafe-inline

### Security Headers:
- Content-Security-Policy: nonce-based, block unsafe-inline
- Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: restrict camera, mic, geolocation to ()
- Cross-Origin-Opener-Policy: same-origin
- Cross-Origin-Resource-Policy: same-origin

### Secrets Management:
- All secrets in dedicated vault (AWS Secrets Manager, HashiCorp Vault, etc.)
- Never in source code, Dockerfiles, CI logs, or environment dumps
- Rotate secrets regularly, audit access

### Dependencies & Supply Chain:
- Use lockfiles and SRI hashes for CDN assets
- Automated vulnerability scanning in CI (Snyk, Dependabot, npm audit, pip-audit)
- Generate SBOM for releases
- Minimal dependency philosophy, evaluate trust posture before installing

### API Security:
- Rate limiting on every endpoint (token bucket or sliding window algorithm)
- CORS: never use wildcard (*) in production
- Object-level authorization (BOLA prevention) on every CRUD endpoint
- Validate Content-Type headers

### Encryption:
- TLS 1.2 minimum, TLS 1.3 preferred (disable SSLv3, TLS 1.0/1.1)
- HSTS preloading for production domains
- Encrypt sensitive data at rest
- Never roll your own cryptography, use vetted libraries

### Logging & Monitoring:
- Log auth events, authorization failures, input validation failures
- Never log passwords, session tokens, credit card numbers, or sensitive data
- Use tamper-evident logs
- Alert on anomalous behavior (impossible travel, velocity changes)

### PyQt Specific:
- Validate all local file operations (prevent path traversal)
- Encrypt local storage if storing sensitive data (QSettings)
- Validate IPC messages if using inter-process communication
- Never load untrusted plugins or extensions without sandboxing

## Error Handling & Logging

**Handle errors consistently and predictably across the entire application, so failures are debuggable and never silently swallowed.**

### Custom Exceptions:
- Create custom exception classes in dedicated `exceptions/` folder
- Group by domain (e.g., `AuthenticationError`, `PaymentError`, `ValidationError`, `NotFoundError`)
- Use meaningful naming that describes the error condition
- Include context data in exception (request ID, timestamp, relevant IDs)
- Inherit from base app exception for unified handling

### API Error Response Shape:
- Define a standard error response shape for APIs (e.g., `{ error: { code, message, details, request_id } }`) and use it everywhere, not ad hoc per endpoint
- Use HTTP status codes correctly (400 validation, 401 auth, 403 forbidden, 404 not found, 500 server)
- User-facing messages: human-readable, explain what went wrong and what the user can do next (avoid generic "Something went wrong" unless truly unexpected)
- Never expose internal error details (stack traces, DB errors, file paths) to end users; log them internally and return a generic, safe message instead
- Include correlation/request ID in error response so users can reference it when contacting support

### Global Error Handlers:
- Use a centralized error-handling middleware/boundary rather than repeating try/catch logic across every route or component
- Flask: use `@app.errorhandler` for global exception handling
- FastAPI: use `app.add_exception_handler` with `JSONResponse`
- React: use Error Boundaries for component-level error recovery; prevent a single component crash from taking down the whole page
- PyQt: use try/except with logging, emit signals for cross-thread errors
- Implement a "last resort" global error handler that catches all unhandled exceptions

### Error Classification:
- Distinguish between expected errors (validation failures, not found, unauthorized) and unexpected errors (bugs, crashes) in both handling and logging severity
- Expected errors (4xx): log at WARN level, return specific user-facing message
- Unexpected errors (5xx): log at ERROR level with full context (stack trace, request context, user ID), return generic safe message
- Never use empty catch blocks; every caught error must be logged, handled, or explicitly re-thrown with reasoning

### Structured Logging:
- Use structured logging (JSON format for production) rather than plain text, to support querying and alerting
- Standardize field names across all services: `service`, `level`, `event`, `timestamp`, `trace_id`, `request_id`, `user_id`
- Log events, not sentences; use snake_case event names (e.g., `payment_failed`, `user_authenticated`) for searchability
- Use log levels correctly:
  - DEBUG: detailed internal state, off in production by default, enable temporarily for troubleshooting
  - INFO: normal business events worth retaining (user signed up, order shipped, deployment completed)
  - WARN: something unexpected happened but the system recovered (retry succeeded, fallback triggered, deprecated endpoint used)
  - ERROR: something failed and requires investigation (payment failed, DB connection refused, external API 5xx)
  - FATAL: the process cannot continue, unrecoverable state (missing required config, connection pool exhausted)
- Never log sensitive data (passwords, tokens, PII, credit cards, API keys, session data); hash or redact at the logger level
- Log at system boundaries: HTTP requests/responses, database queries, external service calls, queue operations
- Don't log in tight loops or high-frequency paths; use sampling or DEBUG level for verbose output
- Don't use logs as metrics; use dedicated metrics systems for counts, rates, histograms
- Include correlation/request IDs in every log line for distributed tracing (X-Request-Id, trace_id from OpenTelemetry)
- Include trace_id and span_id in logs to correlate with distributed traces across services
- Include service version and environment in logs for deploy correlation
- Centralized logging service for production (ELK, Datadog, etc.)

### Log Protection & Retention:
- Implement log retention policies; don't keep logs forever
- Protect logs from unauthorized access and modification (security audit trail)
- Log security-relevant events: authentication decisions, access control failures, input validation failures, deserialization failures
- Encode log data to prevent log injection attacks

### Crash Reporting (Desktop/Mobile Apps):
- Generate crash logs with stack traces, system info, app version
- Store crash logs locally for offline scenarios
- Implement crash report client/modal for user submission
- Allow users to add description before sending
- Send via email (Resend, SendGrid) or dedicated crash reporting service
- Include in crash report: OS, app version, last actions, memory state
- Provide user feedback that crash was submitted
- For debugging: include request context, user actions leading to crash
- Consider services: Sentry, Bugsnag, or custom solution

### Alerting:
- Set up alerting for critical errors (auth failures spiking, payment failures, 5xx rates) rather than relying on manually checking logs
- Use SLO-based alerts: "error rate exceeds X% for Y minutes" rather than alerting on every individual error
- Separate symptom alerts (user-facing impact) from cause alerts (dependency failure) for faster triage

### Error Tracking & Uptime Monitoring:
- Integrate an error tracking tool (Sentry, Bugsnag, or equivalent) in every project from the start; unhandled exceptions must be captured automatically, not just logged locally
- Set up uptime monitoring on all production-facing URLs/APIs with alerts on downtime (Pingdom, UptimeRobot, or equivalent)
- Review and tune alert thresholds periodically to avoid alert fatigue (too many false positives) or missed incidents (thresholds too loose)

## Git Workflow

**Follow industry-standard Git branching and collaboration practices.**

### Rules:
- Create a new feature branch for every new feature or significant change
- Use descriptive branch names (e.g., feature/user-authentication, bugfix/login-error)
- Develop features in isolation without affecting the main branch
- Create Pull Requests (PRs) to merge feature branches into main, do not merge branches directly
- Keep feature branches short-lived (1-3 days) to minimize merge conflicts
- Ensure all CI checks pass before merging PRs
- Review code changes in PRs before merging to maintain code quality
- Main branch should always remain stable and production-ready
- Always write tests for every new feature
- Run all tests after completion of any new feature and before pushing to GitHub to confirm everything works well
- Ensure all tests pass before merging PRs

## Testing Strategy

**Define what "tested" means so coverage isn't left to interpretation, and tests aren't skipped or faked to pass CI.**

### Rules:
- Follow test pyramid as starting ratio: ~70% unit tests, ~20% integration tests, ~10% E2E tests
- Google's size model for measurable constraints: Small (≤60s, no network/DB/filesystem), Medium (≤300s, localhost services only), Large (≤900s, unrestricted)
- Write unit tests for all business logic, utility functions, and data transformations
- Write integration tests for API endpoints covering success, validation failure, and authorization failure cases
- Write integration tests for database queries, service boundaries, and API handlers against actual web stack
- Write end-to-end tests for critical user flows only (e.g., signup, checkout, core feature path), not every possible interaction
- Mock external services (payment providers, third-party APIs, email) in tests; never call real external services in automated test runs
- Do not mock the thing being tested itself (e.g., don't mock the function under test to force a pass)
- New features must include tests before being considered complete; do not defer "adding tests later"
- Bug fixes must include a regression test that reproduces the bug and confirms the fix
- Coverage by risk, not by mandate: require 80-90% coverage on new and changed lines (diff coverage), not arbitrary repo-wide targets
- A high coverage number proves lines executed, not that behavior was verified; prioritize meaningful assertions over hitting a percentage
- Never delete, skip, or comment out a failing test to make CI pass; fix the underlying issue or flag it explicitly for discussion
- Use realistic test data/fixtures, not placeholder values that don't exercise edge cases (empty strings, nulls, boundary numbers)
- Keep tests independent and order-agnostic; no test should depend on another test having run first
- Flaky tests are defects, not personality traits; quarantine them, track flake rate, and fix within a time-bound window
- Use factories/builders for readable test data setup, not shared mutable fixtures that leak state between tests
- Write tests at the lowest level that gives the confidence you need; if a unit test can catch it, don't write an integration test; if integration can catch it, don't write E2E
- Contract tests for service/API boundaries where one service depends on another; version the contract and validate compatibility before release
- Test the seam/contract, not the implementation details; avoid asserting implementation trivia
- Use transactional test isolation for database tests (rollback per test) rather than resetting full schema between tests
- CI lanes: fast lane on PR (lint, type checks, unit tests, fastest integration), confidence lane on merge (broader integration, contract verification, critical E2E), deep lane nightly (full E2E matrix, performance, resilience)
- Document testing conventions in a shared testing strategy document for team consistency
- If a higher-level test spots an error and no lower-level test is failing, write a lower-level test
- Test data should be explicit, minimal, and reusable; seed data owned by tests, not magical shared state
- Never test basic language/runtime behavior or snapshot giant objects without understanding them
- Avoid over-mocked "unit" tests that never touch the real boundary; a slower, realistic integration test is often worth ten brittle, over-mocked tests

## Environment & Setup

**Ensure any developer or agent can get a project running from a clean clone with zero guesswork.**

### Rules:
- Every project must include a `.env.example` file listing all required environment variables with placeholder values and a one-line comment on what each is for
- Never commit actual `.env` files or real secrets to the repository
- Include a `README.md` (or `SETUP.md`) with exact, copy-pasteable steps to install dependencies, set up the database, and start the dev server
- Document required tool versions explicitly (Node, Python, package manager) using version files where possible (`.nvmrc`, `.python-version`, `engines` in `package.json`)
- Use lockfiles (`package-lock.json`, `poetry.lock`, etc.) and commit them, never rely on floating versions
- Provide a single setup command or script (e.g., `make setup`, `npm run setup`) that installs dependencies, runs migrations, and seeds any required local data
- Document how to reset the local environment to a clean state (e.g., `make reset-db`)
- If Docker is used, provide a working `docker-compose.yml` for local development that starts all required services (DB, cache, etc.) with one command, including health checks
- Clearly state which OS/environment assumptions apply (e.g., "requires WSL on Windows") if any
- Never assume global system dependencies are installed; check and document them (e.g., Redis, Postgres, ffmpeg)
- Validate environment variables at startup (fail fast if missing required vars)
- Include troubleshooting section for common OS-specific issues
- Test setup script in CI to prevent drift
- Use EditorConfig for consistent formatting across IDEs
- Consider DevContainers for complex projects or mixed-OS teams

## CI/CD Compliance

**Always ensure code passes all CI checks before committing.**

### Rules:
- After ANY code changes (edit, create, delete), run these checks before committing:
  - `ruff check backend/` (lint)
  - `ruff format --check backend/` (format)
  - `npm run lint` (frontend lint, if frontend files changed)
  - `npm run build` (frontend build, if frontend files changed)
- If any check fails, fix ALL errors before committing
- Run tests when possible: `python -m pytest tests/ -v --tb=short` (requires test DB)
- Never commit code that fails lint or format checks

## Tech Stack Defaults

**Avoid re-deciding the stack on every project; default to a known, agreed-upon set of tools unless explicitly told otherwise.**

### Rules:
- Default stack per project type:
  - Backend APIs: FastAPI (Python)
  - Desktop apps: PyQt6 (Python)
  - Static/simple websites: Vite + React/TypeScript
  - Multi-user web apps: Next.js + React + TypeScript
  - Database: PostgreSQL (unless specific need dictates otherwise)
- Do not introduce a new framework, library, or major dependency without explicit confirmation, even if it seems like a "better" fit
- Prefer boring, well-supported, actively maintained tools over trendy or experimental ones unless the user specifically asks to explore something new
- If a project requires a stack outside the default (e.g., a data pipeline instead of a web app), state the proposed stack and reasoning before starting, and wait for confirmation
- Keep frontend, backend, and database choices consistent across projects of the same type unless there's a stated reason to diverge
- Avoid mixing multiple state management, styling, or ORM solutions within a single project
- When a new tool is genuinely needed mid-project, flag it explicitly rather than silently adding it to `package.json`/`requirements.txt`
- Never choose pre-1.0 or less than 2-year-old frameworks for production use
- Team expertise takes priority over theoretical "best" choices
- Document stack decisions and rationale for future reference

## API Design Conventions

**Keep API design consistent and predictable across the entire application so endpoints don't need to be relearned one by one.**

### Resource Naming & Structure:
- Use consistent naming conventions for endpoints with plural nouns for resources (e.g., `/users`, `/orders`), not a mix of styles
- Use kebab-case for multi-word resource names (e.g., `/blog-posts`, not `/blogPosts` or `/blog_posts`)
- Limit nesting depth to maximum two levels; use query parameters for deeper relationships (e.g., `/users/123/orders` not `/users/123/orders/456/items/789`)
- Use string IDs with prefixes (e.g., `usr_123`, `ord_456`) instead of sequential integers to prevent enumeration attacks and improve readability

### HTTP Methods & Status Codes:
- Follow standard REST verb/status code semantics: GET (read, 200), POST (create, 201), PUT/PATCH (update, 200), DELETE (remove, 204); do not repurpose verbs for unrelated actions
- Return meaningful HTTP status codes; do not return 200 for errors with an error flag buried in the body
- Use 400 for validation errors, 401 for authentication required, 403 for authorization denied, 404 for not found, 409 for conflicts, 422 for unprocessable entity, 429 for rate limited, 500 for server errors
- Every 4xx and 5xx response must have a body with error details; never return bare status codes

### Versioning:
- Version APIs explicitly (e.g., `/api/v1/...`) from the start, even for internal-only APIs, to avoid breaking changes later
- Use URL path versioning (`/v1/`, `/v2/`) as default; header versioning is harder to test and cache
- Only increment major version when introducing breaking changes (removed fields, renamed endpoints, changed response shapes)
- Additive changes (new fields, new endpoints, new optional params) are backward-compatible and do not require a new version
- Add `Deprecation` and `Sunset` headers when deprecating versions; provide migration timeline and documentation
- Keep breaking changes out of existing API versions; introduce a new version instead of silently changing behavior

### Response Design:
- Use a consistent, predictable response envelope for all endpoints (success and error), not a different shape per route
- For single resources: return directly or wrap in `{ "data": {...} }`
- For lists: wrap in `{ "data": [...], "pagination": {...} }` to include pagination metadata
- Use ISO 8601 UTC for all timestamps (`2024-03-15T14:30:00Z`); never use Unix timestamps or locale-specific formats
- Represent money as integer minor units (cents) to avoid floating-point precision issues
- Choose field naming convention (camelCase or snake_case) and enforce consistently; never mix in same API

### Pagination:
- Paginate all list endpoints by default; never return unbounded result sets
- Cursor-based pagination preferred for large/frequently-changing datasets; use opaque base64-encoded cursors
- Include `hasMore`, `nextCursor`, `previousCursor` in response pagination object
- Use offset pagination only for small datasets (<50k rows) or when users need random page access
- Include `Link` headers for pagination (next, prev, first, last) following RFC 5988

### Filtering, Sorting & Search:
- Use consistent filtering, sorting, and search query parameter conventions across endpoints (e.g., `?sort=-created_at&status=active`)
- Use query parameters for filtering, sorting, searching, and pagination; keep filter names consistent across endpoints
- Support field selection with `fields` parameter (e.g., `?fields=id,name,email`) to reduce payload size

### Validation & Documentation:
- Validate and document required vs optional fields for every endpoint; reject unknown fields rather than silently ignoring them
- Document all endpoints (OpenAPI/Swagger or equivalent) and keep the spec in sync with actual implementation
- Use OpenAPI 3.1 as single source of truth; generate SDKs and documentation from spec

### Error Handling:
- Use RFC 9457 Problem Details for error format (`application/problem+json`) with machine-readable `type`, human-readable `title`, and optional `errors` array for field-level details
- Define a standard error response shape (e.g., `{ error: { code, message, details, request_id } }`) and use it everywhere
- Include `trace_id` or `request_id` in error responses for debugging correlation

### Idempotency & Reliability:
- Design idempotent endpoints where applicable (GET, PUT, DELETE are idempotent by spec)
- Use `Idempotency-Key` header for POST requests on payment/critical actions; cache response for 24h
- Return error if parameters differ on retry with same idempotency key to prevent accidental reuse

### Rate Limiting & Security:
- See Rate Limiting section for full rate limiting strategy
- Put API keys and tokens in headers (Authorization, X-API-Key), never in query parameters
- Configure CORS explicitly with specific origins; never use wildcard (`*`) in production

### Webhooks:
- Implement webhook signing (HMAC-SHA256) with timestamp verification; reject messages older than 5 minutes
- Include event ID for idempotent processing; support retries with exponential backoff

### Breaking Changes:
- Define breaking vs non-breaking changes explicitly: non-breaking (adding fields, endpoints, optional params); breaking (removing/renaming fields, changing types, adding required params)
- Never make breaking changes without a version bump

## Database & Migrations

**Manage schema changes safely and predictably so migrations never risk data loss or break existing deployments.**

### Core Migration Rules:
- All schema changes must go through migration files; never modify the database schema manually in production or staging
- Migrations must be reversible where possible (provide both `up` and `down`); if a migration is not reversible, state this explicitly and why
- Use descriptive, timestamped migration file names that clearly state what the migration does (e.g., `20260715_add_email_verified_to_users`)
- Never edit a migration file that has already been run in any shared environment (staging/production); create a new migration to fix or amend it instead
- Keep seed data separate from migrations; seeds are for local/dev/test data, migrations are for schema changes only

### Expand-and-Contract Pattern:
- Use expand-and-contract pattern for zero-downtime migrations: expand (add new), dual-write, backfill, cut over reads, contract (remove old)
- Each phase is independently deployable and independently reversible; never skip phases
- Additive, backward-compatible changes preferred: add new columns as nullable or with defaults first, backfill data, then enforce constraints in a later migration
- Avoid renaming or dropping columns/tables in a single step if the app is still deployed with old code referencing them
- For column renames: add new column, dual-write, cut over reads, drop old column; never use RENAME COLUMN while old code is running
- For column type changes: add new column of new type, backfill, swap in app code, drop old column
- Deploy read switches behind feature flags with graduated rollout (1% -> 10% -> 50% -> 100%)
- Keep old code path alive and tested until rollback horizon has passed (minimum one week for critical tables)

### Safe DDL Operations:
- Use `CREATE INDEX CONCURRENTLY` for PostgreSQL (does not block writes); check `pg_index.indisvalid` afterward and retry if invalid
- Add foreign keys with `NOT VALID` first, then `VALIDATE CONSTRAINT` separately to avoid long locks
- Add `NOT NULL` columns as nullable first, backfill, then add constraint; on PostgreSQL 11+ adding a column with a volatile default is instant
- Set `lock_timeout` on migration sessions to fail fast instead of blocking production traffic
- Use online schema change tools for unsafe operations on large tables (gh-ost, pt-online-schema-change for MySQL; pg_repack for PostgreSQL)

### Backfill at Scale:
- Backfill in batches (1,000-10,000 rows per transaction) with sleep intervals between batches; never run a single giant UPDATE on large tables
- Use a unique key for batching (order by primary key); track progress so backfill can resume if interrupted
- Monitor replication lag during backfills; pause if lag exceeds threshold to avoid overwhelming read replicas
- Backfill should run as a proper background job with retries, cancellation, and monitoring; never run from a psql session on your laptop

### Deployment Sequencing:
- Never deploy code and schema in the same step; decouple them so you can roll back code without rolling back schema, and vice versa
- At every phase, the schema must be compatible with both the previous and the next application version
- Dual-write to both old and new columns in same transaction during migration; log mismatches loudly
- Have a rollback plan for every migration; some are reversible, some require "deploy forward"
- Define foreign key constraints and cascading rules explicitly (ON DELETE CASCADE/RESTRICT/SET NULL) rather than leaving referential integrity to application code alone

### Testing & Validation:
- Test migrations against a copy of production-like data volume before running on production, especially for large tables
- Test on a production-sized dataset, not just staging; staging/prod scale mismatch is the root cause of most migration incidents
- Run migration linting in CI (e.g., squawk for PostgreSQL) to catch dangerous patterns before production
- Back up the database before running destructive migrations in production

### Monitoring During Migration:
- Monitor during migration: lock waits, replication lag, query latency, user-visible errors
- Treat a migration as an incident-in-waiting; monitor actively while it runs, and confirm recovery when it's done
- If replication lag exceeds threshold during backfill, pause backfill until lag recovers

## State Management (Frontend)

**Choose the right level of state for the right scope, so state isn't unnecessarily global or awkwardly prop-drilled.**

### State Classification & Tool Selection:
- Use local component state (`useState`/`useReducer`) for state that only affects a single component and doesn't need to be shared
- Use React Context for state that needs to be shared across a small, related subtree (e.g., theme, current user session) — not for frequently-changing, high-frequency data
- Use a global state library (Zustand, Redux Toolkit, etc.) only when state genuinely needs to be accessed/mutated from many unrelated parts of the app; do not default to it for everything
- Use TanStack Query (or SWR) for server state (API data): automatic caching, background refetching, request deduplication, optimistic updates, retry with exponential backoff, loading/error states without boilerplate
- Use React Hook Form + Zod for form state: dirty tracking, validation, submission handling; don't put draft form values in global stores
- URL state should live in the URL (useSearchParams, nuqs): filters, pagination, search queries, sort order — shareable, bookmarkable, survives page refresh

### Server State vs Client State:
- Never duplicate server data into global client state unnecessarily; use TanStack Query for server state instead of manually syncing it into a store
- Keep server state (API data) and client/UI state (modals open, form input, active tab) clearly separated; don't mix them in the same store
- Avoid one mega-store mixing server and client state; keep them in separate stores/libraries
- For Next.js App Router: Server Components handle initial data fetch; TanStack Query manages client-side cache and mutations; Zustand stays out of the data path

### State Scope & Placement:
- Colocate state as close as possible to where it's used; lift state up only when multiple components genuinely need to share it
- Avoid prop drilling beyond 2-3 levels; if state needs to go deeper, move it to Context or a store instead of threading props
- Derive state where possible instead of storing redundant copies (e.g., compute a filtered list from source data rather than storing both the original and filtered array in state)
- Use `useMemo` for derived computed state instead of storing redundant copies; one source of truth prevents sync bugs
- Keep state as close to where it's consumed as possible; lift only when a real sharing need emerges
- Avoid putting derived/computed state in stores; derive it in selectors or `useMemo` instead
- Use `useRef` for mutable values that need to persist across renders but don't trigger re-renders (e.g., timers, previous values, DOM references)

### Re-render Optimization:
- Use `useCallback` for event handlers passed to child components to prevent unnecessary re-renders
- Avoid inline function definitions in JSX for props that trigger re-renders (e.g., `onClick={() => doSomething()}`)
- Use `React.memo` for pure components that receive the same props frequently and re-render expensive
- Use Zustand's `shallow` comparison for objects/arrays to prevent unnecessary re-renders when state shape is complex
- Use React's `useTransition` for non-urgent state updates (search filters, tab switches) to keep UI responsive during expensive re-renders
- Use React's `useDeferredValue` for expensive computations that can be deferred (filtering large lists, search results)

### Global State Best Practices:
- Zustand is the recommended default for global client state in 2026: minimal API, no providers required, selector-based subscriptions to prevent unnecessary re-renders (~3KB vs Redux Toolkit ~15KB)
- Always use selector functions with Zustand: `useStore(state => state.field)` not `useStore()` — subscribing to the whole store causes re-render on any state change
- Context API is not a state management solution; it's a dependency injection mechanism for rarely-changing values (theme, locale, auth, feature flags); every Context update re-renders every consumer
- Memoize Context value with `useMemo` to prevent unnecessary re-renders of consumers
- Zustand with `persist` middleware for state that survives page refreshes (theme preference, sidebar state)
- Avoid storing non-serializable values (functions, class instances, DOM nodes) in global state stores
- Never put filter/pagination state in Zustand; use URL search params so filters are shareable and survive refresh
- Use Redux Toolkit's `createSlice` and `createAsyncThunk` for Redux projects (never write reducers by hand)
- Consider Jotai for fine-grained atomic state when you have many small, independent pieces of state and render performance is constrained
- Implement proper Error Boundaries for state-related runtime errors; don't let a single component crash take down the whole page

### State Lifecycle:
- Reset/clear relevant state on logout or major context switches (e.g., switching workspaces/accounts) to prevent stale data leaks

### Decision Tree:
- Local UI state (one component): `useState`/`useReducer`
- Shared client state (multiple components): Zustand with selectors
- Server data (API/database): TanStack Query (or SWR)
- Global config (rarely-changing): Context API
- URL-relevant state (filters, pagination): URL search params
- Complex forms: React Hook Form + Zod
- Persistent state (survives refresh): Zustand + persist middleware

## File/Folder Structure

**Use a consistent, predictable project layout so agents don't invent a new structure per repo or per feature.**

### Rules:
- Organize by feature/domain rather than by file type for application code (e.g., `features/auth/`, `features/orders/` instead of scattering related files across top-level `components/`, `hooks/`, `services/` folders)
- Keep a consistent top-level structure across projects of the same type (e.g., `src/`, `tests/`, `public/`, `config/`) so switching between projects doesn't require relearning the layout
- Each feature/module folder should contain its own components, hooks, types, and tests colocated together, not spread across the repo
- Keep genuinely shared/reusable code (UI primitives, utilities, shared types) in clearly named top-level folders (`shared/`, `common/`, `lib/`) separate from feature-specific code
- Avoid deeply nested folder structures (more than 3-4 levels) that make files hard to locate
- Use `index.ts`/`index.js` barrel files sparingly and consistently, only where they genuinely simplify imports, not as a blanket default
- Name files and folders consistently (pick one casing convention: kebab-case, camelCase, or PascalCase per file type, and stick to it project-wide)
- Keep configuration files (env, build config, linting) at the project root; don't scatter config across nested folders
- Document the folder structure convention in the README so new features are added in the right place without guessing
- Never mix backend and frontend code in the same folder tree unless the project is explicitly a monorepo with clearly separated packages

### Absolute Imports & Path Aliases:
- Configure `tsconfig.json`/`jsconfig.json` with path aliases (`@/`, `@/features/*`, `@/shared/*`) to eliminate fragile relative imports like `../../components/Button`
- Prefer absolute imports for all internal modules to simplify refactoring and improve readability

### Module Boundary Enforcement:
- Every feature must expose public API only through `index.ts` — internal files are private implementation detail
- Add ESLint `no-restricted-imports` to prevent features from importing other features' internals directly
- Use `eslint-plugin-boundaries` to enforce layer rules automatically in CI

### Feature Internal Structure:
- Use consistent subfolders within each feature: `api/`, `model/`, `ui/`, `types/`, `index.ts`
- `api/` = networking + query/mutation hooks; `model/` = validation + business rules + types; `ui/` = feature-specific components
- Feature `index.ts` exports only the minimal public surface needed by routes or other features

### Dependency Direction Rules:
- `shared/` never imports from `features/`, `entities/`, or `routes/`
- `entities/` never imports from `features/` or `routes/`
- `features/` never imports from other `features/` (default rule; if cross-feature coupling is unavoidable, use a `relations/` subfolder to make it explicit)
- `routes/` or `pages/` can import from everything (composition layer)

### Test Colocation:
- Tests live next to the code they test (`Component.test.tsx` beside `Component.tsx`, not in a separate `tests/` folder)
- Feature-level `__mocks__/` folder for shared test fixtures specific to that feature
- Top-level `__tests__/` for cross-feature integration tests and E2E tests only

### Entities Layer (for scale):
- `entities/` holds domain nouns (User, Organization, Invoice) — stable concepts that multiple features reference
- Entities contain domain types, invariants, and domain helpers; they are not UI components
- Promote a concept to `entities/` only when two or more features actually need it

### Monorepo Structure (when needed):
- Use Turborepo + pnpm workspaces for multiple apps sharing component libraries and configs
- `apps/` for deployable applications (web, admin, docs); `packages/` for shared code (ui, config, tsconfig)
- Turborepo caches build outputs — changing a single component only rebuilds apps that depend on it

## Accessibility (a11y)

**Build applications usable by everyone, including people using assistive technology, by default — not as an afterthought.**

### Rules:
- Target WCAG 2.1 AA compliance as the minimum standard for all user-facing interfaces
- Use semantic HTML elements (`button`, `nav`, `main`, `header`, `label`) instead of generic `div`/`span` with click handlers
- Ensure full keyboard navigability: all interactive elements must be reachable and operable via Tab/Enter/Space/Escape, with a visible focus indicator
- Provide meaningful `alt` text for all images; use empty `alt=""` for purely decorative images
- Use proper ARIA labels/roles only when semantic HTML isn't sufficient; don't override native semantics unnecessarily
- Maintain a minimum color contrast ratio of 4.5:1 for normal text and 3:1 for large text/UI components
- Never rely on color alone to convey meaning (e.g., error states must also use icons/text, not just red color)
- Ensure form inputs have associated, visible labels (not just placeholder text as the only label)
- Manage focus properly in modals/dialogs: trap focus within the modal while open, and return focus to the triggering element on close
- Announce dynamic content changes (toasts, live validation errors) to screen readers using `aria-live` regions
- Test with keyboard-only navigation and a screen reader (VoiceOver, NVDA) for critical flows before considering a feature complete
- Respect user motion preferences (`prefers-reduced-motion`) for animations and transitions

### WCAG 2.2 Specific Criteria:
- 2.4.11 Focus Not Obscured — focused elements must not be hidden by sticky headers, cookie banners, or toasts; use `scroll-margin-top` on focusable elements sized to match sticky header height
- 2.5.7 Dragging Movements — provide keyboard/click alternative for drag-and-drop operations (e.g., arrow keys for reorder, accessible resize handles with `role="separator"`)
- 2.5.8 Target Size (Minimum) — interactive targets at least 24x24 CSS pixels; add padding or invisible pseudo-elements for small icon buttons
- 3.2.6 Consistent Help — help paths (contact links, FAQs) in same position/order across all pages
- 3.3.7 Redundant Entry — don't re-enter same info in same procedure; use autocomplete, carry forward previous input
- 3.3.8 Accessible Authentication — allow password paste, support passkeys, no CAPTCHA-only login

### Skip Navigation & Landmarks:
- Include a visually hidden "Skip to main content" link as first focusable element on every page
- Use `<header>`, `<nav>`, `<main>`, `<footer>` landmark elements for page structure
- Landmarks let screen reader users jump to content in one keystroke

### Heading Hierarchy:
- One `<h1>` per page; never skip heading levels (h1 → h3 breaks screen reader navigation)
- Screen reader users navigate by headings; broken hierarchy is like a book with wrong chapter numbers
- Use semantic heading elements for structure, not for visual styling

### Form Accessibility:
- Link errors to inputs with `aria-describedby` and `aria-invalid` attributes
- On submit failure, focus the first error field programmatically
- Use `role="alert"` for error summaries (assertive announcement for blocking errors)
- Use `requestAnimationFrame` when focusing after state update (React batches async, so focus() before DOM update targets nothing)

### Route Transition Focus (SPA):
- After client-side navigation, programmatically move focus to new page content
- Announce route changes to screen readers via `aria-live` region
- Render visually hidden focus target at top of each page for consistent focus landing

### Linting & Tooling:
- Enable `eslint-plugin-jsx-a11y` with recommended rules (catches missing alt, invalid ARIA, keyboard event issues)
- Use Radix UI, React Aria, or Headless UI for accessible primitives (Dialog, Dropdown, Tabs, Tooltip) — they handle focus trapping, keyboard navigation, and ARIA patterns correctly
- Never use `outline: none` on interactive elements; use `focus-visible` pseudo-class to show focus ring only for keyboard users

### Testing:
- Automated tools (axe-core, Lighthouse, jest-axe) catch only 30-50% of issues; manual keyboard/screen reader testing is required
- Test with VoiceOver on iOS and TalkBack on Android (mobile screen readers behave differently than desktop NVDA/JAWS)
- Tab through every interactive element in sequence; confirm focus is always visible, never unintentionally trapped, and returned to logical position when modal/drawer closes

## Third-Party Integrations

**Integrate external services deliberately and consistently, so vendor choices and integration patterns don't vary unpredictably project to project.**

### Rules:
- State the default vendor per integration category before starting (e.g., payments: Paystack/Flutterwave; auth: Clerk/Auth0; email: Resend; file storage: S3/R2) and don't introduce a different vendor without explicit confirmation
- Wrap every third-party service behind an internal abstraction/interface (e.g., a `PaymentProvider` module) rather than calling the vendor's SDK directly throughout the codebase, so the vendor can be swapped without a full rewrite
- Store all third-party API keys/secrets in the secrets vault, never hardcoded or committed, and scope keys to the minimum permissions needed
- Handle third-party outages gracefully: implement timeouts, retries with backoff, and fallback behavior (e.g., queue for later) rather than letting a failed external call crash the request
- Verify webhooks from third-party services using signature verification; never trust webhook payloads without validation
- Log all third-party API failures with enough context to debug (which service, which call, response code) without logging sensitive payloads
- Track third-party API usage/rate limits and handle rate-limit responses (429) with backoff rather than retry-storming
- Keep a record (README or `INTEGRATIONS.md`) of every third-party service used, what it's for, and where its credentials/config live
- Avoid adding a new third-party dependency for functionality that can be reasonably built in-house, unless it meaningfully saves time/risk (e.g., auth, payments)
- Test integration failure paths explicitly (mocked timeouts, error responses), not just the happy path

### Contract-First Integration:
- Define data contracts/payloads before building; version contracts with MAJOR.MINOR.PATCH
- Use tolerant readers — accept new fields from vendors without breaking; reject missing required fields
- Monitor vendor changelogs and deprecation schedules proactively
- Map vendor error codes to stable internal error codes for consistent handling

### Idempotency & Deduplication:
- Use idempotency keys for all non-GET requests (especially payments, emails)
- Assume at-least-once delivery for webhooks; store event IDs and dedupe before processing
- Use upserts by external ID rather than inserts to prevent duplicates

### Dead Letter Queues (DLQs):
- Capture failed events with payload, metadata, attempts, and correlation ID
- DLQs are not graveyards — provide controlled replay tooling for triage and recovery
- Split automated replay from human review for permanent failures

### Webhook Security (OWASP):
- Verify HMAC signatures from raw request body (not parsed JSON); use constant-time comparison
- Use dual-secret window for rotation — accept old+new secrets during transition
- Validate timestamps (±5 min window) to prevent replay attacks
- Reject HTTP — enforce TLS 1.2+ on all webhook endpoints
- Prevent SSRF — validate callback URLs against internal IPs/metadata endpoints (127.0.0.0/8, 10.0.0.0/8, 169.254.169.254)

### Token Lifecycle Management:
- Use short-lived access tokens; refresh before expiry
- Alert on repeated refresh failures (indicates revoked consent or vendor outage)
- Rotate credentials regularly; build "disconnect" path for revocation
- Store secrets in vault, never in code, logs, or config files
- Use per-webhook secrets — a single shared secret is a single point of failure

### Correlation & Observability:
- Propagate request/correlation IDs end-to-end for traceability
- Log metadata (service, response code, latency), not sensitive payloads
- Track rate limit headers (remaining, reset) to forecast throttling
- Normalize upstream errors to stable internal error codes

### Error Handling Patterns:
- Classify errors: validation (400/422, no retry), auth (401/403, no retry), rate limit (429, retry with Retry-After), transient (502/503/504, retry with backoff)
- Cap retries to 2-3 attempts for user-facing requests
- Honor Retry-After header on 429 responses
- Never return raw upstream errors to frontend — normalize to consistent error shape

### BFF Pattern (Backend-for-Frontend):
- Keep third-party credentials server-side via API routes/BFF
- Never expose API keys in client bundles (Next.js: avoid `NEXT_PUBLIC_` prefix for secrets)
- Expose a stable internal contract; adapt vendor changes behind it

### Outbound Throttling:
- Enforce client-side rate limiting to prevent DDoSing your vendor
- Use token bucket or queue for batch jobs; centralized throttling for serverless

### Two-Provider Rule:
- Only build abstraction layer when you have, or can realistically anticipate, a genuine second option
- Don't abstract just for "cleanliness" — the switching cost must be real and significant

### Decorator Pattern for Cross-Cutting Concerns:
- Compose logging, caching, retry, circuit breaking as independent decorators wrapping adapters
- Each decorator is independently testable and reusable across any adapter

### Testing:
- Contract tests for request/response shapes and required fields
- Auth tests that validate token refresh and scope constraints
- Idempotency tests that send duplicates and verify no duplicate writes
- Fixture runs against sandbox vendor accounts using representative data

## Deployment & Environments

**Keep environments consistent and deployments predictable, so what works in staging works in production.**

### Rules:
- Maintain at least three environments: local/dev, staging, and production; staging must mirror production as closely as possible (same infra type, similar data shape) — for cost optimization, staging can use smaller instance sizes or be stopped outside business hours, but must match production's architecture and configuration (see Cost/Resource Awareness for budget-conscious staging strategies)
- Never test new features directly in production; staging must be used first for any change that touches shared infrastructure or data
- Use environment-specific config via environment variables, never hardcoded environment checks scattered through the codebase (`if (env === 'prod')` sprinkled everywhere)
- Automate deployments through CI/CD; never deploy by manually copying files or running ad hoc commands against production
- Require all CI checks (lint, tests, build) to pass before a deployment can proceed
- Use feature flags for risky or incomplete features instead of long-lived feature branches, so code can be merged to main safely and toggled on/off independently of deployment
- Implement a clear rollback strategy (previous build/image kept ready, or one-command rollback) for every deployment pipeline
- Run database migrations as a distinct, controlled step in the deployment pipeline, not bundled invisibly into app startup
- Use zero-downtime deployment strategies (blue-green, rolling) for production; avoid deployments that require taking the app fully offline
- Tag/version every production release (git tags or release names) so any deployed state can be traced back to an exact commit
- Restrict production deployment and infrastructure access to authorized roles only; no direct production database or server access for routine work

### Artifact Immutability:
- Build a single immutable artifact once; promote that exact build through staging and production unchanged
- Never rebuild per environment — inject config via environment variables at runtime
- Treat the CI runner as a high-value target with OIDC, SBOMs, and provenance

### Trunk-Based Development:
- Short-lived branches (1-2 days max), merge to trunk daily
- Feature flags decouple deploy from release — merge incomplete work behind a flag
- Require at least one approval and passing CI before merge to trunk
- Google runs 35,000+ developers on one monorepo trunk — the model scales

### Expand-Contract Pattern (Database Migrations):
- Expand: add new schema element without removing old ones
- Migrate: gradually update code to use new structure; backfill data
- Contract: remove old structure once new is fully adopted
- This is the only pattern that actually solves zero-downtime schema changes
- Blue-green does not save you — database is shared between blue and green

### Health Checks:
- Include health check endpoints (`/health`, `/ready`) that verify critical dependencies (DB, cache, external services) are reachable, not just that the server process is running
- Shallow health checks for container startup; deep health checks for application readiness
- Synthetic transaction tests for end-to-end validation
- Circuit breakers in health checks — return healthy with degraded mode if external deps fail

### Canary Deployments:
- Start with 1-5% traffic; expand based on error rate, latency percentiles, business metrics
- Automated rollback thresholds — halt if metrics degrade
- Use Argo Rollouts or Flagger for progressive delivery on Kubernetes
- Include conversion and business metrics in health gates, not just technical metrics

### Pod Disruption Budgets:
- Ensure minimum available pods (e.g., 70%) during rolling updates
- Prevent voluntary disruptions from taking down too many instances

### Deployment Observability:
- Annotate deployments on dashboards for quick correlation when errors appear
- Tag deployments with version, commit, and timestamp
- Track DORA metrics: deployment frequency, lead time, change failure rate, MTTR

### Rollback Drills:
- Monthly rollback drill for each major service
- Measure time from rollback command to full traffic restoration
- If MTTR > 5 minutes, your deployment strategy is not actually safe
- Test the rollback path in staging at least once a month

### GitOps:
- Declarative state management via Git (ArgoCD, Flux)
- Deployment pipeline becomes auditable, reproducible, and rollback-capable through Git operations

### Conventional Commits:
- Use `feat:`, `fix:`, `chore:` for automated changelogs and semantic versioning
- Block merges automatically when commit messages don't follow the format

### Supply Chain Security:
- Generate Software Bill of Materials (SBOM) for releases
- Use SRI hashes for CDN assets
- Automated vulnerability scanning in CI (Snyk, Dependabot)

### Feature Flag Lifecycle:
- TTL and auto-removal reminders to prevent tech debt
- Flag lifecycle policy — don't let flags accumulate forever

### Multi-Stage Pipeline:
- Build → Test → Staging → Production with quality gates
- Each stage catches a different class of problem

### Smoke Tests:
- Post-deployment critical path verification
- Monitor error rates, latency, saturation against baseline thresholds
- Auto-rollback if metrics degrade

### Dashboards & Infrastructure Metrics:
- Set up dashboards for key business/health metrics (signups, active users, error trends) so issues are visible without digging through raw logs
- Monitor infrastructure-level metrics (CPU, memory, disk, DB connection pool usage) in addition to application-level metrics
- Track key application metrics (response times, error rates, request volume) per endpoint/service, not just overall uptime

## Documentation Standards

**Keep documentation accurate and current so agents and developers can rely on it instead of re-discovering context by reading code.**

### Rules:
- Every project must have a `README.md` covering: what the project is, tech stack, setup instructions, and how to run/test it locally
- Document complex or non-obvious business logic inline (why, not just what) — code comments should explain reasoning that isn't self-evident from the code itself
- Keep API documentation (OpenAPI/Swagger or equivalent) in sync with actual implementation; update it in the same PR as the API change, not as an afterthought
- Maintain a `CHANGELOG.md` with entries per release/PR describing what changed, following a consistent format (e.g., Keep a Changelog style: Added/Changed/Fixed/Removed)
- Document architectural decisions that affect the whole project (e.g., "why we chose X over Y") in a lightweight ADR (Architecture Decision Record) format, kept in the repo
- Update the README/docs in the same PR as the code change that makes them outdated; don't defer documentation updates to "later"
- Avoid documenting implementation details likely to change frequently (exact line numbers, internal variable names); document behavior and contracts instead
- Keep a single source of truth per topic; don't duplicate the same setup instructions or environment details across multiple docs that can drift out of sync
- Document known limitations, edge cases, and TODOs explicitly rather than leaving them undocumented in code
- Write documentation assuming the reader (human or agent) has no prior context on this specific project, even if they know the general stack

### API Documentation Tools:
- For FastAPI: use `scalar_fastapi` for modern, interactive API docs (rising in 2026 over Swagger UI)
- Alternative: ReDoc for polished, read-only consumer-facing documentation
- All derive from OpenAPI spec — write once, use everywhere
- Lint OpenAPI spec in CI with Spectral to enforce style guides

### OpenAPI as Source of Truth:
- Write OpenAPI 3.1 spec once; documentation, SDKs, mock servers, and test suites derive from it
- Eliminates documentation drift where prose docs and actual API behaviour diverge
- Include request/response schemas, required fields, authentication requirements, and HTTP status codes for every endpoint
- Test OpenAPI spec in CI to verify all critical endpoints are documented

### API Documentation Structure (5 Pillars):
- Reference: complete endpoint list with parameters, schemas, examples
- Guides: explain concepts and design decisions
- Tutorials: step-by-step for specific goals
- Code Examples: copy-paste snippets in multiple languages (cURL, Node.js, Python)
- Changelog: what changed, when, migration notes

### Architecture Decision Records (ADRs):
- Use Nygard template: Title, Status, Context, Decision, Consequences
- One decision per document, couple of pages max, written in plain language, active voice
- Include alternatives considered and trade-offs made
- Keep in repo: `docs/decisions/` or `docs/adr/` — not in wikis
- ADRs are immutable once accepted; create new ADR for changed decisions
- Never delete ADRs — mark as superseded with link to new ADR
- Quarterly ADR review to update statuses and prevent ADR rot

### ADR Lifecycle:
- Proposed → Accepted → Deprecated → Superseded
- Status tracking makes current state of each decision clear
- Superseding ADR links to original to preserve reasoning history
- Link ADRs from code in files shaped by the decision

### ADR in PR Process:
- Add ADR checkbox to PR template for significant changes
- Reviewers ask "is ADR present or linked?" for new dependencies, data storage changes, API contracts
- ADRs are documentation, not bureaucracy — lightweight PR review, not committee meeting

### Changelog Best Practices:
- Follow Keep a Changelog format with semantic versioning
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security
- Include migration guides for breaking changes
- Link changelog from API documentation and `Deprecation` headers

### API Deprecation Strategy:
- Include `Deprecation` and `Sunset` headers in responses
- Link to migration guide from deprecation notice
- Provide timeline (e.g., "sunset: 2026-12-31")
- Never remove without notice — deprecate first, remove later

### Docs-as-Code:
- Treat documentation like code: version-controlled in Git, reviewed in PRs, auto-deployed
- Update docs in same PR as code change that makes them outdated
- Don't defer documentation updates to "later"
- ADRs in repos are reviewed in PRs, versioned with git, visible to engineers browsing codebase

### Security for Documentation:
- If using CDN-loaded Scalar/Swagger, set Content Security Policy headers
- Gate docs behind environment variable (e.g., `API_DOORS_ENABLED=true`) for self-hosters

## AI Agent Boundaries

**Define what an AI agent must never do autonomously, so high-risk actions always require explicit human approval.**

### Rules:
- Never push directly to `main`/`master` or any production branch; always work through feature branches and PRs
- Never delete or truncate production data, tables, or databases without explicit, one-time confirmation for that specific action
- Never rotate, revoke, or regenerate production secrets, API keys, or credentials without explicit confirmation
- Never run destructive database migrations (drop column/table, irreversible data transforms) against staging or production without explicit confirmation and a backup taken first
- Never deploy directly to production; deployments go through the defined CI/CD pipeline and environment promotion path
- Never modify billing, payment configuration, or third-party account settings without explicit confirmation
- Never install new dependencies, upgrade major versions, or change the tech stack without flagging it first (see Tech Stack Defaults)
- Never disable, weaken, or bypass security controls (auth checks, CSP, rate limiting) to "make something work faster," even temporarily
- Never commit secrets, API keys, or credentials to the repository, even in a "temporary" or "test" commit
- When an action is irreversible or affects shared/production environments, state the risk clearly and wait for explicit confirmation before proceeding, even if previously given broad permission for the task
- If uncertain whether an action falls into a restricted category, treat it as restricted and ask first

### Cognitive-Executive Separation:
- The system that reasons about actions must be structurally unable to execute them
- The system that executes actions must be structurally unable to reason about them
- Independent, immutable validator interposed between reasoning and execution
- When reasoning system is compromised, prompt-level guardrails provide zero protection — architectural boundaries hold regardless

### Default Deny:
- Requests matching no policy are rejected — never silently allowed, never routed to an unowned queue
- "Ask a human" is something you opt into with an explicit catch-all policy
- Unmatched request means missing policy (configuration bug), not silent passage
- When policy engine errors, right answer is `fail-closed` — not `fail-open`

### Separation of Duties:
- The identity that creates an approval request must be distinct from the identity that decides it
- Enforce in decision logic, not just UI — database is the only place a code path cannot route around
- High-blast-radius actions deserve n-of-m (two finance approvers for transfer above threshold)

### Temporal Scope:
- Approvals have a lifetime; approve-once ≠ approve-forever
- Approve once is the default — grant covers exactly this request
- Standing grants (approve-for-an-hour) are separate, deliberate choice with declared scope and TTL
- Every standing grant is revocable and appears in a list humans can see and cancel
- An approval you cannot enumerate is a permission you have lost control of

### Immutable Audit Trail:
- Every approval decision records provenance: which category, which actor, why it was allowed
- Categories: policy match, tool flag, human decision, standing grant, system override
- Capture full sequence: request → classification → decision → execution → outcome
- Audit trail must be append-only and queryable by tenant, action type, decision, date range
- Audit trail captures human approval decision AND downstream execution outcome for compliance

### Break-Glass is a Feature:
- Emergency path: explicit, attributable, time-boxed, loud — not a service-role key handed out in dark
- Explicit: distinct action (`emergency_override`), never side effect of missing policy or expired SLA
- Attributable: invoked by named human, recorded as its own provenance category, never anonymous
- Time-boxed: elevated grant expires in minutes, not "until someone remembers to revoke"
- Loud: fires notification to second party as it happens, lands on review queue afterward
- Using break-glass should feel like pulling a fire alarm, not flipping a switch

### Confidence Thresholds:
- Per-action-type thresholds, not a single global value
- Low confidence (below threshold) routes to review regardless of action type
- A 0.85 threshold for 'send external email' may be appropriate; 'delete production record' requires explicit human sign-off regardless of confidence
- Expose confidence scores, action risk classifications, agent reasoning traces in review UI

### Payload Locking:
- Lock approved payload with HMAC signature before inserting into execution queue
- Verify signature in execution worker before running
- If payload mutated, reject and re-route to review rather than proceeding with unreviewed action
- Approved payload is cryptographically locked to prevent mutation between approval and execution

### Fail-Closed:
- When policy engine errors, right answer is `fail-closed` — not `fail-open`
- When approver doesn't respond before SLA, right answer is `expired → reject` or `expired → escalate` — not `expired → allow`
- Unanswered requests default to deny after configurable timeout (e.g., 300 seconds)

### Reversible Execution:
- Capture pre-destructive state to enable rollback when validation fails
- Actions affecting external systems (API calls, emails) may not be reversible
- For irreversible external actions, pre-execution policies should require human approval
- Reversible Execution reduces blast radius within local environment but cannot guarantee reversibility for external side effects

### Rate-Limit Approvals:
- Rate-limit human approval requests to prevent approval fatigue attacks
- Adversary floods user with benign-seeming requests to induce reflexive approval
- Measure p50/p95/p99 latency from request to decision per policy — gate that is slow is agent that is effectively offline

### No Secrets in Logs:
- Never log sensitive data (passwords, tokens, PII, credit cards, API keys)
- Hash or redact at the logger level, not in application code
- Redact PII at the edge (in SDK) so only metadata and content hash reach approval infrastructure

## Cost/Resource Awareness

**Flag operations that cost real money or consume significant resources before running them, so nothing expensive happens silently.**

### Rules:
- Flag before running any operation that incurs direct monetary cost (paid API calls with per-request pricing, cloud resource provisioning, sending bulk emails/SMS) and state the estimated cost if possible
- Flag before running large-scale or long-running database operations (full table scans, bulk updates/deletes on large tables) that could impact performance or incur cost on managed DB services
- Avoid unnecessary repeated calls to paid third-party APIs during development/testing; use mocks, sandbox/test-mode credentials, or cached responses instead
- Be explicit about compute-intensive operations (large batch jobs, AI model calls on large datasets, video/image processing at scale) and their expected resource/time footprint before starting
- Default to the smallest viable resource tier/instance size for new infrastructure; scale up deliberately based on actual measured need, not preemptively
- Avoid provisioning new cloud infrastructure (databases, servers, storage buckets) without confirmation, since these often carry ongoing costs even when idle
- When choosing between a paid third-party service and a free/open-source alternative, state the tradeoff (cost vs. time/maintenance) rather than defaulting to whichever is more familiar
- Set or recommend usage limits/budget alerts on metered services (cloud spend alerts, API usage caps) to prevent runaway costs from bugs or loops
- Avoid unbounded loops or retries against paid APIs; always cap retry counts and use backoff

### Cost Forecasting:
- Forecast per scope (team, service, environment), not organization-wide
- Combine trend-based forecasting with known drivers (product launches, team growth)
- Reforecast weekly (operational) and monthly (full review); quarterly strategy alignment
- Track forecast accuracy with Mean Absolute Percentage Error (MAPE); target <15%
- Account for commitment expirations — reserved instance/Savings Plan expirations cause baseline jumps

### Budget Alerts with Graduated Thresholds:
- Alert at 50% — early warning to team owner
- Alert at 80% — approaching limit, escalate to engineering lead + finance
- Alert at 100% — projected overrun, executive review
- Alert at 110% — trigger automated review or approval workflow
- Route alerts via email, Slack, Teams, or PagerDuty; don't let them sit unread
- None of the major cloud providers automatically cap usage when budget exceeded — alerts are notification-only, not enforcement

### Anomaly Detection:
- Catch sudden cost spikes before they blow through budget
- Baselining current spend, then flag deviations from historical patterns
- Run continuously, not on a review cycle — waste between reviews is where largest unplanned costs accumulate
- Anomaly detection complements threshold alerts (catches spikes, not just gradual drift)

### Tagging for Cost Allocation:
- Mandatory tagging at resource creation, enforced via policy-as-code (AWS Service Control Policies, Azure Policy, GCP Organization Policy)
- Block untagged resource creation — don't audit after the fact
- Keep tag schema small and enforceable; comprehensive schemas nobody follows are worse than small ones everyone uses
- 40-60% of resources untagged in organizations that leave tagging optional
- Use tags to attribute cost to teams, projects, environments, and cost centers

### Rightsizing:
- Match resource size to actual workload demand, not "to be safe" overprovisioning
- Rightsize before you commit — single most expensive mistake is buying reservations before rightsizing
- Use cloud provider recommendations (AWS Compute Optimizer, Azure Advisor, GCP Recommender)
- Track waste rate: percentage of spend on idle or underutilized resources

### Scheduled Shutdowns:
- Shut down non-prod resources after hours and on weekends
- Schedule automated shutdowns via policy-as-code, not manual processes
- Non-prod environments running 24/7 often account for 30-40% of waste

### Cost-Per-Unit Metrics:
- Track cost per user, per training run, per inference, per transaction
- Makes cost visible in units the organization can reason about
- Ties cloud spend to business value, not just raw infrastructure

### Showback/Chargeback:
- Showback: make cost visible to teams without billing them (changes behavior through awareness)
- Chargeback: bill teams directly for their consumption (changes behavior through accountability)
- Most organizations start with showback, graduate to chargeback once allocation is trusted

### Policy-as-Code for Cost Guardrails:
- Enforce cost rules automatically at resource creation: block expensive instance types, require approval above threshold, prevent public data egress
- Version-controlled, applied through native tools or open-source engines
- Constrains genuinely dangerous actions without slowing everyone down

### Orphaned Resource Detection:
- Find and clean up abandoned resources: unused instances, unattached disks, forgotten sandboxes
- 30-40% of cloud spend is typically waste (idle instances, oversized resources, unattached storage)
- Run continuous cleanup, not one-time sprints

### Cross-Team Cost Reviews:
- Monthly operational review: variance against budget, top cost drivers, anomalies
- Quarterly deeper audits: KPIs, commitment utilization, waste rate
- Engineering + finance in same review cycle — cost decisions need both perspectives

### Cost Anomaly Response Runbook:
- Documented process when alert fires: investigate root cause, take corrective action, prevent recurrence
- Don't let alerts become ignored emails — turn alert into fixed problem

## Versioning & Changelog

**Version releases predictably and record what changed, so it's always clear what's deployed and why.**

### Rules:
- Follow Semantic Versioning (MAJOR.MINOR.PATCH) for all releases: MAJOR for breaking changes, MINOR for backward-compatible features, PATCH for backward-compatible fixes
- Tag every production release in git with its version number, matching the version in `package.json`/`pyproject.toml`/equivalent
- Update `CHANGELOG.md` in the same PR as the change, not retroactively; every user-facing or API-facing change gets an entry
- Group changelog entries by type (Added, Changed, Fixed, Removed, Security) for readability, following a consistent format (e.g., Keep a Changelog)
- Write changelog entries in plain language describing user/developer impact, not raw commit messages or internal implementation details
- Bump the MAJOR version and document a migration guide for any breaking change (API contract change, removed feature, incompatible config change)
- Never silently break backward compatibility within the same MAJOR version
- Keep API versioning (see API Design Conventions) and application/package versioning tracked separately but referenced from each other where relevant
- Archive or clearly mark deprecated features in the changelog with a removal timeline before actually removing them
- Ensure PR titles/commit messages are structured (e.g., Conventional Commits: `feat:`, `fix:`, `chore:`) so changelogs and version bumps can be generated or verified consistently

### Pre-release Versions:
- Use pre-release identifiers: `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.1`
- Pre-release precedence: alpha < beta < rc < stable
- Use alpha for early development, beta for feature-complete, rc for release candidate

### 0.x.y Strategy:
- During initial development, use `0.x.y` — anything may change at any time (no stability promise)
- During `0.x`, `feat:` commits bump patch (0.1.0 → 0.1.1), `feat!:` bumps minor (0.1.0 → 0.2.0)
- Graduate to `1.0.0` deliberately — it's a commitment to backwards compatibility
- Starting at `v1.0.0` on day one is wrong if the API is still unstable

### Version Ranges in Package Managers:
- `^1.2.3` = compatible with 1.2.3 (same MAJOR) — npm default
- `~1.2.3` = close to 1.2.3 (same MINOR) — more conservative
- `1.2.3` = exact version — pin for reproducibility
- Document which range strategy your project uses

### Automated Versioning Tools:
- semantic-release: fully automated, commit-driven, publishes packages
- release-please: Google-maintained, creates Release PRs with changelog
- standard-version: simpler, local-first, generates changelog and tags
- Use one of these — manual versioning is error-prone and inconsistent

### commitlint Enforcement:
- Enforce Conventional Commits with commitlint in local hooks (Husky) and CI
- Bad commits fail locally — fast feedback, no waiting for CI
- CI blocks merge for non-conforming commits — no exceptions
- Use squash-based workflow so lead maintainers can clean up commit messages on merge

### CHANGELOG.md Structure:
- Keep `[Unreleased]` section at top — accumulate changes between releases
- Use ISO 8601 dates (YYYY-MM-DD) — unambiguous across locales
- Link version to git tag comparison (e.g., `[2.1.0]: https://github.com/org/repo/compare/v2.0.0...v2.1.0`)
- Every version gets an entry — gaps erode trust
- List newest version first
- Hide `chore`, `docs`, `test` commits from changelogs — nobody reads those in release notes

### Release Notes Timing:
- Ship release notes when release ships, or within 24 hours
- Late release notes are worse than no release notes
- Make "update changelog" a PR checkbox or Definition of Done item
- The person who ships the change writes the entry — they understand the context

### Deprecation Before Removal:
- Give users at least one MINOR version cycle to migrate (ideally two or three)
- Deprecation entry format: "[Feature] is deprecated. It will be removed in [version/date]. Use [alternative] instead. [Link to migration guide]."
- Track deprecation notices in changelogs automatically
- Never remove without deprecating first

### Breaking Changes First:
- Breaking changes go first in changelog, in their own section
- Include migration steps — no exceptions
- "We didn't think anyone used that" is not an excuse
- Document breaking changes in commit footer with `BREAKING CHANGE:` or `!` suffix

### Changelog Anti-patterns to Avoid:
- Commit log dump — raw git log is noise, curate 5-8 entries from 50 commits
- "Various bug fixes" — means nothing, describe the fix or leave it out
- Missing breaking changes — burns customers, loses trust
- Inconsistent timing — readers stop trusting and stop reading
- Inconsistent granularity — aim for 3-10 entries per release

### Link Changelog to User Feedback:
- Explain what motivated the change: "Added CSV export (your #3 most requested feature)"
- Turns changelog from product record into relationship-building tool
- Connect releases to user feedback when possible

### Docker Image Tagging with Semver:
- Release of `v2.3.1` produces three tags: `2.3.1`, `2.3`, and `2`
- Users pinning to `2` get compatible updates; `2.3.1` gets exactly that
- Tag Docker images with semver, not just commit SHAs

### Monorepo Versioning:
- Independent versioning: each package versions separately based on its changes
- Linked versioning: group packages that must release together
- Use release-please `linked-versions` or similar for lockstep
- Commits scoped to a package only bump that package

### Keep a Changelog Principles:
- Changelogs are for humans, not machines
- Every version should have an entry (don't skip)
- Group by type: Added, Changed, Deprecated, Removed, Fixed, Security
- Show release date in ISO 8601
- Follow Semantic Versioning
- List newest version first

## Modularity

**Keep code broken into small, focused, loosely-coupled pieces so any single file or module can be understood, tested, and changed in isolation.**

### Rules:
- Cap file/function length as a soft limit (e.g., ~200-300 lines per file, ~40-50 lines per function); if exceeded, split by responsibility rather than growing the file further
- Each module/component/service should have a single, clearly stated responsibility; if it needs "and" to describe what it does, split it
- Build a shared, reusable component library for UI elements used in more than one place; avoid copy-pasting near-identical components across features
- Extract common logic (validation, formatting, calculations) into shared utility/helper functions rather than duplicating it inline across files
- Organize by feature/domain (see File/Folder Structure) so each module's boundaries match a real business concern, not an arbitrary technical layer
- Enforce a clear dependency direction: lower-level modules (utilities, data access) should not import from higher-level modules (UI, feature logic); avoid circular dependencies
- Separate business logic from presentation: UI components should call into hooks/services for logic rather than embedding data-fetching, calculations, or business rules directly
- Define clear interfaces/contracts (prop types, function signatures, API schemas) between modules so internals can change without breaking consumers
- Centralize configuration and constants (feature flags, magic numbers, hardcoded strings) in dedicated config files rather than scattering them inline across components
- Expose a minimal, intentional public API per module (via barrel exports or explicit exports); keep internal implementation details unexported and not directly imported by other modules
- Favor composition over inheritance and over deeply nested conditional logic; break complex conditionals into smaller, named functions

### Independent Variation Principle (IVP):
- Separate elements that vary independently; unify elements that vary dependently
- Ask "who or what causes this code to change?" to determine module boundaries
- Elements governed by different change drivers should be in different units
- Elements governed by the same change driver should be in the same unit
- This is not a matter of taste — module boundaries are a mathematical consequence of minimizing change propagation cost

### Change Driver Analysis:
- Identify change drivers: pricing team, compliance department, infrastructure group, external API
- Different actors, different business domains, different technical concerns = different modules
- Analyze version control history to identify who requests changes and why
- Ground architectural decisions in actual business domain knowledge, not accumulated experience alone

### Context-Aware SRP (Don't Over-Segment):
- SRP is a guideline, not a rule — apply with nuance
- If cross-cutting concerns dominate, aggregate related responsibilities into broader units
- If interdependent concerns dominate, combine classes with shared state
- If high concurrency is required, use shared resource pools and aggregated classes
- Over-segmentation isolates components, creating bottlenecks and inefficiency
- Balance modularity with system-level cohesion

### Information Hiding:
- Hide volatile knowledge behind stable boundaries
- Separate what varies for different causes; unite what varies for the same cause
- Interfaces should be stable; implementations should be replaceable
- Internal details should not leak across module boundaries

### Law of Demeter (Principle of Least Knowledge):
- Only talk to your immediate friends — don't chain method calls across object boundaries
- Reduces coupling; each unit only knows about its direct collaborators
- Avoid `a.b().c().d()` patterns — refactor to `a.doSomething()` that encapsulates the chain

### Interface Segregation Principle:
- Many specific interfaces better than one general-purpose interface
- Clients shouldn't depend on methods they don't use
- Split fat interfaces into role-specific contracts

### Dependency Inversion Principle:
- High-level modules shouldn't depend on low-level modules — both should depend on abstractions
- Abstractions shouldn't depend on details — details should depend on abstractions
- Apply when high-level and low-level modules have independent change drivers

### Module Contracts & Boundaries:
- Define clear interfaces/contracts (prop types, function signatures, API schemas) between modules
- Internals can change without breaking consumers as long as contract holds
- Use TypeScript interfaces, PropTypes, or Zod schemas to enforce contracts at compile time

### Feature Toggles for Decoupling:
- Use feature flags to decouple deployment from release
- Merge incomplete code behind flags; toggle on when ready
- Prevents long-lived feature branches and their merge conflicts

### Strangler Fig Pattern (for Legacy Code):
- Incrementally replace monolith with modular components
- New features go into new modules; old features migrate gradually
- Never do big-bang rewrites — they almost always fail

### Circular Dependency Prevention:
- Circular dependencies indicate misaligned module boundaries
- Use dependency injection or event systems to break cycles
- Lint tools can detect circular imports in CI

## User Experience & Compliance Standards

**Build user-friendly, compliant applications that respect user rights and provide intuitive interactions.**

### Rules:
- Web applications that require user information submission must include Terms of Service and Privacy Policies built around the specific context of the app
- Provide an option to delete user accounts and their data in the profile section (or somewhere accessible) to comply with data privacy regulations (GDPR, CCPA, etc.)
- Include a "Forgot Password" button and functionality in all sign-in pages
- Use subtle nudges (e.g., field shaking, highlighting) instead of popups for error feedback like required fields or terms acceptance
- Mark all required input fields with an asterisk "*" beside the label text
- Ensure all form validation provides clear, immediate feedback without disrupting user flow

## Data Privacy & Account Management

**Implement comprehensive data privacy features and account management controls.**

### Rules:
- Provide an "Export My Data" button that downloads all user data as a JSON file via API endpoint (e.g., GET /api/v1/auth/account/export) to comply with GDPR Article 20 (Right to data portability)
- Include a "Delete Account" button that opens a confirmation modal with a warning banner
- Require users to type "DELETE" in the confirmation modal to ensure intent before proceeding with account deletion
- Implement a 10-day retention period after account deletion initiation, during which user data is retained
- During the retention period, display "Yes, delete my account now" button for immediate deletion if user is certain
- Display a "Restore" button beside "Delete my account now" to allow users to cancel deletion and restore their account during the retention period
- Ensure all account deletion features are easily accessible in the profile section
- All destructive elements, buttons, and prompts must have a confirmation modal that follows the app's theme and standard, proper, and industry-standard UI/UX and design principles

## Research & Discovery

**Conduct thorough pre-implementation research and discovery before writing any code.**

### Antemortem (Pre-Implementation Reconnaissance):
- Stress-test the planned change on paper before writing code
- Enumerate hypothesized risks, classify as REAL/GHOST/NEW with file:line citations
- Revise spec BEFORE implementation begins; 15-30 minutes of recon saves days of rework
- Every trap scored on 4 axes: probability, evidence strength, blast radius, reversibility

### Spec-Driven Development:
- Write requirements before code; each phase (specify → plan → task → implement → validate) has review gates
- Acceptance criteria must be precise enough to map to tests; "fast" or "clean" are not criteria
- Non-goals are as important as goals — without them, agents expand scope by default
- Fix the spec when reality diverges; code that drifts silently from spec becomes permanent drift

### Contract-First, Code Last:
- Write the contract (what triggers it, what data it needs, what "done" looks like) before opening an editor
- Surface product questions early; wrong guesses cost review cycles, asking costs 10 seconds
- Iterate on mockups, not pull requests — rework after real implementation is not proportional to change size

### Exploration Phase (Facts Only):
- Read-only passes whose sole job is mapping what already exists
- No opinions at this stage — just facts with file references
- Every opinion formed before facts are in is a guess wearing a confident voice

### Clarification Phase (Ask, Don't Guess):
- Surface open questions from contract directly instead of assuming
- Wrong guesses cost whole review cycles; asking costs seconds
- Document clarification log with decisions and rationale

### Mockup Before Implementation:
- Use real data, real design tokens, real containers — not placeholders
- Iterate cheaply on scratch files; disagreement on mockups costs minutes, on production code costs days
- Split UX conversation from implementation — makes disagreement cheap to raise

### Decision Log:
- Record decisions and rationale for future reference
- Preserve traceability from business intent to test evidence
- Decision log is append-only; never delete, only add new entries

### Risk Assessment:
- Identify technical, product, security, privacy, operational, dependency risks
- Score each risk on impact + likelihood + mitigation
- Unknowns that could change the plan are risks too

### Acceptance Criteria (Measurable Behavior):
- Happy path, permission boundaries, invalid input, empty states, failure states
- Migration/backwards compatibility behavior
- Accessibility, analytics, logging expectations
- Each criterion maps to at least one test

### Non-Goals:
- Explicitly state what you're NOT building
- Without non-goals, scope expands by default
- Non-goals are how you say no in advance

### Evidence-Based Requirements:
- Pain mentioned once = hypothesis; pain mentioned by 3+ independent people = requirement
- Synthesize every 3-4 interviews; let opportunity map evolve
- Tag every theme with evidence (quote, interview, frequency)

### Citing Sources:
- When research informs a technical decision, cite the source (docs URL, commit SHA, file:line)
- "The code shows X" is not evidence; "line 82 of file.py calls Y" is
- Primary-source citations make findings verifiable and trustworthy

### Library Evaluation Before Adoption:
- Check: version compatibility, maintenance status (last release date), community adoption, bundle size
- Check: license compatibility, security vulnerability history, TypeScript support
- Check: breaking changes in recent versions, migration effort from current stack
- State the tradeoff (cost vs. time/maintenance) rather than defaulting to familiar

### Assumption Verification:
- Verify assumptions against official docs rather than guessing API behavior
- Run quick spikes/POCs to validate uncertain assumptions before committing
- If docs are ambiguous, test the behavior directly; don't assume

### Codebase Convention Reading:
- Read existing patterns before introducing new ones
- Match the codebase's style, naming, file organization, error handling patterns
- If you find yourself fighting conventions, that's a signal to reconsider

### Minimum Pre-Implementation Checklist:
- Problem brief and success metric approved
- Feature spec, requirements, acceptance criteria documented
- Technical plan, risk assessment, test strategy reviewed
- Tasks decomposed small enough to execute and review independently
- Rollout and rollback plan understood

### FDE Discovery (Five-Phase Validation):
- Scope: Map stakeholders, systems, and the fuzzy ask before talking to anyone in depth
- Interview: Run structured, follow-up-driven conversations with 8-10+ end users before writing production code
- Synthesize: Convert raw interview transcripts into repeated themes and ranked opportunities; a pain mentioned by 3+ independent people is a requirement
- Validate: Confirm with customer SMEs that the top opportunity is worth building and co-define what "good" looks like
- Spec: Write the requirement so precisely that a peer engineer could build it without another meeting

### Assumption Testing Discipline:
- Each assumption should be: Specific, Singular, Important, Measurable, Testable
- Define success criteria before running any test: "This assumption is confirmed if [observable result]. It is disconfirmed if [observable result]."
- Use assumption mapping: plot on importance vs. evidence grid; start with upper-right quadrant (high importance, weak evidence)
- Test multiple solution ideas in parallel to prevent confirmation bias
- Seek commitment currencies (time, reputation, money), not compliments
- Triangulate: use multiple methods to test the same assumption

### Validation Gates (RPI Framework):
- Research → Plan → Implement with explicit validation gates between each phase
- FAR scale before moving to Plan: Factual (based on actual code), Actionable (you know exactly what to build), Relevant (solves the real user need)
- FACTS scale before moving to Implement: Feasible, Atomic, Clear, Testable, Scoped
- If any gate fails, implementation pauses; do not auto-fix and proceed
- Fresh sessions per phase to avoid polluted context

### Scope Definition:
- Clear scope reduces surprises; 52% of software projects exceed budgets due to scope creep
- Include 20-30% contingency in budgets
- Document assumptions explicitly and validate them
- Define acceptance criteria for every feature before coding begins
- Get stakeholder alignment during scoping, not during development

## Prompt/Context Engineering

**Handle ambiguity with judgment: ask when the cost of a wrong guess is high, proceed with a stated assumption when it isn't.**

### Rules:
- Before asking a clarifying question, check if the answer is already inferable from the codebase, prior conversation, or existing conventions in the project; don't ask for information that's already available
- Distinguish between high-stakes ambiguity (data model changes, destructive actions, security/auth behavior, anything hard to reverse) and low-stakes ambiguity (naming, minor styling, internal variable choices) — ask for the former, proceed with a stated assumption for the latter
- When proceeding on an assumption, state it explicitly in the response (e.g., "Assuming X because Y — let me know if that's wrong") so it's visible and easy to correct
- Batch clarifying questions together rather than asking one, waiting, then asking another; minimize round-trips for the same task
- If a request could reasonably mean two different things, state both interpretations briefly and either ask which is intended or pick the more conservative one and say so
- Re-read the full instruction/task before acting; don't respond to only the first part of a multi-part request
- When context is missing that's required to proceed safely (e.g., which environment, which user role, which of several similar files), ask — don't guess and apply the change broadly
- Prefer narrow, reversible actions when uncertain (e.g., propose a change before applying it) over broad changes that assume intent
- If the user's instruction conflicts with an existing rule in this file, flag the conflict explicitly rather than silently prioritizing one over the other

### Context Engineering Fundamentals:
- Prompt engineering focuses on wording; context engineering focuses on what data the agent actually sees at inference time
- The system prompt is often a small fraction of the context window — memory, RAG results, and tool outputs dominate
- Context is the agent's operating system, not passive input: it manages memory, allocates resources, isolates processes

### Context Quality Criteria:
- Relevance: give the agent only what's necessary for the current step, no more
- Sufficiency: context must contain everything needed for a decision without guesswork
- Isolation: output of one module should not "contaminate" another
- Economy: every token costs money, time, and latency — architecture determines unit economics
- Provenance: track where each piece of context came from for debugging

### Context Rot (Four Degradation Modes):
- Context poisoning: a hallucination enters context and reproduces at every subsequent step
- Context distraction: model relies on accumulated history instead of trained knowledge (worse past 100K tokens)
- Context confusion: irrelevant information degrades response quality
- Context clash: incremental data contradicts earlier context (39% quality drop in studies)

### Lost in the Middle:
- Model performance is highest when relevant information is at the beginning or end of context
- Over 30% accuracy drop for information buried in the middle
- Put critical instructions first and last, never the middle

### Tool Set Hygiene:
- Most common failure mode: bloated tool sets that cover too much functionality or lead to ambiguous decision points
- If a human engineer can't definitively say which tool should be used, an AI agent can't either
- Right number of tools is almost always smaller than what teams ship in v1
- Each tool definition and result consumes tokens

### Memory Management:
- Don't dump entire conversation history back into context with every turn
- Use sliding window buffer that only keeps recent turns
- Summarize long threads into compact state updates
- Early interactions become irrelevant or contradict current tasks

### Token Budgets:
- Track token usage and tool-call counts per task
- Set budgets and alert when an agent class regularly exceeds them
- LLM reasoning performance starts degrading around 3,000 tokens
- Practical sweet spot for most tasks: 150-300 words

### Prompt Structure Best Practices:
- XML tags (not markdown or numbered lists) are best for structuring Claude prompts
- Positive framing beats negation: "only use real data" consistently outperforms "don't use mock data"
- Skip explicit "think step by step" for reasoning models (o-series, Claude Extended Thinking) — they already do it internally
- Few-shot prompting (3-5 examples) remains highest-ROI technique

### Model-Specific Behavior:
- GPT-5 is router-based — "think hard" literally triggers reasoning model
- Gemini prefers shorter, more direct prompts; always include few-shot examples (zero-shot is explicitly not preferred)
- Pin production apps to specific model snapshots to avoid router behavior changes

### Version Control & Testing:
- Version control your prompts — prompt drift is real
- Build a golden test set: representative inputs with expected outputs
- Run test set on every prompt change (regression testing for instructions)
- Audit longest prompts — anything over 300 words should be questioned

### Caching-Friendly Structure:
- Place static content first (system instructions, few-shot examples, tool definitions)
- Variable content last (user messages, query-specific data)
- With prompt caching, this can cut costs by 90% and latency by 85%

### Four-Level Pyramid Maturity Model:
- Level 1: Prompt Engineering (crafting queries)
- Level 2: Context Engineering (information environment)
- Level 3: Intent Engineering (organizational goals, values, trade-off hierarchies)
- Level 4: Specification Engineering (machine-readable corporate policies, quality standards)
- Each level subsumes the previous as necessary foundation

### Context Governance:
- Every context file needs a named owner accountable for accuracy
- Establish review cadence (monthly for active codebases, quarterly for mature)
- Three review questions: Is each section accurate? Is it still necessary? Is it discoverable?

## Definition of Done

**A feature or fix is not "complete" until it passes every relevant check below — this is the final gate before something is called done.**

### Checklist:
- [ ] Code implements the full requirement, not a partial version, and matches the confirmed interpretation of the request
- [ ] Tests written and passing (unit, integration, and/or e2e as applicable) — see Testing Strategy
- [ ] All CI checks pass: lint, format, build, tests — see CI/CD Compliance
- [ ] No new security issues introduced (input validation, auth checks, no secrets committed) — see Security
- [ ] Error handling in place for expected failure cases, with user-facing messages that make sense — see Error Handling & Logging
- [ ] Accessibility basics verified for any new UI (keyboard nav, labels, contrast) — see Accessibility
- [ ] Responsive/works across target viewports for any new UI — see Design Principles
- [ ] Documentation updated (README, API docs, changelog) if the change affects setup, usage, or public behavior — see Documentation Standards
- [ ] No unresolved TODOs or commented-out code left in without explanation
- [ ] Self-reviewed the diff end-to-end before flagging as ready (see Code Review Checklist)
- [ ] Confirmed with the user on any assumption made during implementation that wasn't explicitly specified
- [ ] No unrelated changes bundled in (scope creep) — refactors and unrelated fixes go in separate PRs (see Refactoring Policy)

### Three Levels of DoD:
- Story level: code complete, tests pass, reviewed, merged, docs updated, acceptance criteria met
- Sprint level: all stories meet story DoD, sprint goal achieved, increment is releasable, no critical bugs
- Release level: all sprint DoDs met, release testing passed, performance validated, security reviewed, release notes written

### Observable Checks:
- Every DoD line should pass two tests: can a teammate verify it in under 2 minutes? Would two different people reach the same yes or no?
- "High quality" and "code reviewed" are not DoD criteria; "code merged with at least one approving review and no unresolved 'must fix' comments" is

### Risk Buckets (Keep DoD Tight):
- Functional correctness (tests, acceptance validation)
- Operational readiness (logging, alerts, runbooks)
- Security and compliance (threat checks, dependency review)
- Maintainability (code review, refactor boundaries, documentation)
- Write DoD criteria that close the biggest, most frequent gaps first

### DoD Extensions by Class of Work:
- Maintain a single team DoD for every backlog item
- Add short extensions for specific categories (e.g., "Schema change": migration reviewed, backward compatibility confirmed, rollback tested; "Auth change": security review completed, audit logging verified)
- Short extensions keep you honest without turning every item into paperwork

### Enforceability:
- Add checklist to Jira issue template so every ticket carries DoD reminders
- Encode gates in CI so "tests pass" isn't a conversation, it's a requirement
- Add lightweight PR template in GitHub/GitLab that prompts for test evidence and rollout notes
- In Sprint Review, explicitly call out any item that didn't meet DoD and treat it as not done
- "If it doesn't meet DoD, it doesn't count toward sprint completion"

### Two-Sprint Trial:
- Pick one metric that reflects "staying done": count how many items move out of Done after the sprint ends
- After two sprints, revise the DoD based on evidence, not vibes

### Aspirational Items:
- Mark aspirational items separately and create a plan to close the gap
- Example: if team doesn't have integration tests yet, add "integration tests" as aspirational and commit to building test infrastructure over next two sprints
- Use RICE framework to prioritize which gaps to close first

### Documentation Triggers (Not All-or-Nothing):
- If you changed a public API, update API reference and add example call
- If on-call will troubleshoot it, update runbook with symptoms and first checks
- If UI changed, update help text or internal support notes
- Both "write comprehensive docs" and "we'll document later" fail

### Non-Functional Requirements:
- Performance, accessibility, and observability are classic "later" items that become never
- Anchor DoD language to standards like WCAG from W3C to reduce opinion fights
- Include accessibility verification for any new UI (keyboard nav, labels, contrast)

### Creating DoD Process (45 min):
- List top 10 reasons items aren't truly shippable at Sprint Review
- Circle the top 3 that cost most time or customer trust
- Write 6-12 DoD lines that prevent those failures in observable terms
- Decide what evidence counts: CI run link, screenshot, log query, PR checklist

## Code Review Checklist

**Before flagging any work as ready for the user, do a self-review pass as if reviewing someone else's PR — catch issues before they're surfaced.**

### Rules:
- Re-read the full diff top to bottom before declaring the task complete; don't rely on memory of what was written
- Check that the change does exactly what was asked, nothing more (no unrelated files touched) and nothing less (no partial implementation left silently incomplete)
- Verify naming is clear and consistent with the rest of the codebase (see Development Standards)
- Check for leftover debug code: `console.log`, commented-out blocks, temporary test values, unused imports/variables
- Confirm no secrets, API keys, or credentials were introduced anywhere in the diff, including test files and config
- Check error paths, not just the happy path: what happens on empty input, network failure, unauthorized access, unexpected types
- Verify existing tests still pass and new tests were added for the new logic (see Testing Strategy)
- Check for duplicated logic that should instead reuse an existing utility/component (see Modularity)
- Confirm the change doesn't silently break an existing feature or API contract elsewhere in the codebase
- Check that any new dependency, config, or environment variable is documented (see Documentation Standards, Environment & Setup)
- Read error messages and UI copy for clarity and tone, not just correctness
- If something feels uncertain or was a judgment call during implementation, flag it explicitly in the summary rather than staying silent about it

### PR Size Limits:
- Keep PRs under 200-400 lines; past 400 lines, defect detection drops sharply and reviewers skim
- If a feature can't be done in under 400 lines, split into stacked PRs (schema migration → endpoint → UI)
- Encode the ceiling in CI: warn above 400 lines, block above 800 with manual override

### Review Rubric (Priority Order):
- Correctness: Does the code do what the ticket says? Edge cases? Load handling?
- Clarity: Will the engineer who touches this in 6 months understand it?
- Performance: Quadratic loops? N+1 queries? Unnecessary allocations?
- Style: Cosmetic preferences; automate with linters, never block PRs for this

### Human-Only Review Zone:
- Security boundaries (auth flows, crypto, RBAC, tenant isolation) — AI catches obvious holes, humans catch subtle ones
- Business logic correctness — AI can verify tests pass, not that "calculate invoice" matches the contract
- Novel architecture — AI is weakest where you're doing something new; route to senior engineer
- Label these PRs `needs-human-review` or `security-sensitive`

### Comment Prefixes (Reduce Friction):
- `nit:` — minor, optional, won't block
- `suggestion:` — consider this, but not required
- `question:` — need clarification before proceeding
- `blocker:` — must fix before merge
- This single convention removes ~30% of review friction

### Explain the WHY, Not Just the WHAT:
- Instead of "use Map here," say "use Map here so the lookup stays O(1) when customer list grows past 1,000"
- Reviewer's job is to teach the next reviewer; one-line directives don't teach

### Self-Review Before Requesting:
- Authors should review their own diff before requesting review — catches obvious issues (debug logs, TODO comments, missing tests)
- Shows respect for reviewer's time
- Self-review should never count as the required approval

### Automate Style Checks:
- Run linters and formatters in CI as a gate before any PR reaches a human
- If you can define a style rule clearly, enforce it automatically so it never comes up in review
- Style nits should never block a PR in 2026

### 24-hour Review SLA:
- First reply (question, comment, request for changes, or approval) within 24 hours
- Not "approve in 24 hours" — first response
- Track metrics: p50 time to first review under 24h, p90 under 48h

### Production Hardening Checks:
- Resource management: database connections, file handles properly closed/released, even in failure paths
- Concurrency safety: shared state synchronized correctly, no deadlocks/race conditions
- Observability: metrics, tracing spans, health check endpoints
- Configuration: no hardcoded secrets, proper secrets management

### Anti-Patterns to Avoid:
- Reviewing only the code, not the tests
- Approving based on trust without reading the diff
- Letting PRs sit for weeks without review
- Rubber-stamping changes from senior developers
- Reviews longer than 30 minutes (sign of too-large PR)

## Refactoring Policy

**Keep refactoring intentional and separate from feature work, so improvements don't introduce risk or obscure what actually changed.**

### Rules:
- Do not refactor unrelated code while implementing a feature or fix; if a problem is spotted outside the scope of the current task, flag it and propose a separate follow-up rather than fixing it inline
- Keep refactoring PRs separate from feature/bug-fix PRs so each can be reviewed and reverted independently
- Before refactoring, confirm the current behavior is covered by tests; add tests first if coverage is missing, so the refactor can be verified as behavior-preserving
- State the reason for a refactor explicitly (e.g., "extracting this into a shared utility because it's duplicated in 3 places") rather than refactoring based on preference alone
- Avoid large, sweeping refactors in a single change; prefer small, incremental refactors that are each easy to review and revert
- Never refactor code purely for stylistic preference (e.g., rewriting working code to a "nicer" pattern) without a stated functional or maintainability reason
- When refactoring touches a widely-used shared module/utility, flag the blast radius (what else depends on it) before proceeding
- If a refactor changes a public interface (function signature, API contract, exported component props), treat it as a breaking change and follow Versioning & Changelog rules
- Run the full test suite after any refactor, not just tests directly related to the changed files, to catch unintended side effects

### Three Levels of Refactoring:
- Micro-refactoring (daily, minutes): rename, extract method, simplify conditionals, remove duplication near the change
- Local refactoring (hours-days): split god class, replace leaky abstractions, introduce interfaces, reduce coupling
- Structural refactoring (weeks): redefine boundaries, migrate data models, strangle legacy behind anti-corruption layer
- Most teams get outsized results by making micro + local routine, then treating structural as staged operational work

### Refactoring Triggers (When to Refactor):
- A feature is hard to add because the code resists modification
- The same module becomes a repeated hotspot (high churn)
- Bugs and incidents cluster around the same region
- New engineers struggle to predict behavior
- Dependency upgrades are disproportionately painful
- Refactor when change is already happening — invest in safety first

### Safety Stack (Every Refactor):
- Contracts: APIs, events, schemas must not change
- Tests: unit + contract/integration at boundaries
- Telemetry: logs, metrics, traces tied to invariants
- Rollback controls: feature flags, canary, reversible migrations

### AI-Assisted Refactoring Guardrails:
- Allowed: rename/extract/simplify within code you're already changing, tighten boundaries, propose small steps with checkpoints, generate tests
- Not allowed without approval: large rewrites across modules, boundary changes without migration plan, silent behavior changes hidden in refactor PRs, changes to security/auth/payment logic
- Required safety checks: tests added/strengthened, CI green + contract tests, telemetry impact considered, rollback strategy identified

### Operating Rhythm:
- Daily (10-20 min): make one micro-refactor in code you touched
- Weekly (60-90 min): select one hotspot, add characterization tests, execute 1-2 safe steps
- Monthly (staged): for structural refactors, define success metrics, run in parallel, cut over gradually

### Four Preconditions for AI Refactoring:
- Tests cover the area (run suite green, capture baseline)
- Scope is one concern (write goal in one sentence; if you can't, split the task)
- Clean working tree (git status clean, fresh commit)
- You review every diff (budget review time as part of the task)

### When NOT to Refactor:
- Code is stable, well-tested, not causing performance or maintenance issues
- Right before major releases
- During production incidents
- When cost of refactoring outweighs benefits
- When deadlines are extremely tight
- Building temporary prototypes or throwaway code

## Rollback & Incident Response

**When something breaks in production, prioritize restoring service quickly and safely over diagnosing the root cause immediately.**

### Rules:
- If a deployment is suspected of causing a production incident, roll back first, investigate the root cause after service is restored
- Never attempt to "hot fix" a production incident directly by editing code/config live in production; roll back to the last known-good state instead
- Have a documented, one-command (or one-click) rollback path for every deployment pipeline, tested before it's actually needed (see Deployment & Environments)
- On detecting an incident, immediately assess severity/blast radius (how many users affected, is data at risk) before deciding next steps
- Communicate incident status clearly and immediately when user-facing impact is confirmed, even before the root cause is known
- Preserve logs, error traces, and system state from the time of the incident before rolling back or restarting services, so root cause analysis is still possible afterward
- After service is restored, conduct a root cause analysis and write a brief postmortem: what happened, why, and what change prevents recurrence
- Any fix resulting from an incident must include a regression test that would have caught the issue (see Testing Strategy)
- Never silently patch an incident without documenting it; every production incident gets a record, however minor
- If the incident involves a security issue (data exposure, auth bypass), treat it under Security's incident rules first: contain, assess exposure, then follow standard rollback/postmortem steps
- Avoid making unrelated changes while resolving an active incident; keep the fix minimal and scoped to restoring service

### First 30 Minutes of Incident:
- Freeze: Don't immediately restart, redeploy, or scale — preserve evidence first
- Assess Blast Radius: Which services affected? Every customer? Is data at risk? Is failure still spreading?
- Stop the Bleeding: Pause bad rollout, stop workers consuming bad messages, suspend autoscaling
- Choose Recovery Strategy: Different failures need different responses (bad deploy → rollback, bad config → restore, data corruption → stop writes then restore)
- Recover One Layer at a Time: Don't restart, revert, and change DB simultaneously — you won't know what fixed it
- Validate as a User: Health endpoints may return 200 while login is broken; test actual user flows

### Rollback Triggers (Specific Thresholds):
- Error rate: rollback if 5xx rate exceeds baseline by 3× for 10 consecutive minutes
- Latency: rollback if p95 latency exceeds 2× baseline for 15 minutes
- Business metric: rollback if conversion rate drops by more than 15% vs same-day-last-week
- Data integrity: rollback immediately on any inconsistency detected by invariant checker
- Vague stop-loss ("if something looks bad") gets overridden at 3am by whoever wants to go to bed

### Incident Commander (IC) Role:
- Assign IC immediately on incident declaration
- IC manages resources, drives communication, makes decisions
- IC is responsible for all aspects of response, not just technical
- Name a backup IC in case primary is unavailable

### Mitigation vs Resolution:
- Mitigation = restore service (rollback, reroute, disable feature)
- Resolution = permanently fix root cause
- During active incident, prioritize mitigation every time
- Spending 45 minutes finding root cause while users are impacted is wrong order of operations
- If you can restore 90% of service in 5 minutes by rolling back, do that first

### Rollback Runbook (Must Be Testable):
- Document step-by-step procedure with estimated times
- Answer without interpretation: How to check if release is working? What does "healthy" look like? First step if not healthy? Who to page?
- Test for good runbook: can a new on-call engineer execute it at 3am without paging anyone else?
- Test rollback procedure in staging monthly; document last test date

### Database Migration Rollback:
- Expand-contract pattern: add new column alongside old, deploy code that writes to both, backfill, then remove old
- Expand migration is always safe to roll back; contract migration is deployed only after old code is gone
- If migration is forward-fix only, state that explicitly — pretending DB migration can be "rolled back" is how incidents get worse
- Before rolling back, ask: Did schema change? Did background jobs modify data? Are queued messages still compatible?

### Named Ownership:
- Every rollback needs a clear owner accountable for correctness, test coverage, deployment readiness
- Designate who can declare rollback, who executes, who approves follow-up actions
- If multiple leads must agree in real time, rollback may be delayed — give one role clear authority
- Name a backup owner in case primary is unavailable

### Postmortem Process:
- Blameless: focus on decisions that were difficult during incident, not who made mistakes
- Build from incident timeline and preserved evidence, not from memory
- Schedule within 24-72 hours of resolution, before memories fade
- Follow-up work must be concrete: improve alert, write runbook, test rollback, add feature flag
- Action items tracked in Jira with owners and due dates

## Multi-Agent Collaboration

**When multiple AI agents work on the same repository, prevent conflicting, overlapping, or overwritten work.**

### Rules:
- Before starting work, check for other in-progress branches/PRs that might touch the same files or feature area, to avoid duplicate or conflicting effort
- Each agent works on a dedicated feature branch scoped to a single task; never have multiple agents committing to the same branch simultaneously
- Keep tasks assigned to agents narrow and well-scoped so overlap between agents' work is minimal by design
- If two agents' changes are likely to conflict (same files, same module), sequence the work explicitly rather than running both in parallel
- Before merging, check whether another agent's recent merge has changed shared files/interfaces this work depends on; rebase/resolve rather than assuming the base branch is unchanged
- Never force-push over another agent's branch or commits; resolve conflicts through standard merge/rebase workflows
- If an agent modifies a shared utility, config, or interface that other in-progress work depends on, flag it so dependent work can be updated rather than silently breaking
- Log or summarize what each agent did in PR descriptions clearly enough that another agent (or human) picking up related work later has full context
- When uncertain whether another agent is currently working on the same area, ask/check rather than assuming exclusive ownership of the codebase
- Maintain a single shared source of truth for project conventions (this file) so agents don't diverge into inconsistent patterns over time

### Git Worktree Isolation:
- Each agent gets its own complete checkout of the repo, on its own branch, in its own directory
- They share the same `.git` database but never interfere with each other's working tree
- Conflicts only surface at merge time — where they're cheap to resolve because each branch is small and well-scoped
- Never let two agents edit the same branch

### Atomic Task Claiming:
- Prevent two agents from grabbing the same task simultaneously
- Use a task board with atomic claiming — agent claims task in single operation that blocks others
- SQLite-backed kanban board, Redis/Postgres advisory locks, or file-lock-based claiming

### Coordinator/Specialist/Verifier Roles:
- Coordinator: performs task decomposition, dependency ordering, delegation, progress tracking — does not write code
- Specialist: executes bounded tasks with single responsibility per task — should not silently expand scope
- Verifier: validates output before it reaches humans — requires execution evidence, not just static analysis

### Sequential Merges:
- Don't merge all branches at once — go one at a time, run tests after each merge, fix conflicts before proceeding
- Each subsequent branch rebases onto newest main, reducing surprise conflicts late in sequence
- Only rebase before sharing branches publicly (rebasing rewrites history)

### Spec-Scoped Tasks:
- Convert large change into small tasks with explicit file and interface boundaries
- Specifications should include parameters, constraints, and acceptance criteria to prevent agents from overstepping
- For each pair of tasks, ask: can agent A finish without knowing what agent B did? If no, restructure or sequence

### Quality Gates (Mandatory Before Merge):
- Automated tests: CI runs unit/integration tests plus linting and security scanning
- Quality gates: enforce coverage and critical rule thresholds before merge
- AI review stages: run code-review and bug-finding passes as separate steps
- Human checkpoints: reserve humans for semantic correctness and architecture

### Single-Writer Rule for Hotspot Files:
- Routes, configs, registries, `index.ts` — files that many tasks touch
- Assign one agent per hotspot file; other tasks that need it become prerequisites
- Good decomposition eliminates 90% of conflicts before they happen

### Task Size Guidelines:
- 15-45 minutes per task — under 15, overhead of separate agent isn't worth it; over 45, decompose further
- 5-6 tasks per teammate is the sweet spot — too small and coordination overhead dominates; too large and agents work too long without check-ins

### Dependency-Aware Task Plans:
- Manager constructs dependency graph (DAG) of subtasks with explicit dependencies
- Independent subtasks run in parallel; dependent ones wait
- Prerequisite tasks (schema, interface, config) run alone first; everything else launches after completion

### Human Review Before Merge:
- No agent output should merge to `main` without human review
- Automated CI gates (tests, lint, type check) are necessary but not sufficient
- Semantic errors can pass compilation, linting, and even basic tests but fail in production

### Secrets Isolation:
- Use hooks or tool permissions to prevent agents from reading `.env` files, credentials, or secret stores
- Agents that don't need network access shouldn't have it — block outbound requests except to approved domains

## Dependency Update Policy

**Keep dependencies current and secure without introducing instability from unmanaged or surprise upgrades.**

### Rules:
- Run automated dependency vulnerability scanning regularly (Dependabot, npm audit, pip-audit) and address flagged vulnerabilities promptly, prioritized by severity
- Apply patch-level updates (bug fixes, security patches) routinely; these should not require extensive discussion
- Treat minor version updates as low-risk but still worth a quick changelog check for deprecations before merging
- Treat major version updates as requiring explicit review: read the migration guide/changelog, assess breaking changes, and test thoroughly before adopting — never bump a major version silently as part of an unrelated change
- Update dependencies in their own dedicated PR, separate from feature work, so any regression is easy to isolate and revert
- Never update a dependency and a feature/fix in the same commit or PR
- Pin exact versions (or use lockfiles) for production dependencies rather than relying on loose version ranges that can silently pull in breaking changes
- Before adding a new dependency, check its maintenance status (recent commits, open issues, download trends) and prefer actively maintained, widely-used packages
- Avoid adding a dependency for something trivial that can be written in a few lines; weigh the long-term maintenance cost of a dependency against the convenience it provides
- Remove unused dependencies promptly rather than leaving dead weight in the project
- Test the full suite after any dependency update, not just a smoke test, since transitive dependency changes can cause subtle breakage

### Update Classes (Treat Differently):
- Class A — Emergency security patches: fast-track, but still staged (micro-canary), with explicit rollback plan
- Class B — Routine patch/minor updates: weekly cadence, normal canary, normal gates
- Class C — Major upgrades / behavioral changes: project work with test environments, feature flags, rehearsed rollback
- Class D — "Invisible" changes: base images, OS repo refreshes, kernel updates, runtime updates — treat as B or C

### Cooldown Windows:
- Wait 3-7 days before adopting new releases — lets ecosystem vet first
- If a compromised version is published and yanked within 48 hours, cooldown means automation never saw it as eligible
- Configure security-update path that shortens or waives maturity window for urgent CVEs

### Auto-Merge Guardrails:
- Auto-merge should be structurally incapable of bypassing verification — branch protection requiring status checks, not bot settings
- Only patch and minor updates with every check green are eligible for auto-merge
- Major updates simply never reach auto-merge and wait for human
- Exclude pre-1.0 (`0.x`) packages from auto-merge — minor bumps may be breaking under semver

### Lockfile Hygiene:
- Always commit lockfiles — they make builds reproducible
- Use deterministic install commands (`npm ci`, `pip install --require-hashes`)
- Regenerate lockfiles periodically to pick up transitive dependency updates
- Diff lockfiles in code review to catch unexpected changes

### Security SLA by Severity:
- Critical CVEs: patch within 24 hours
- High severity: patch within 7 days
- Medium/Low: batch with regular update cycle
- Define clear response times, not "whenever we get to it"

### Approved Package List:
- Maintain list of pre-approved packages for common needs (HTTP clients, date handling, validation, testing)
- When developer needs library, check approved list first
- New packages go through lightweight review before adding

### New Dependency Review Process:
- Before adding, fill brief form: why needed, alternatives considered, license type, maintenance status, transitive dependency count, bundle size impact
- Takes 5 minutes, prevents impulsive additions
- Check: maintenance activity, download count, license compatibility, bundle size, transitive count, bus factor

### Supply Chain Security:
- Lockfiles with integrity hashes to detect tampering
- Enable provenance feature to verify packages built from claimed source
- Run Socket.dev or similar tools that detect suspicious package behavior (install scripts, network access)
- Pin exact versions for critical dependencies

## Feature Flags

**Decouple deployment from release: ship code dark, then turn it on deliberately and gradually.**

### Rules:
- Wrap any risky, incomplete, or user-facing behavioral change in a feature flag rather than relying on long-lived feature branches
- Default new flags to "off" in production; enable explicitly per environment, not by default on merge
- Support at least three rollout mechanisms: global on/off, percentage-based rollout, and per-user/per-segment targeting
- Name flags descriptively and consistently (e.g., `feature.checkout_v2`), and document what each flag controls and its owner
- Remove flags promptly once a feature is fully rolled out and stable; don't let stale flags accumulate as permanent if/else branches
- Never nest flag conditionals more than one or two levels deep; deeply nested flag logic is a sign the feature needs isolating into its own module
- Test both flag states (on and off) for any flagged feature, not just the "on" path
- Log flag evaluation for critical flags (which variant a user saw) to support debugging and analysis
- Kill-switch flags for critical infrastructure (e.g., disable a failing third-party integration) should be checked and toggleable without a full deployment

## Background Jobs / Queues

**Handle asynchronous work reliably: jobs must survive crashes, retries must not duplicate side effects, and queue health must be visible.**

### Rules:
- Make job handlers idempotent by design (safe to run more than once) since at-least-once delivery is the norm for most queue systems
- Define an explicit retry policy per job type: max retry count, backoff strategy (exponential preferred), and what happens after retries are exhausted
- Route permanently failing jobs to a dead-letter queue rather than retrying indefinitely or silently dropping them
- Prioritize queues/jobs explicitly (e.g., separate queues for critical vs. best-effort work) rather than a single undifferentiated queue for everything
- Monitor queue depth and processing latency; alert when a queue backs up beyond a defined threshold
- Keep job payloads small and serializable (pass IDs, not full objects) to avoid stale-data bugs when a job runs after the source data has changed
- Log job start, completion, and failure with enough context (job ID, type, relevant entity ID) to trace a specific job's lifecycle
- Set explicit timeouts per job type so a hung job doesn't block a worker indefinitely
- Ensure jobs are transactionally safe with their triggering action (e.g., use outbox pattern or enqueue-after-commit) to avoid enqueuing jobs for data that never actually saved
- Version job payload schemas when job structure changes, so in-flight jobs from before a deploy don't break on the new worker code

## Caching Strategies

**Cache deliberately: know what layer caches what, how it invalidates, and how stampedes are prevented.**

### Rules:
- Identify and document each caching layer in use (CDN, application/in-memory, distributed cache like Redis, database query cache) and what each is responsible for
- Choose a cache invalidation strategy explicitly per cache: TTL-based expiry, event-based invalidation on write, or a hybrid — don't leave it undefined
- Prefer short TTLs with background refresh over long TTLs with manual invalidation, unless the data is genuinely static
- Use cache keys that clearly encode what varies (e.g., include user ID, locale, or version in the key) to avoid serving stale or wrong data across contexts
- Prevent cache stampedes (many requests recomputing the same expired key simultaneously) using locking, request coalescing, or stale-while-revalidate patterns
- Never cache sensitive or user-specific data in a shared/public cache layer (e.g., CDN) without proper cache-control scoping
- Set explicit `Cache-Control`/`ETag` headers for HTTP responses rather than relying on default behavior
- Invalidate related cache entries together when underlying data changes (e.g., updating a user should invalidate that user's cached profile and any list caches containing them)
- Monitor cache hit/miss rates; a persistently low hit rate signals a caching strategy that isn't matching actual access patterns
- Avoid caching by default for data that changes frequently or where staleness has real user impact (e.g., account balances, live availability)

## Rate Limiting

**Protect every endpoint from abuse and overload with explicit, consistent limits communicated clearly to clients.**

### Rules:
- Apply rate limiting to every public-facing endpoint, not just auth/login; state the algorithm used (token bucket or sliding window preferred over fixed window)
- Set limits per scope appropriate to the endpoint: per-IP for unauthenticated routes, per-user/per-API-key for authenticated routes
- Use stricter limits for sensitive/expensive operations (login, password reset, search, AI/LLM calls) than for routine reads
- Return standard rate-limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`) so clients can back off appropriately
- Return HTTP 429 with a clear error body on limit exceeded, not a generic error or silent drop
- Implement backoff-aware retry logic on the client/consumer side for any internal service calling a rate-limited API
- Rate limit at the infrastructure/gateway level where possible (in addition to application level) to protect against abuse before it reaches application code
- Distinguish between burst limits (short window, higher tolerance) and sustained limits (longer window, stricter) where traffic patterns warrant it
- Log and alert on repeated rate-limit violations from the same source, as this often signals abuse, a misconfigured client, or a retry loop bug
- Avoid a single global rate limit for the entire API; tune limits per endpoint based on its cost/sensitivity

## Data Modeling

**Design schemas that are clear, queryable, and future-proof — not just technically correct.**

### Rules:
- Normalize schemas to at least 3NF by default; denormalize deliberately and only for a stated performance reason, with the tradeoff documented
- Use consistent naming conventions across all tables: singular or plural table names (pick one), `snake_case` or `camelCase` for columns (pick one), and stick to it project-wide
- Use explicit, descriptive foreign key names (e.g., `user_id` not `uid` or `owner`) so relationships are clear without checking the schema
- Choose primary key strategy deliberately (auto-increment integer, UUID, ULID) based on access patterns: UUIDs/ULIDs for distributed systems or public-facing IDs, integers for internal-only high-volume tables
- Index every foreign key and any column used in frequent WHERE/JOIN/ORDER BY/GROUP BY clauses; document the reasoning for non-obvious composite indexes
- Model timestamps consistently (`created_at`, `updated_at` on every table at minimum) and always store in UTC
- Avoid storing derived/computed data unless caching it is a deliberate performance decision with a defined invalidation path
- Use enums or lookup tables for fixed sets of values rather than free-text strings, to prevent invalid states
- Model soft-deletes (`deleted_at`) explicitly where data recovery/audit matters, and document how queries must account for them (default scopes, etc.)
- Avoid overly generic tables (e.g., a single `metadata` JSON blob replacing a proper schema) unless the data is genuinely unstructured; prefer explicit columns for anything queried or filtered on

## Service Level Objectives & Tracing

**Make system health measurable and requests traceable — don't guess when you can measure.**

### Rules:
- Define SLIs (e.g., p95 latency, error rate, availability) and SLOs (target thresholds) for critical services; alert on SLO burn rate, not just raw threshold breaches
- Implement distributed tracing (OpenTelemetry or equivalent) across services so a single request can be followed end-to-end, not just logged per-service
- Propagate a trace/correlation ID through every service, queue job, and external call in a request's lifecycle (see Error Handling & Logging for logging mechanism)
- Track error budgets against SLOs to inform how much risk (deploy frequency, experimentation) is acceptable at a given time
- Review SLOs periodically against actual usage patterns; targets set at launch often need revisiting as traffic and expectations grow

## Search

**Implement search deliberately based on scale and relevance needs, rather than defaulting to basic SQL `LIKE` queries or a full search engine regardless of fit.**

### Rules:
- Use basic database full-text search (Postgres `tsvector`, MySQL FULLTEXT) for simple, low-volume search needs; reach for a dedicated search engine (Elasticsearch, Meilisearch, Typesense, Algolia) only when relevance ranking, faceting, or scale genuinely requires it
- Define what fields are searchable and their relative weight (e.g., title matches rank higher than description matches) rather than treating all matched fields equally
- Keep the search index in sync with the source of truth explicitly (event-driven reindexing on write, or scheduled reindex) and document the sync strategy and its lag tolerance
- Support typo tolerance/fuzzy matching for user-facing search where users are typing free text, not just exact substring matches
- Paginate search results and cap maximum result set size; never return unbounded results from a search query
- Log search queries with no/low results to identify gaps in indexed content or relevance tuning needs
- Sanitize and validate search input to prevent injection (especially when building raw query strings for the search engine)
- Debounce search-as-you-type requests on the frontend to avoid overwhelming the backend with a request per keystroke
- Track search analytics (top queries, zero-result queries, click-through on results) to inform relevance tuning over time
- Test relevance with real, representative queries, not just exact-match happy paths

## Developer Experience (DX)

**Make the local development loop fast, debuggable, and welcoming to anyone (human or agent) picking up the project fresh.**

### Rules:
- Local dev environment must start with a single command (`npm run dev`, `make dev`, etc.) — no manual multi-step setup required after initial install (see Environment & Setup)
- Support hot reload/fast refresh for frontend changes; backend changes should restart or reload automatically in dev, not require manual process restarts
- Provide clear, actionable error messages in dev mode (stack traces, source maps enabled) even where production intentionally hides these details
- Include a `CONTRIBUTING.md` covering: branch naming, commit message format, PR process, and how to run tests locally
- Keep local dev dependencies (seed data, mock services) easy to reset to a known state without manual cleanup
- Ensure linting/formatting run automatically on save or via a pre-commit hook, so style issues are caught before CI rather than after
- Provide debugging configuration (e.g., VSCode `launch.json`, breakpoint-friendly setup) for common entry points, not just print/log-based debugging
- Keep build and test feedback loops fast; if a full test suite takes too long for routine iteration, provide a faster subset command for local use
- Document common troubleshooting steps for known local setup issues (port conflicts, DB connection errors) in the README
- Avoid requiring access to production or shared staging credentials for routine local development; local dev should work fully isolated

## Desktop Development (PyQt)

**Keep the UI thread responsive, separate concerns cleanly, and package the app reliably across target platforms.**

### Rules:
- Never block the main/UI thread with long-running work (network calls, file I/O, heavy computation); use `QThread`, `QRunnable`/`QThreadPool`, or `asyncio` bridges instead
- Communicate between worker threads and the UI thread using Qt signals/slots, never by directly mutating UI elements or shared state from a non-UI thread
- Keep business logic separate from UI code: widgets/views should call into service/controller classes rather than embedding data processing or API calls directly in slot methods
- Use the model/view framework (`QAbstractItemModel`, `QListView`, `QTableView`) for any list/table with more than a handful of items, rather than manually creating widgets per row
- Handle platform-specific behavior explicitly (file paths, native dialogs, keyboard shortcuts, title bar behavior) and test on all target OSes rather than assuming parity
- Package and distribute using a consistent, documented tool (PyInstaller, cx_Freeze, briefcase) with a reproducible build config checked into the repo
- Version the packaged application distinctly from the codebase version if they can diverge (e.g., build number vs. app version)
- Validate all local file operations and paths to prevent path traversal or unsafe writes, especially for user-provided file paths (see Security)
- Encrypt or protect locally stored sensitive data (`QSettings`, local DB/cache files) rather than storing it in plaintext
- Handle app updates deliberately (auto-update mechanism or clear manual update instructions); don't leave users on stale, potentially insecure versions indefinitely
- Test startup performance and memory usage on low-spec target hardware, not just the development machine

<!-- context7 -->
Use Context7 MCP to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service — even well-known ones like React, Next.js, Prisma, Express, Tailwind, Django, or Spring Boot. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Use even when you think you know the answer — your training data may not reflect recent changes. Prefer this over web search for library docs.

Do not use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Steps

1. Always start with `resolve-library-id` using the library name and what to look up in the library's documentation, unless the user provides an exact library ID in `/org/project` format
2. Pick the best match (ID format: `/org/project`) by: exact name match, description relevance, code snippet count, source reputation (High/Medium preferred), and benchmark score (higher is better). If results don't look right, try alternate names or queries (e.g., "next.js" not "nextjs", or rephrase the question). Use version-specific IDs when the user mentions a version
3. `query-docs` with the selected library ID and what to look up in the library's documentation (not single words), scoped to a single concept. If the question spans multiple distinct concepts (e.g. routing and auth and caching), make a separate `query-docs` call per concept with the same library ID, unless the question is about how the concepts interact — combined queries dilute ranking and return shallow results for each topic
4. Answer using the fetched docs
<!-- context7 -->
