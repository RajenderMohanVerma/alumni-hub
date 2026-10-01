# Tasks — Alumni Hub

> Complete work breakdown, derived from the shipped v1.0 codebase plus the remaining backlog.
> Legend: `[x]` shipped · `[~]` partial / placeholder · `[ ]` not started

---

## 0. Current Delivery Snapshot

| Metric | Value |
| --- | --- |
| App version | 1.0 (first release) |
| Status | Core features complete; production-hardening incomplete |
| Backend LOC (Python) | ~9,400 across 22 modules |
| Templates | 90 files |
| Static assets | 12 CSS, 4 JS |
| DB tables | 20 |
| DB indexes | 26 |
| Routes in `app.py` | ~100 |
| Blueprints | 4 |
| Socket.IO events | 15 inbound / 27 outbound |
| Maintenance scripts | 14 |
| Automated tests | 1 (2-line import smoke check) |

---

## 1. Phase 1 — Foundation (Complete)

### 1.1 Project Bootstrap
- [x] Flask application object with env-driven config selection (`app.py:42-44`)
- [x] Development / Production configuration classes (`config.py:20-37`)
- [x] `.env` loading via `python-dotenv` (`config.py:4`, `app.py:40`)
- [x] `requirements.txt` with pinned core versions
- [x] `Procfile` → `gunicorn app:app`
- [x] `vercel.json` build + route config
- [x] `.gitignore` covering `.env`, `node_modules`, OS junk

### 1.2 Database Layer
- [x] Connection factory with `current_app` config lookup (`db_utils.py:4`)
- [x] WAL mode, `synchronous=NORMAL`, 20 s timeout, `sqlite3.Row`
- [x] `init_db()` idempotent schema creation + migration (`app.py:298`)
- [x] `users` table with 20 columns including verification/approval/suspension flags
- [x] `student_profile`, `alumni_profile`, `faculty_profile`
- [x] `alumni_meet_registration` (23 fields)
- [x] `connection_requests` with `accepted_at`, `updated_at`, `UNIQUE(sender_id, receiver_id)`
- [x] `connections` with canonical `min/max` ordering and `UNIQUE` pair
- [x] `registration_log` audit table
- [x] `password_resets` OTP store
- [x] `user_activity` presence table
- [x] `temp_users` pending-registration store
- [x] 15 indexes declared in `init_db()`

### 1.3 Authentication
- [x] `User(UserMixin)` model with all profile fields (`app.py:238`)
- [x] `load_user()` with tolerant field access and avatar fallback (`app.py:264`)
- [x] `LoginManager` wired with `login_view = 'login'`
- [x] Registration with role-specific form validation (`app.py:874`)
- [x] Gmail-domain restriction
- [x] Duplicate-email detection and conflict resolution
- [x] 6-digit OTP generation, 2-minute expiry, temp_users staging
- [x] OTP verification → real user creation + role-specific profile insert
- [x] Approval gate (alumni/faculty) and auto-login for students
- [x] OTP resend
- [x] Login with role-based dashboard redirect
- [x] Logout with presence update
- [x] Werkzeug password hashing throughout

---

## 2. Phase 2 — Core Features (Complete)

### 2.1 Profiles
- [x] `/profile` role router
- [x] Role-specific profile view routes with access guards
- [x] Role-specific profile edit routes (owner-or-admin)
- [x] Profile photo upload with extension whitelist
- [x] Auto-creation of default faculty profile
- [x] `/profile/complete/<id>` completion wizard
- [x] `initials` Jinja filter
- [x] `normalize_profile_pic()` helper
- [x] Profile completeness meter on student dashboard
- [x] Upgrade page variants per role

### 2.2 Connection System
- [x] Send request (role-agnostic)
- [x] Duplicate / already-connected / pending guards
- [x] Mutual-request auto-connect
- [x] Accept with connection-row creation
- [x] Reject
- [x] Connection status query API
- [x] Pending request list
- [x] Full connection list (blueprint)
- [x] 5-minute resend cooldown
- [x] Email notification on request / accept / reject / mutual
- [x] Real-time Socket.IO push to receiver and admin monitor
- [x] Pending-request count on all four dashboards
- [x] Network search with role filter
- [x] WhatsApp bridge + jump routes (phone hidden from HTML)

### 2.3 Dashboards
- [x] Student dashboard — alumni, faculty, students, pending, recommendations
- [x] Alumni dashboard — profile, pending, recommendations
- [x] Faculty dashboard — profile, students, alumni, colleagues, pending
- [x] Admin dashboard — users, role counts, 5-year chart, event totals
- [x] Role guards on every dashboard

