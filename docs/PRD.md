# PRD — Alumni Hub (Product Requirements Document)

> **Project:** Alumni Hub — Alumni Connection Network
> **Type:** Academic / Major Project (MCA)
> **Version:** 5.0 · **Status:** Production Ready (per README) · **Last Updated:** June 2026
> **Codebase analysed:** `app.py` (4,875 lines), `routes/`, `services/`, `models/`, `database/`, `utils/`, `templates/`, `static/`, `scripts/`

---

## 1. Product Overview

Alumni Hub is a web platform that reconnects a college community (built for the DBIT / JIMS alumni community) by bringing **students, alumni, faculty and administrators** into one unified system.

The product solves four real problems:

| Problem | Product Answer |
| --- | --- |
| Alumni lose touch with the institution after graduating | Persistent searchable directory with role-specific profiles |
| Students have no access to alumni career knowledge | Instagram-style connection requests + mentorship + job board |
| Placement cells manage opportunities over email/notice boards | Full job lifecycle (post → admin approve → student apply) with 30+ metadata fields |
| Admins have no visibility of community activity | Live dashboard, analytics charts, registration logs, CSV/DB export, connection monitor |

### 1.1 Product Vision
*"Connecting Generations — Building Connections, Creating Opportunities."*

### 1.2 Tagline
**ALUMNI HUB — Building Connections, Creating Opportunities**

---

## 2. Users & Roles

The entire application is built around a single `users.role` discriminator (`app.py` `init_db()`), which drives navigation, dashboard routing, template selection and access control.

| Role | Primary Goal | Key Screens | Implemented In |
| --- | --- | --- | --- |
| **Guest** (unauthenticated) | Discover the platform | Home, About, Services, Events, Contact, FAQ, Privacy, Terms, Report Issue | `templates/common/*` |
| **Student** | Find mentors, jobs and peers | Student dashboard, Network, Messages, Mentorship, Jobs, Events, Notifications, Settings, Upgrade | `templates/student/*`, `app.py:1418 dashboard_student` |
| **Alumni** | Give back — mentor, post jobs, network | Alumni dashboard, Network, Mentorship, Spotlight, Post Job, Jobs, Events, Messages, Notifications, Settings, Alumni Meet registration | `templates/alumni/*`, `app.py:1490 dashboard_alumni` |
| **Faculty** | Guide students, academic guidance, post jobs | Faculty dashboard, My Profile, Students directory, Alumni directory, Colleagues, Announcements, Reports, Post Job, Events, Messages | `templates/faculty/*`, `app.py:1525 dashboard_faculty` |
| **Admin** | Govern the platform | Admin dashboard, User management (all/student/alumni/faculty), Approve requests, Jobs Matrix, WhatsApp Broadcast, Messaging Control, Connection Monitor, Analytics, Registration Logs, CSV/DB export | `templates/admin/*`, `app.py:1608 dashboard_admin` |

### 2.1 Role Lifecycle

```
Register (role chosen) → temp_users + OTP → Verify OTP
      ├── student  → is_approved = 1  → auto-login → /student/dashboard
      ├── alumni   → is_approved = 0  → wait for admin → /login (pending msg)
      ├── faculty  → is_approved = 0  → wait for admin → /login (pending msg)
      └── admin    → never self-registers (seeded in init_db)

Student ──POST /student/upgrade-to-alumni──► Alumni (role flipped + alumni_profile created)
```

**Sources:** `app.py:874 register()`, `app.py:1067 verify_otp()`, `app.py:3596 upgrade_to_alumni()`, `app.py:574` admin seeding.

---

## 3. Functional Requirements

### 3.1 Authentication & Account Security

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-A1 | Email + password login with role-based redirect | `app.py:813 login()` |
| FR-A2 | Registration restricted to `@gmail.com` addresses | `app.py:891` |
| FR-A3 | Password minimum 8 characters, centralised validation | `utils/helpers.py:199 validate_password()`, used in `app.py:2460`, `app.py:2502` |
| FR-A4 | Passwords stored as salted Werkzeug hashes | `generate_password_hash` / `check_password_hash` |
| FR-A5 | Email OTP verification (6 digits, 2-minute expiry) for new signups | `app.py:962`, `app.py:987`, `app.py:1086` |
| FR-A6 | OTP resend with new code + expiry | `app.py:1204 resend_otp()` |
| FR-A7 | OTP **never** exposed in flash messages — server log only | `app.py:1044`, `app.py:1244`, `app.py:2396` use `logger.warning(...)` |
| FR-A8 | Forgot password → OTP → single-use token → new password | `app.py:2331`, `app.py:2411`, `app.py:2446` |
| FR-A9 | Change password (verifies old password first) | `app.py:2485 change_password()` |
| FR-A10 | Session cookie secure + HttpOnly, 1-hour lifetime | `config.py:12-14` |
| FR-A11 | Duplicate-email conflict resolution during registration | `app.py:1109-1125` re-check before insert |
| FR-A12 | Account suspension blocks login | `app.py:842` |
| FR-A13 | Admin approval gate for alumni & faculty | `app.py:837`, `app.py:1104` |

### 3.2 Profiles

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-P1 | Role-specific profile tables (student / alumni / faculty) | `app.py:360`, `app.py:377`, `app.py:397` |
| FR-P2 | View profile by user_id with role-gated visibility | `app.py:1275`, `1296`, `1317`, `1355` |
| FR-P3 | Edit profile (owner or admin only) | `app.py:2023`, `2098`, `2190`, `2264` |
| FR-P4 | Profile photo upload (16 MB cap, png/jpg/jpeg/gif) | `app.py:76`, `utils/helpers.py:57 save_profile_photo()` |
| FR-P5 | Company logo upload for jobs | `utils/helpers.py:91 save_company_logo()` |
| FR-P6 | Profile completion wizard | `app.py:2538 complete_profile()` |
| FR-P7 | Faculty profile auto-created with defaults when missing | `app.py:1334`, `app.py:1540`, `services/profile_service.py:70 ensure_faculty_profile()` |
| FR-P8 | Avatar fallback via `ui-avatars.com` when no photo | `app.py:271`, `models/recommendation.py:177` |
| FR-P9 | Initials avatar Jinja filter | `app.py:95 get_initials()` |
| FR-P10 | Profile completeness meter on dashboard | `templates/student/dashboard.html` (`#completenessBar`) |

### 3.3 Connections (Instagram-Style)

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-C1 | Send connection request (role-agnostic: student↔alumni↔faculty) | `app.py:3809`, `routes/connection_routes.py:11` |
| FR-C2 | Mutual-request auto-connect | `app.py:3848-3871` |
| FR-C3 | Accept request → creates `connections` row + email + real-time notify | `app.py:3915` |
| FR-C4 | Reject request → status update + email + real-time notify | `app.py:3972` |
| FR-C5 | Query connection status between two users | `app.py:4024` (returns `connected` / `pending` / `received` / `none`) |
| FR-C6 | Pending request inbox per user | `app.py:4065` |
| FR-C7 | Full connection list | `routes/connection_routes.py:293` |
| FR-C8 | Pending-request cooldown (5 minutes) | `routes/connection_routes.py:45-56` |
| FR-C9 | Real-time Socket.IO push for request/accept/reject | `app.py:3886`, `3945`, `3997` (rooms `user_<id>`, `admin_monitor`) |
| FR-C10 | Email notification on request / accept / reject / mutual | `app.py:4096 send_connection_email()` |
| FR-C11 | Network search & filter (name/email + role) | `app.py:3546 search_network()` |
| FR-C12 | WhatsApp deep-link bridge that hides raw phone numbers | `app.py:4353`, `app.py:4372`, `templates/contact_bridge.html` |