---

## 3. Phase 3 — Messaging & Real-Time (Complete)

### 3.1 Persistence
- [x] `public_messages` with `is_hidden` + `deleted_by` soft delete
- [x] `private_messages` with read receipts and per-recipient soft delete
- [x] `conversations` with last-message pointer and unread subquery
- [x] `messaging_lock` single-row global switch
- [x] `message_search_index` table created
- [x] `scripts/init_messaging_db.py` provisioning script

### 3.2 Data Access (`database/messaging_db.py`)
- [x] Lock get / set / clear / status
- [x] User suspend / unsuspend / list suspended
- [x] Send / fetch / delete / hide / unhide public messages
- [x] Send private message + conversation upsert + last-message update
- [x] Conversation message history
- [x] User conversation list with unread counts
- [x] Mark message / conversation as read
- [x] Soft delete per recipient
- [x] Unread count
- [x] Message search (public / private / both)
- [x] Conversation create / lookup
- [x] Messaging statistics

### 3.3 WebSocket Layer (`routes/websocket_routes.py`)
- [x] `connect` / `disconnect` with auth guard and presence
- [x] Room joins: `user_<id>`, `public_chat`, `admin_monitor` (admin)
- [x] Public messaging send / delete
- [x] Global lock / unlock with broadcast
- [x] Private messaging send
- [x] Mark message / conversation read
- [x] Private message delete
- [x] Public + private typing indicators
- [x] Online users list
- [x] Lock status refresh
- [x] Conversation history fetch
- [x] Error handler
- [x] `ping_timeout=60`, `ping_interval=25`, `async_mode='threading'`

### 3.4 REST Mirror (`routes/messaging_routes.py`)
- [x] Public send / list / delete
- [x] Private send / read / delete
- [x] Inbox with conversations + unread count
- [x] Conversation create + messages
- [x] Message search
- [x] Admin lock / unlock / status / statistics
- [x] Admin moderation listing
- [x] Admin suspend / unsuspend / list
- [~] `GET /api/messages/private/<conversation_id>` — placeholder response only (`routes/messaging_routes.py:201-217`)

### 3.5 UI
- [x] Public chat page with lock banner and moderation
- [x] Private chat page with typing indicator and read receipts
- [x] Admin messaging control panel
- [x] Connection-gated access to private chat

---

## 4. Phase 4 — Career Board (Complete)

- [x] `jobs` table with 40+ columns
- [x] Alumni/faculty job posting → `approval_status='pending'`
- [x] Admin posting with immediate publish
- [x] Admin approve / reject with reason
- [x] Real-time approval push to poster (`job_approval_update`)
- [x] Pending-approval queue and badge count API
- [x] Jobs Matrix with live status toggle
- [x] Add/Edit job — 11-section admin form
- [x] Company logo upload + website
- [x] Deadline-driven Open/Closed/Expired lifecycle
- [x] Active vs Previous job split in listings
- [x] Student/alumni/faculty variant listings
- [x] Skill-based job recommendation (top 5)
- [x] Job deletion

---

## 5. Phase 5 — Recommendation Engine (Complete)

### 5.1 Phase 1 — Rule-Based (`models/recommendation.py`)
- [x] Branch match +5
- [x] Skill overlap +5 per skill
- [x] Domain match +3
- [x] Passing-year proximity +4 / +2
- [x] City match +2
- [x] Mutual connections +2 each
- [x] Exclusion set (self / connected / pending)
- [x] Mutual-connection map pre-fetch (avoids N+1)
- [x] Reason string per recommendation
- [x] Top 5 by score
- [x] Job recommendation by skill intersection
- [x] `get_recommended_users()` backward-compatible wrapper

### 5.2 Phase 2 — ML Collaborative Filtering (`services/recommendation_engine.py`)
- [x] Named weight constants (5 / 4 / 3 / 2)
- [x] Interaction matrix builder across 5 sources
- [x] L2 row normalisation
- [x] `NearestNeighbors(metric='cosine', algorithm='brute')`
- [x] `n_neighbors = min(10, n-1)`
- [x] Global thread-safe model cache with 5-minute guard
- [x] Background daemon-thread training at startup inside `app_context`
- [x] Cold-start threshold (`MIN_INTERACTIONS = 2`)
- [x] Exclusion set + cross-role filter in ML results
- [x] Cosine distance → 0–100 similarity score
- [x] Hybrid merge with dedupe and score sort
- [x] Graceful `ImportError` / empty-matrix / error handling
- [x] Interaction logging (best-effort)