### 3.4 Real-Time Messaging

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-M1 | Public (broadcast) chat over WebSocket | `routes/websocket_routes.py:80`, room `public_chat` |
| FR-M2 | 1-to-1 private chat with typing indicators + read receipts | `routes/websocket_routes.py:200`, `256`, `334`, `355` |
| FR-M3 | Per-user Socket.IO rooms (`user_<id>`) | `routes/websocket_routes.py:42` |
| FR-M4 | Private chat **gated on accepted connection** (admin exempt) | `app.py:1718-1726` |
| FR-M5 | Global admin messaging lock + soft-hide of all public messages | `database/messaging_db.py:53 lock_messaging()`, `183 hide_all_public_messages()` |
| FR-M6 | Per-user messaging suspension | `database/messaging_db.py:85-121` |
| FR-M7 | Admin message moderation (soft delete) | `database/messaging_db.py:171` |
| FR-M8 | Message content cap 5,000 characters | `routes/websocket_routes.py:101`, `routes/messaging_routes.py:78` |
| FR-M9 | Conversation thread tracking (last message, unread count) | `database/messaging_db.py:275 get_user_conversations()` |
| FR-M10 | Soft delete per-recipient view | `database/messaging_db.py:345` |
| FR-M11 | Message search (public / private / both) | `database/messaging_db.py:389` |
| FR-M12 | REST mirror of all messaging operations under `/api/messages/*` | `routes/messaging_routes.py` |
| FR-M13 | Admin messaging statistics | `database/messaging_db.py:504` |
| FR-M14 | Online-user presence broadcast | `routes/websocket_routes.py:26`, `390` |

### 3.5 Career Board / Jobs

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-J1 | Alumni & faculty post jobs | `app.py:4552 post_job()` |
| FR-J2 | Admin posts jobs directly (30+ fields, 11-section form) | `app.py:3225 admin_add_job()` |
| FR-J3 | Admin approval workflow for alumni/faculty postings | `approval_status` column, `app.py:3123`, `3152` |
| FR-J4 | Real-time approval/rejection push to poster | `app.py:3139`, `3169` (`job_approval_update`) |
| FR-J5 | Rejection reason captured | `jobs.rejection_reason`, `app.py:3163` |
| FR-J6 | Job lifecycle: Open / Closed / Expired (deadline-driven) | `app.py:1634 list_jobs()`, `app.py:1965 alumni_jobs()` |
| FR-J7 | Admin Jobs Matrix with status toggle | `app.py:3069`, `app.py:3202` |
| FR-J8 | Pending-approval badge counter API | `app.py:3184 api_pending_jobs_count()` |
| FR-J9 | Company logo + website + CTC range + perks + selection process | `app.py:600 jobs_cols_to_add`, `templates/admin/add_job.html` |
| FR-J10 | Skill-based job recommendation (top 5) | `models/recommendation.py:213 get_recommended_jobs()` |
| FR-J11 | Apply link / apply method support | `apply_link`, `apply_method` columns |

### 3.6 Recommendation Engine (Hybrid ML)

**Phase 1 — Rule-Based** (`models/recommendation.py:26`)

| Signal | Score |
| --- | --- |
| Same branch / department | +5 |
| Skill overlap | +5 per matching skill |
| Same professional domain | +3 |
| Passing year within 2 years | +4 |
| Passing year within 4 years | +2 |
| Same city | +2 |
| Mutual connections | +2 per mutual |

**Phase 2 — ML Collaborative Filtering** (`services/recommendation_engine.py`)

| Signal | Weight | Direction | Source Table |
| --- | --- | --- | --- |
| Accepted connection | 5 | Bidirectional | `connections` |
| Private message | 4 | Sender → Receiver | `private_messages` |
| Connection request | 3 | Sender → Receiver | `connection_requests` |
| Job application | 2 | Student → Job poster | `job_applications` |
| `profile_view` | 1 | User → Target | `user_interactions` |
| `job_click` | 2 | User → Target | `user_interactions` |
| `mentorship_request` / `message` | 4 | User → Target | `user_interactions` |

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-R1 | Build user×user interaction matrix from real DB data | `services/recommendation_engine.py:68 build_interaction_matrix()` |
| FR-R2 | KNN with cosine similarity, `n_neighbors = min(10, n-1)`, brute algorithm | `services/recommendation_engine.py:188 train_knn_model()` |
| FR-R3 | Train once at startup in a background daemon thread, cache globally with a lock | `services/recommendation_engine.py:469 init_recommendation_engine()`, `_model_cache` at `:55` |
| FR-R4 | 5-minute retrain cache guard | `services/recommendation_engine.py:205` |
| FR-R5 | Cold-start fallback: users with < 2 interactions get rule-based only | `services/recommendation_engine.py:50 MIN_INTERACTIONS`, `:298` |
| FR-R6 | Hybrid merge — ML first, rule-based fills remaining, dedupe, sort by score, top 5 | `services/recommendation_engine.py:381 hybrid_recommendation()` |
| FR-R7 | Cross-role matching: students see alumni, alumni see students | `models/recommendation.py:59`, `services/recommendation_engine.py:334` |
| FR-R8 | Exclude self, already-connected and pending-request users | `models/recommendation.py:62`, `services/recommendation_engine.py:312` |
| FR-R9 | API: `GET /recommendations`, `GET /recommendations/<id>`, `POST /recommendations/retrain` (admin), `POST /recommendations/log` | `routes/recommendation_routes.py` |
| FR-R10 | AI badge on ML-sourced recommendation cards | `templates/student/dashboard.html`, `templates/alumni/dashboard.html` |
| FR-R11 | One-click Connect from a recommendation card | `/api/connection-request/send` |
| FR-R12 | Graceful degradation if scikit-learn/numpy missing | `services/recommendation_engine.py:253 ImportError` handler |

### 3.7 Administration & Governance

| ID | Requirement | Implementation Evidence |
| --- | --- | --- |
| FR-D1 | Dashboard with role counts + 5-year registration chart | `app.py:1608`, `services/admin_service.py:190`, `:212` |
| FR-D2 | View/manage users by role | `app.py:1380 admin_view_users()` |
| FR-D3 | Pending approval queue | `app.py:1398`, `app.py:4706`, `app.py:4723` |
| FR-D4 | User deletion with cascade + Super Admin protection | `app.py:2963 delete_user()` (protects `admindbit195@college.edu`) |
| FR-D5 | Registration log with role filter + search + CSV export | `app.py:170`, `app.py:2654`, `app.py:2708` |
| FR-D6 | Role-specific user CSV export | `app.py:2770 download_csv()` |
| FR-D7 | Full SQLite database download | `app.py:2905 download_database()` |
| FR-D8 | Analytics page | `app.py:2624 admin_analytics()` |
| FR-D9 | Live connection monitor (role filter + search + user drill-down modal) | `app.py:1750`, `app.py:1784`, `services/admin_service.py:124` |
| FR-D10 | Messaging control panel | `app.py:1739`, `templates/admin/admin_messaging_control.html` |
| FR-D11 | WhatsApp broadcast (role filtered, link generation) | `app.py:3410` |
| FR-D12 | WhatsApp auto-send via pywhatkit | `app.py:3471` |
| FR-D13 | Email compose to any user with rich signature | `app.py:4392`, `app.py:4472` |
| FR-D14 | Report an issue (public) → email to admin | `app.py:4264` |
| FR-D15 | Contact form → dual email (admin + requester confirmation) | `app.py:672` |

### 3.8 Content / Informational Pages

Home, About (incl. team section), Services, Events, Contact, FAQ, Privacy Policy, Terms & Conditions, Report Issue, Spotlight, Announcements, Mentorship, Coming Soon — all under `templates/common/*` with dedicated enhancement CSS.

---

## 4. Non-Functional Requirements