### 5.3 API
- [x] `GET /recommendations`
- [x] `GET /recommendations/<user_id>` (self or admin)
- [x] `POST /recommendations/retrain` (admin only)
- [x] `POST /recommendations/log`
- [x] AI badge on ML cards
- [x] One-click connect from a card

---

## 6. Phase 6 — Administration (Complete)

- [x] User list per role + "all"
- [x] Pending approval queue
- [x] Approve / reject user APIs
- [x] Verify / block user route
- [x] User deletion with cascade across 8 tables + Super Admin protection
- [x] Analytics page
- [x] Registration log with role filter + search
- [x] Registration CSV export
- [x] Role-specific user CSV export (student / alumni / faculty / all)
- [x] Full database download
- [x] Connection monitor with role filter, search and drill-down
- [x] Messaging control panel
- [x] WhatsApp broadcast link generator
- [x] WhatsApp auto-send via pywhatkit
- [x] Compose email to any user
- [x] Admin events / stats pages
- [x] Optimised dashboard queries (2 queries instead of 20+)

---

## 7. Phase 7 — UI/UX (Complete)

- [x] `base.html` master layout with SEO meta, OG, Twitter cards
- [x] Role-aware navbar with dropdowns
- [x] Smart-scroll hide/show navbar
- [x] Mobile overlay menu with profile card and staggered links
- [x] Floating navbar with pill links
- [x] Scroll progress bar + back-to-top
- [x] Particle network canvas background
- [x] Mesh gradient balls and blob animations
- [x] 3D tilt cards (Vanilla Tilt)
- [x] Scroll-triggered entrances (IntersectionObserver)
- [x] Counters with re-trigger guard
- [x] Typing / word-reveal text animation
- [x] Magnetic navbar branding
- [x] AOS footer reveals
- [x] Glassmorphic OTP screen with 120 s countdown
- [x] Toast/alert system with 5 s auto-dismiss
- [x] 13-file CSS architecture
- [x] `robots.txt` + `sitemap.xml` routes
- [x] Marquee footer + map block
- [x] Public pages: home, about, services, events, contact, FAQ, privacy, terms, report issue
- [x] Social pages: LinkedIn, Facebook, Instagram, YouTube, GitHub
- [x] Coming-soon page

---

## 8. Phase 8 — Hardening (Partial — Current Focus)

### 8.1 Security Hardening
- [x] Centralised password validation (`PASSWORD_MIN_LENGTH = 8`)
- [x] OTP never rendered to the browser — server log only
- [x] `sanitize_html()` helper available
- [x] `safe_error_message()` helper available
- [x] `@role_required()` decorator available
- [x] Upload extension whitelist + `secure_filename`
- [x] 16 MB request cap
- [x] Session cookie `Secure` + `HttpOnly` + 1 h lifetime
- [x] Private chat gated on accepted connection
- [x] SQL parameterisation everywhere
- [x] Super Admin deletion protection
- [ ] Remove hard-coded `MAIL_PASSWORD` fallback from `app.py:50`
- [ ] Remove the plaintext mail password from `README.md` §4
- [ ] Force Super Admin password rotation on first login
- [ ] Fail fast when `SECRET_KEY` is still the dev default in production
- [ ] Add rate limiting to `/login`, `/verify-otp`, `/resend-otp`, `/forgot-password`
- [ ] Restrict `cors_allowed_origins` from `"*"` to configured origins
- [ ] Add CSRF protection on all POST forms
- [ ] Strip OTPs from logs in production mode

### 8.2 Connection-Leak Fixes
- [x] `try/finally` + `close()` on `load_user`
- [x] Same on `private_chat`, `alumni_jobs`, `admin_jobs`, `admin_toggle_job`, `admin_delete_job`
- [x] Same on `upgrade`, `whatsapp_bridge`, `whatsapp_jump`, `compose_email`, `send_user_email`
- [x] Same on all connection-request endpoints
- [x] Same across all remaining route handlers (62 call sites)
- [ ] Audit `routes/connection_routes.py` — several early `return` paths call `conn.close()` inline instead of using `finally`