| ID | Category | Requirement | Evidence |
| --- | --- | --- | --- |
| NFR-1 | Performance | Admin dashboard must not use per-row COUNT loops | Single `GROUP BY role` + single `GROUP BY year, role` — `app.py:1634`, `1647` |
| NFR-2 | Performance | Indexed access paths on hot tables | 26 indexes in DB; 15 declared in `app.py:547` |
| NFR-3 | Performance | `SELECT *` avoided in existence checks | `SELECT 1 FROM connections` — `app.py:1720` |
| NFR-4 | Concurrency | SQLite WAL mode + `synchronous=NORMAL`, 20 s busy timeout | `db_utils.py:11-13`, `database/messaging_db.py:17-19` |
| NFR-5 | Reliability | Every route closes its DB connection via `try/finally` | 62 `get_db_connection()` call sites, all guarded |
| NFR-6 | Reliability | Blueprints registered at **module level** so Gunicorn/Vercel works | `app.py:4827-4850` |
| NFR-7 | Reliability | DB migration runs on every startup (idempotent `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE` guarded) | `app.py:4861 init_db()` |
| NFR-8 | Observability | Structured `logging` module (not bare `print`) for errors | `app.py:35`, `logger` used in services/routes |
| NFR-9 | Security | XSS prevention — Jinja2 autoescape + `sanitize_html()` | `utils/helpers.py:189` |
| NFR-10 | Security | Role-based access control via decorator + per-route checks | `utils/decorators.py:26 role_required()` |
| NFR-11 | Security | Error messages never leak internals | `utils/helpers.py:177 safe_error_message()`, JSON 403/500 generic messages |
| NFR-12 | Upload safety | 16 MB request cap, extension whitelist, `secure_filename` | `app.py:76`, `utils/helpers.py:52` |
| NFR-13 | Responsiveness | Laptop / tablet / mobile layouts, stacking grids | Bootstrap 5 + media queries across `static/css/*` |
| NFR-14 | UX performance | 60 fps animations, GPU-accelerated transforms | `static/css/animations.css`, `ui-enhancements.css` |
| NFR-15 | SEO | Meta description, keywords, Open Graph, Twitter cards, canonical, robots.txt, sitemap.xml | `templates/base.html:8-32`, `app.py:3579`, `app.py:3584` |
| NFR-16 | Deployment | PythonAnywhere (Procfile → gunicorn) **and** Vercel config supported | `Procfile`, `vercel.json` |

---

## 5. Technical Stack (as implemented)

### Backend
- **Flask 2.3.2** + **Flask-Login 0.6.2** + **Werkzeug 2.3.6**
- **Flask-SocketIO 5.3.4** / python-socketio 5.9.0 / python-engineio 4.7.1 (`async_mode='threading'`)
- **Flask-Mail** over Gmail SMTP (`smtp.gmail.com:587`, STARTTLS)
- **Flask-APScheduler** — one job: `periodic_profile_reminder`, every 2 days
- **SQLite** via raw `sqlite3` (no ORM), `row_factory = sqlite3.Row`, WAL mode
- **scikit-learn ≥ 1.3.0** (`sklearn.neighbors.NearestNeighbors`, `sklearn.preprocessing.normalize`)
- **numpy ≥ 1.24.0**
- **python-dotenv 1.0.0** for `.env`
- **pywhatkit** (lazy-loaded) for WhatsApp automation

### Frontend
- **Bootstrap 5.3** (CDN), **FontAwesome 6.4**, **AOS 2.3.1**, **animate.css 4.1.1**, **Chart.js**
- **Google Fonts:** Outfit, Plus Jakarta Sans (JetBrains Mono on admin dashboard)
- **Socket.IO client 4.5.4** (CDN)
- **Vanilla Tilt 1.7.0** (3D tilt cards)
- 13 custom CSS files + 4 custom JS files
- Jinja2 templating with `base.html` master layout

---

## 6. Data Model Summary

20 tables in `data/college_pro.db`.

### Core
| Table | Purpose | Key Columns |
| --- | --- | --- |
| `users` | Identity + shared profile | `email` UNIQUE, `role`, `password`, `is_verified`, `is_approved`, `is_suspended`, `branch`, `passing_year`, `current_domain`, `skills`, `interests`, `city`, `company`, `bio` |
| `student_profile` | Student-specific | `user_id` UNIQUE, `enrollment_no` UNIQUE, `department`, `degree`, `semester`, `cgpa`, `skills`, `achievements`, `resume_link` |
| `alumni_profile` | Alumni-specific | `user_id` UNIQUE, `enrollment_no`, `department`, `degree`, `pass_year`, `company_name`, `designation`, `work_location`, `experience_years`, `linkedin_url`, `skills`, `bio`, `achievements` |
| `faculty_profile` | Faculty-specific | `user_id` UNIQUE, `employee_id` UNIQUE, `department`, `designation`, `specialization`, `qualification`, `experience_years`, `office_location`, `office_hours`, `bio` |

### Social Graph
| Table | Purpose |
| --- | --- |
| `connection_requests` | `sender_id`, `receiver_id`, `status` (pending/accepted/rejected), `accepted_at`, `updated_at`, `UNIQUE(sender_id, receiver_id)` |
| `connections` | `user_id_1`, `user_id_2`, `connected_at`, `UNIQUE(user_id_1, user_id_2)` — always stored min/max |
| `user_interactions` | ML training signal: `user_id`, `target_user_id`, `interaction_type` |

### Messaging
| Table | Purpose |
| --- | --- |
| `public_messages` | Broadcast chat, `is_hidden`, `deleted_by` (soft delete) |
| `private_messages` | 1-to-1, `is_read`, `read_at`, `deleted_by_sender`, `deleted_by_receiver` |
| `conversations` | `user_id_1`, `user_id_2`, `last_message_id`, `last_message_at`, `UNIQUE(user_id_1, user_id_2)` |
| `messaging_lock` | Single-row global switch (`id = 1`), `is_locked`, `locked_by`, `reason` |
| `message_search_index` | Reserved search index table (currently unused) |

### Governance / Ops
| Table | Purpose |
| --- | --- |
| `registration_log` | Full registration audit trail with role-specific metadata |
| `password_resets` | OTP store for password recovery |
| `user_activity` | `last_login`, `online_status` for admin monitoring |
| `alumni_meet_registration` | 23-field alumni meet form |
| `temp_users` | Pending OTP registrations |
| `jobs` | 40+ columns covering the full recruitment lifecycle |
| `job_applications` | Student → job applications (feeds ML weight 2) |

---

## 7. API Surface

### 7.1 In-app routes (`app.py`) — 100+ endpoints

**Public:** `/` `/about` `/services` `/events` `/contact` `/login` `/register` `/verify-otp` `/resend-otp` `/forgot-password` `/verify-reset-otp` `/reset-password-final` `/privacy-policy` `/terms-conditions` `/faq` `/report-issue` `/robots.txt` `/sitemap.xml`

**Student/Role:** `/student/dashboard` `/alumni/dashboard` `/faculty/dashboard` `/admin/dashboard` `/profile` `/profile/complete/<id>` `/network` `/messages` `/mentorship` `/notifications` `/settings` `/jobs` `/post-job` `/spotlight` `/events` `/announcements` `/reports` `/upgrade` `/change-password` `/logout`

**Profiles:** `/student|alumni|faculty|admin/profile/<user_id>` and `/…/edit`

**Alumni Meet:** `/alumni/meet/register` `/alumni/meet/view`

**Admin:** `/admin/users/<role>` `/admin/approve-requests` `/admin/verify-user/<id>/<action>` `/admin/analytics` `/admin/registrations` `/admin/export/registrations` `/admin/jobs` `/admin/jobs/add` `/admin/jobs/edit/<id>` `/admin/jobs/approve/<id>` `/admin/jobs/reject/<id>` `/admin/jobs/delete/<id>` `/admin/whatsapp-broadcast` `/admin/messaging-control` `/admin/connection-monitor` `/admin/connection-monitor/user/<id>` `/admin/events` `/admin/stats`

**REST JSON:** `/api/faculty/students` `/api/faculty/alumni` `/api/alumni/<id>` `/api/student/<id>` `/api/delete-user/<id>` `/api/download-csv/<role>` `/api/download-db/<type>` `/api/approve-user/<id>` `/api/reject-user/<id>` `/api/admin/jobs/pending-count` `/api/admin/jobs/toggle/<id>`

### 7.2 Blueprints
| Blueprint | Prefix | File |
| --- | --- | --- |
| `messaging_bp` | `/api` | `routes/messaging_routes.py` |
| `connection_bp` | `/api/connection-request` | `routes/connection_routes.py` |
| `recommendation_bp` | `/` | `routes/recommendation_routes.py` |
| `social_bp` | `/social` | `routes/social_routes.py` |
| WebSocket handlers | — | `routes/websocket_routes.py` (`setup_websocket_handlers(socketio)`) |

### 7.3 Socket.IO Events