### 8.3 Performance
- [x] Admin dashboard: 20+ COUNTs → 2 `GROUP BY` queries
- [x] `get_role_counts()` single query
- [x] `get_yearly_stats()` single query
- [x] `get_admin_job_stats()` single query
- [x] 15 indexes added in `init_db()`
- [x] `scripts/optimize_db.py` for ad-hoc indexing
- [x] `SELECT *` → `SELECT 1` for existence checks
- [x] ML model cached in memory, trained once
- [x] Lazy import of pywhatkit and scikit-learn
- [ ] Remove duplicate indexes (`idx_connections_u1/u2` vs `idx_connections_user1/user2`; `idx_connreq_*` vs `idx_connection_requests_*`)
- [ ] Add composite index on `jobs(approval_status, is_active, deadline)`
- [ ] Add index on `connections(user_id_1, user_id_2)` as a composite to serve both-direction lookups
- [ ] Paginate the user directory queries (currently `LIMIT 50` hard cap)

### 8.4 Deployment
- [x] `Procfile` for Gunicorn
- [x] Module-level bootstrap so Gunicorn works
- [x] `vercel.json`
- [x] `robots.txt` / `sitemap.xml`
- [x] Idempotent migration on every boot
- [ ] Wire a PostgreSQL driver into `get_db_connection()` (config expects `DATABASE_URL`, code only opens SQLite)
- [ ] Move uploads to object storage for serverless
- [ ] Add Redis message queue for multi-worker Socket.IO
- [ ] Add a health-check endpoint for the host
- [ ] Update sitemap domain when deploying elsewhere

### 8.5 Code Quality
- [x] Modular `utils/` extraction
- [x] Modular `services/` extraction
- [x] Structured `logging` introduced
- [x] 26+ bug fixes applied (constructor args, `False` vs `false`, template paths, faculty OTP redirect)
- [ ] Convert remaining ~60 `print()` calls to `logger`
- [ ] Split `app.py` (4,875 lines) into `routes/` blueprints
- [ ] Unify the two DB connection factories onto one file
- [ ] Adopt `utils/db.get_db()` (or delete it)
- [ ] Collapse duplicate connection-request implementations
- [ ] Collapse duplicate root-level vs role templates
- [ ] Fix `url_for('faculty_dashboard')` → `dashboard_faculty` (`app.py:4616`)
- [ ] Implement or delete `get_private_msgs` placeholder
- [ ] Implement or drop the `message_search_index` table
- [ ] Reconcile `scripts/init_db.py` schema with the live schema (`connections.user1_id` vs `user_id_1`)
- [ ] Stop tracking `data/college_pro.db` (contains 10 real accounts) and uploaded images in git

---

## 9. Phase 9 — Testing (Not Started — Highest Priority Gap)

- [ ] Set up `pytest` + `app.test_client()` fixture
- [ ] Auth tests: register → OTP → login for all four roles
- [ ] Authorisation tests: student blocked from `/admin/*`, alumni blocked from `/mentorship`
- [ ] Connection lifecycle test: send → accept → connection row → chat unlocked
- [ ] Mutual-request auto-connect test
- [ ] Recommendation cold-start test (user with 0 interactions)
- [ ] Hybrid merge test (ML + rule dedupe)
- [ ] Messaging lock/unlock test (public send blocked while locked)
- [ ] Suspension test (suspended user cannot log in or send messages)
- [ ] OTP-leak test (assert the code never appears in any response body)
- [ ] Job approval workflow test (alumni post → pending → admin approve → visible to student)
- [ ] File-upload rejection test (`.php`, `.exe` rejected; 17 MB rejected)
- [ ] Password-policy tests across register / reset / change
- [x] Import smoke check (`test_import.py`)
- [x] Recommendation manual script (`scripts/test_recommendations.py`)

---

## 10. Phase 10 — ML Advancement (Backlog)

- [ ] Weighted ensemble: `α × ML_score + (1−α) × rule_score`
- [ ] Matrix factorization (SVD / ALS) for implicit feedback at scale
- [ ] Graph Neural Network embeddings on the connection graph
- [ ] Incremental retraining on new interaction events
- [ ] Scheduled model refresh (APScheduler job)
- [ ] A/B testing harness comparing rule-only / ML-only / hybrid
- [ ] Content-based signal: TF-IDF / embeddings over `skills` + `bio`
- [ ] Semantic job matching: student bio ↔ job description embeddings
- [ ] Exploration / exploitation via contextual bandits
- [ ] Recommendation feedback loop (explicit like/dislike)
- [ ] Offline evaluation harness (precision@k, recall@k, NDCG)
- [ ] Popularity fallback when similarity is degenerate
- [ ] Diversity re-ranking (avoid returning five people from one company)

---

## 11. Phase 11 — Product Expansion (Backlog)