**Client → Server:** `send_public_message`, `delete_public_message`, `lock_messaging`, `unlock_messaging`, `send_private_message`, `mark_message_read`, `mark_conversation_read`, `delete_private_message`, `typing_public`, `stop_typing_public`, `typing_private`, `stop_typing_private`, `get_online_users`, `refresh_lock_status`, `get_conversation_history`

**Server → Client:** `receive_public_message`, `message_sent`, `message_deleted_public`, `message_deleted`, `system_locked`, `system_unlocked`, `lock_success`, `unlock_success`, `receive_private_message`, `message_read`, `conversation_read`, `read_success`, `message_deleted_private`, `delete_success`, `user_typing_public`, `user_stopped_typing_public`, `user_typing_private`, `user_stopped_typing_private`, `user_online`, `user_offline`, `online_users`, `lock_status_update`, `conversation_history`, `error`, `connection_request_received`, `connection_status_update`, `admin_connection_activity`, `job_approval_update`

**Rooms:** `public_chat`, `user_<user_id>`, `admin_monitor`

---

## 8. Success Metrics

| Metric | Target |
| --- | --- |
| Registration completion rate (OTP verified) | > 90% |
| Alumni/faculty approval turnaround | < 24 h |
| Recommendation CTR (card → connect request) | > 25% |
| Connection request acceptance rate | > 40% |
| Job applications per approved posting | > 10 |
| Page load (dashboard, warm) | < 2 s |
| Zero leaked DB connections in logs | 0 |
| Lighthouse accessibility score | > 90 |

---

## 9. Out of Scope (v5.0)

- Post/comment/like feed — code defensively deletes from `posts`/`comments`/`likes` (`app.py:3027-3042`) but **no such tables exist**; feature is not implemented
- Follower graph — `get_user_statistics()` derives followers/following from accepted connections because there is no separate followers table (`services/admin_service.py:20-42`)
- `message_search_index` — table created but no write path
- `GET /api/messages/private/<conversation_id>` — explicit placeholder returning "needs proper implementation" (`routes/messaging_routes.py:201-217`)
- `utils.db.get_db()` context manager — implemented and documented but **not yet adopted** by app code (all routes still use `get_db_connection()` from `db_utils.py`)
- `POST /alumni/whatsapp-send-api` role check happens **after** lazy import of pywhatkit (`app.py:3475-3476`)
- `post_job()` redirects faculty to `url_for('faculty_dashboard')` but the registered endpoint is `dashboard_faculty` — will raise a `BuildError` (`app.py:4616`)
- ML model is never retrained automatically after startup; only via admin API or restart

---

## 10. Future Roadmap

**Recommendation / ML**
1. Weighted ensemble `α × ML_score + (1−α) × rule_score`
2. Graph Neural Networks on the social graph
3. Matrix factorization (SVD / ALS) for implicit feedback
4. Incremental retraining on interaction events
5. A/B testing harness for algorithm comparison
6. Contextual bandits for recommendation diversity

**Platform**
7. PostgreSQL/Neon production database (`scripts/init_postgres.py` already exists)
8. Redis message queue for horizontal WebSocket scaling
9. Push notifications (Web Push / FCM)
10. Full-text search engine (PostgreSQL FTS / Elasticsearch)
11. Mentorship request workflow with matching + slots
12. Event creation/management by admin (currently informational only)

**Governance**
13. Audit log for admin actions
14. Rate limiting / brute-force protection on login + OTP
15. Two-factor authentication

---

## 11. Constraints & Assumptions

- **Email delivery depends on Gmail App Password**; without valid `MAIL_USERNAME`/`MAIL_PASSWORD` OTPs never reach users (app still redirects to the OTP page).
- **Only `@gmail.com` registrations are accepted** (academic-project constraint).
- **SQLite** limits concurrent writes; WAL mode + 20 s timeout is the mitigation. PostgreSQL is the intended upgrade.
- **Vercel's serverless filesystem is ephemeral** — the SQLite file and `static/uploads/` will not persist between invocations; `vercel.json` exists but a managed DB is required for real production use.
- `pywhatkit` drives a real browser for WhatsApp send — requires a desktop session, unsuitable for serverless.
- Seeded Super Admin: `admindbit195@college.edu` / `admindbit195@` (must be rotated before any real deployment).