- [ ] Mentorship request workflow (request → accept → session slots → feedback)
- [ ] Event management by admin (create / edit / RSVP / capacity)
- [ ] Announcements CRUD with targeting by role
- [ ] Post / comment / like feed (tables referenced defensively in `app.py:3027` but never created)
- [ ] Follower graph separate from connections
- [ ] Groups / communities by department or batch
- [ ] Direct messaging attachments
- [ ] Message search powered by SQLite FTS5 instead of `LIKE`
- [ ] Notification centre with persisted read state
- [ ] Push notifications (Web Push / FCM)
- [ ] Mobile-responsive PWA with offline shell
- [ ] Dark mode (complete the existing `nav-dark-mode` hook or remove it)
- [ ] Multi-language support (i18n)
- [ ] Accessibility audit to WCAG 2.1 AA
- [ ] Two-factor authentication
- [ ] Admin action audit log
- [ ] Rate-limited public API with API keys

---

## 12. Maintenance Scripts Inventory

| Script | Purpose | Status |
| --- | --- | --- |
| `scripts/init_db.py` | Drop + recreate base schema, seed admin | ⚠️ Schema is stale vs live DB |
| `scripts/init_messaging_db.py` | Create messaging tables + lock row | Current |
| `scripts/init_postgres.py` | Provision PostgreSQL schema (Neon/Supabase) | ⚠️ No runtime driver consumes it |
| `scripts/migrate_db.py` | Add 7 `users` columns, backfill from profile tables | Current |
| `scripts/migrate_jobs.py` | Initial jobs migration | Current |
| `scripts/migrate_jobs_v2.py` | Add 18 jobs columns across both DB files | Current |
| `scripts/migrate_connection_monitoring.py` | Add connection-monitor support columns | Current |
| `scripts/fix_connections_table.py` | Rebuild `connections` to `user_id_1/user_id_2` | Current |
| `scripts/create_reset_table.py` | Create `password_resets` | Current |
| `scripts/optimize_db.py` | Add indexes | ⚠️ Creates duplicates |
| `scripts/rebrand_templates.py` | Bulk template string replacement | Utility |
| `scripts/check_categories.py` | Inspect job categories | Debug |
| `scripts/check_db.py` / `scripts/debug_db.py` | DB inspection | Debug |
| `scripts/test_email.py` | SMTP connectivity test | Utility |
| `scripts/test_recommendations.py` | Manual recommendation check | Utility |

**Recommendation:** the app's own `init_db()` already performs every migration idempotently at boot. Most `migrate_*.py` scripts are now redundant and should be archived, with `init_db()` documented as the single source of truth.

---

## 13. Prioritised Backlog

### P0 — Blocking any real deployment
1. Remove hard-coded mail credentials; rotate the app password
2. Rotate / force-change the Super Admin password
3. Fix the `faculty_dashboard` BuildError on the faculty job-post path
4. Unify the two DB connection factories onto one file
5. Remove real user data (`data/college_pro.db`) and uploaded images from version control
6. Verify no OTP or password reaches a response body or a production log

### P1 — Correctness and stability
7. Add the pytest suite (Section 9)
8. Implement `GET /api/messages/private/<conversation_id>`
9. Add CSRF protection
10. Add rate limiting on auth endpoints
11. Reconcile `scripts/init_db.py` with the live schema
12. Add composite indexes and remove duplicates
13. Restrict CORS origins

### P2 — Maintainability
14. Split `app.py` into blueprints by domain
15. Collapse duplicate connection-request implementations
16. Collapse duplicate templates into shared partials
17. Convert remaining `print()` to `logger`
18. Adopt `@role_required()` consistently
19. Archive redundant migration scripts

### P3 — Scale and intelligence
20. PostgreSQL driver in `get_db_connection()`
21. Redis message queue + shared presence store
22. Object storage for uploads
23. Weighted ensemble hybrid scoring
24. Scheduled model retraining
25. Matrix factorization / GNN embeddings

### P4 — Product depth
26. Mentorship workflow
27. Event management
28. Announcement targeting
29. Social feed
30. Dark mode
31. Accessibility audit
32. PWA / push notifications

---

## 14. Effort Reference

| Item | Estimate |
|---|---|
| P0 set (6 items) | 2–3 days |
| Test suite (Section 9, 13 cases) | 4–6 days |
| Split `app.py` into blueprints | 5–7 days |
| Template deduplication | 3–4 days |
| PostgreSQL migration | 4–6 days |
| Redis + multi-worker Socket.IO | 3–4 days |
| Weighted ensemble + evaluation harness | 5–7 days |
| Mentorship workflow end-to-end | 6–8 days |
| Accessibility audit + remediation | 4–5 days |