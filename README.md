<div align="center">

# 🎓 Alumni Hub

### Connecting Generations — Building Connections, Creating Opportunities

A production-grade **Alumni Connection Network** that reunites a college community — bringing **students, alumni, faculty and administrators** into one platform with Instagram-style connections, real-time messaging, a moderated job board, and a hybrid **Rule-Based + ML Collaborative Filtering** recommendation engine.

[![Python](https://img.shields.io/badge/Python-3.7%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.2-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Flask-SocketIO](https://img.shields.io/badge/Flask--SocketIO-5.3.4-010101?style=flat-square&logo=socketdotio&logoColor=white)](https://flask-socketio.readthedocs.io/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20mode-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/wal.html)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-%3E%3D1.3-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat-square&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-10B981?style=flat-square)](#-license)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Screenshots](#-screenshots)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Database Schema](#-database-schema)
- [Recommendation Engine](#-recommendation-engine)
- [API Reference](#-api-reference)
- [Real-Time Events](#-real-time-events)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Performance](#-performance)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Known Issues](#-known-issues)
- [Contributing](#-contributing)
- [License](#-license)
- [Documentation](#-documentation)
- [Credits](#-credits)

---

## 💡 Overview

Colleges lose touch with their alumni the moment students graduate. Emails go stale, opportunities live in private WhatsApp groups, and placement cells run on spreadsheets.

**Alumni Hub** solves this with a single platform that serves four distinct audiences:

| Role | What they get |
| --- | --- |
| 🎓 **Student** | Alumni & faculty directory, mentorship requests, personalised job board, peer networking, AI-matched connection suggestions |
| 🎮 **Alumni** | Give back — mentor students, post real openings, register for meets, grow their professional network |
| 👨‍🏫 **Faculty** | Academic guidance, student & alumni directories, post opportunities, share announcements |
| 🛡️ **Admin** | Full user governance, live analytics, job approval queue, messaging moderation, CSV/DB export, real-time connection monitoring |

**What makes it different:** the platform does not stop at a directory. It ships a **two-phase hybrid recommender** — deterministic rule-based scoring backed by a machine-learned KNN collaborative-filtering model — that suggests who each member should know, and self-heals its own database schema on every boot.

> **Project status:** v1.0 — *first release* · Core features complete · Production-hardening in progress

---

## 📸 Screenshots

| View | Route | What it shows |
| --- | --- | --- |
| Landing page | `/` | Animated hero, live particle network, statistics, feature grid |
| Student dashboard | `/student/dashboard` | Profile completeness, personalised jobs, recommendations, stats |
| Alumni directory | `/alumni` | Filterable alumni grid with connection actions |
| Recommendation feed | `/recommendations` | Scored suggestion cards with AI/rule source badges |
| Job board | `/student/jobs` | Skill-matched openings with apply actions |
| Private chat | `/messaging/private/<user_id>` | Real-time thread with typing indicators and read receipts |
| Admin dashboard | `/admin/dashboard` | Role counts, 5-year registration chart, quick actions |
| Connection monitor | `/admin/connection-monitor` | Live WebSocket activity feed with drill-down |

> 📸 **Screenshots are not yet committed.** To publish this README on GitHub, capture the views above
> into `docs/screenshots/` at 1440 px width and replace this table with the image embeds.

---

## ✨ Features

### 🔐 Authentication & Account Security
- Email + password login with **role-based dashboard redirection**
- Registration restricted to Gmail addresses, with a **staged OTP flow** (user is created only after email verification)
- 6-digit cryptographically-random OTP with a **2-minute expiry** — generation, resend and verification
- Password recovery via single-use reset OTP (10-minute validity)
- Change-password flow that verifies the current password first
- **Centralised password policy** — minimum 8 characters via one shared validator
- Secure session cookies (`HttpOnly`, `Secure` in production, 1-hour lifetime)
- **Admin approval gate** — alumni and faculty accounts stay locked until approved
- Per-user **suspension** with immediate session invalidation

### 👤 Multi-Role Profiles
- Separate profile schemas per role: student (enrolment no, semester, CGPA, skills, resume) · alumni (company, designation, work location, experience, LinkedIn) · faculty (employee ID, specialisation, qualification, office hours)
- View, edit and upload a profile photo — restricted to the owner or an admin
- Automatic default profile creation for faculty members who have none
- Avatar fallback chain: uploaded photo → initials → generated `ui-avatars` image
- Live **profile completeness meter** on the student dashboard
- **Student → Alumni self-upgrade** flow that migrates profile data

### 🤝 Instagram-Style Connection System
- Send, accept or reject connection requests between **any** two roles
- **Mutual-request auto-connect** — if both sides requested, they connect instantly
- 5-minute cooldown before a request can be re-sent
- Live in-app notifications over WebSocket, plus email for request/accept/reject/mutual
- Network search with role filtering
- **Privacy-preserving WhatsApp bridge** — contact buttons route through a server-side redirect so phone numbers are never exposed in page HTML

### 💬 Real-Time Messaging
- **Public chat room** broadcast to every authenticated user
- **1-to-1 private chat** gated on an accepted connection
- Typing indicators, **read receipts**, unread badges and conversation threads
- **Global admin messaging lock** — instantly hides the entire public feed
- **Per-user messaging suspension**
- Admin message moderation with soft delete
- Message search across public and private scopes
- Online presence indicators
- A complete **REST mirror** of every WebSocket operation, so either transport works

### 💼 Career Board
- Job posting by alumni and faculty (requires admin approval) and by admin (instant publish)
- **11-section Add/Edit Job form** capturing 40+ professional fields: work mode, employment type, eligibility (branch / batch / minimum CGPA), skills required vs preferred, CTC range, perks, openings, selection process, joining date, deadline, apply method
- Company logo upload and company website
- Automated recruitment lifecycle — **Open / Closed / Expired** driven by the deadline
- **Jobs Matrix** admin view with live status toggles and a pending-approval queue
- Real-time approval/rejection push to the job poster, with a rejection reason
- **Skill-based job recommendations** for students

### 🧠 Hybrid Recommendation Engine
- Deterministic rule-based scoring combined with **KNN collaborative filtering (cosine similarity)**
- Explicit **cold-start handling** — users with insufficient interaction history fall back to rules
- Mutual-connection awareness, cross-role matching, and duplicate suppression
- ML-sourced results are visually tagged with an **AI badge**
- One-click connect directly from a recommendation card

### 🛡️ Administration & Governance
- Live dashboard with role counts and a **5-year registration chart** (Chart.js)
- User management by role, plus a pending-approval queue
- Registration audit log with role-specific metadata, filtering, search and CSV export
- Role-specific CSV export and full database download
- **Real-time connection monitor** with role filters, search and per-user drill-down
- Messaging control panel
- WhatsApp broadcast generator
- Rich composed email with a profile link, WhatsApp bridge and LinkedIn signature
- Automatic **profile-update reminder** every 2 days via APScheduler

### 🎨 UI/UX
- Premium design system with tokenised colours, spacing, radii, shadows and motion
- Glassmorphism surfaces, animated mesh gradients, blob backgrounds and a live particle network
- 3D tilt cards, typing effects, word-reveal headings, magnetic navbar branding
- Scroll-triggered entrances and counters (with a re-trigger guard)
- Smart-scroll navbar, scroll progress bar, and a full-screen mobile menu
- **Fully responsive** from 360 px mobile to ultrawide desktop
- Full SEO block: meta description, keywords, Open Graph, Twitter cards, canonical URL, `robots.txt`, `sitemap.xml`

### 📄 Content Pages
Home · About (with team) · Services · Events · Contact · FAQ · Privacy Policy · Terms & Conditions · Report an Issue · Spotlight · Announcements · Coming Soon · Social links

---

## 🛠️ Tech Stack

### Backend

| Technology | Version | Purpose |
| --- | --- | --- |
| Flask | 2.3.2 | Core web framework |
| Flask-Login | 0.6.2 | Session & user authentication |
| Werkzeug | 2.3.6 | Password hashing, secure filenames |
| Flask-SocketIO | 5.3.4 | Real-time WebSocket transport |
| python-socketio | 5.9.0 | Socket.IO protocol |
| python-engineio | 4.7.1 | Engine.IO transport layer |
| Flask-Mail | latest | SMTP mail delivery |
| Flask-APScheduler | latest | Background job scheduling |
| numpy | ≥ 1.24.0 | Interaction matrix |
| scikit-learn | ≥ 1.3.0 | KNN collaborative filtering |
| python-dotenv | 1.0.0 | Environment variable loading |
| email-validator | 2.0.0 | Email format validation |

### Frontend

| Technology | Purpose |
| --- | --- |
| Bootstrap 5.3 | Grid, components, responsive utilities |
| Vanilla CSS (12 layered files) | Custom design system on top of Bootstrap |
| FontAwesome 6.4 | Iconography |
| AOS 2.3.1 + animate.css 4.1.1 | Scroll & entrance animations |
| Chart.js | Admin analytics charts |
| Socket.IO Client 4.5.4 | Real-time messaging |
| Vanilla Tilt 1.7.0 | 3D card tilt |
| Google Fonts | Outfit · Plus Jakarta Sans · JetBrains Mono |
| Jinja2 | Server-side templating |

### Database
**SQLite** accessed through the raw `sqlite3` driver — no ORM. WAL journal mode, `synchronous=NORMAL`, 20-second busy timeout, `sqlite3.Row` row factory.

---

## 🏗️ Architecture

A **layered monolith** with a genuine service/utility split.

```
┌──────────────────────────────────────────────────────────┐
│  PRESENTATION   Jinja2 templates · Bootstrap 5 · AOS     │
│                 common · auth · student · alumni ·        │
│                 faculty · admin · messaging · social      │
├──────────────────────────────────────────────────────────┤
│  ROUTING        app.py (~100 routes) + 4 Blueprints      │
│                 messaging · connection ·                 │
│                 recommendation · social                   │
│                 + Socket.IO event handlers                │
├──────────────────────────────────────────────────────────┤
│  SERVICE        admin_service · profile_service ·         │
│                 recommendation_engine (ML) ·              │
│                 models/recommendation (rules)             │
├──────────────────────────────────────────────────────────┤
│  PERSISTENCE    db_utils · utils/db · messaging_db       │
│                 SQLite · 19 tables · 25 named indexes       │
├──────────────────────────────────────────────────────────┤
│  INFRA          config · extensions (Mail) ·             │
│                 utils/helpers · utils/decorators ·        │
│                 APScheduler                               │
└──────────────────────────────────────────────────────────┘
```

### Design decisions worth knowing

| Decision | Why |
| --- | --- |
| Bootstrap registration and DB migration run at **module level**, not in `__main__` | Makes `python app.py`, `gunicorn app:app` and serverless entry points behave identically |
| Schema is **self-migrating and idempotent** | `CREATE TABLE IF NOT EXISTS` + guarded `ALTER TABLE` — no migration tool or deploy step required |
| Every route closes its connection in `finally` | Eliminates SQLite lock contention under concurrent WebSocket traffic |
| The ML model is **cached in memory and trained once** | Recommendation latency becomes a single array lookup instead of a full model fit |
| The ML engine **degrades to rule-based** rather than failing | A missing `scikit-learn` install or a sparse matrix never breaks the app |
| Connections stored as a canonical `min/max` pair | The `UNIQUE(user_id_1, user_id_2)` constraint makes duplicate edges structurally impossible |
| Messages are **soft-deleted**, never hard-deleted | Community archives stay intact while content disappears from the relevant view |

Full detail: **[`docs/Architecture.md`](docs/Architecture.md)**

---

## 🗄️ Database Schema

19 tables and 25 explicitly-named indexes (plus 11 implicit indexes from `UNIQUE` constraints). The schema is created and migrated automatically on every application boot.

| Table | Purpose |
| --- | --- |
| `users` | Identity, role, credentials, verification/approval/suspension flags, shared profile fields |
| `student_profile` | Enrolment number, department, degree, semester, CGPA, skills, achievements, resume link |
| `alumni_profile` | Enrolment number, pass year, company, designation, work location, experience, LinkedIn |
| `faculty_profile` | Employee ID, specialisation, qualification, office location & hours |
| `connection_requests` | Directed requests with status and acceptance timestamp |
| `connections` | Accepted friendships (canonical pair, unique) |
| `user_interactions` | ML training signals — profile views, job clicks, mentorship requests |
| `public_messages` | Broadcast chat with hidden/deleted flags |
| `private_messages` | 1-to-1 chat with read receipts and per-recipient soft delete |
| `conversations` | Thread index with last-message pointer and unread counts |
| `messaging_lock` | Single-row global messaging switch |
| `jobs` | 40+ fields covering the full recruitment lifecycle |
| `job_applications` | Student → job applications (ML signal, weight 2) |
| `registration_log` | Registration audit trail with role-specific metadata |
| `password_resets` | Single-use password recovery OTPs |
| `user_activity` | Last login and online status for admin monitoring |
| `alumni_meet_registration` | 23-field alumni meet form |
| `temp_users` | Staged registrations awaiting OTP verification |
| `message_search_index` | Reserved for a future full-text search migration |

### Key indexes

| Query pattern | Index |
| --- | --- |
| Login by email | `idx_users_email` (+ UNIQUE autoindex) |
| User list by role | `idx_users_role` |
| Pending requests for a user | `idx_connection_requests_receiver (receiver_id, status)` |
| Connection lookup, both directions | `idx_connections_user1`, `idx_connections_user2` |
| Yearly registration grouping | `idx_users_created_at` |
| ML interaction lookups | `idx_user_interactions_user`, `idx_user_interactions_target` |

---

## 🧠 Recommendation Engine

### Phase 1 — Rule-Based Scoring

Deterministic profile-similarity scoring in [`models/recommendation.py`](models/recommendation.py).

| Signal | Points | Notes |
| --- | --- | --- |
| Same branch / department | **+5** | Case-insensitive |
| Skill overlap | **+5** per matching skill | Comma-separated sets |
| Same professional domain | **+3** | |
| Passing year within 2 years | **+4** | |
| Passing year within 4 years | **+2** | |
| Same city | **+2** | |
| Mutual connections | **+2** per mutual | Social-graph proximity |

Excluded from results: yourself, already-connected users, and users with a pending request.
Matching is cross-role — students see alumni, alumni see students.

### Phase 2 — ML Collaborative Filtering

KNN with cosine similarity in [`services/recommendation_engine.py`](services/recommendation_engine.py).

**Interaction weights**

| Signal | Weight | Direction | Source table |
| --- | --- | --- | --- |
| Accepted connection | 5 | Bidirectional | `connections` |
| Private message | 4 | Sender → Receiver | `private_messages` |
| Connection request | 3 | Sender → Receiver | `connection_requests` |
| Job application | 2 | Student → Job poster | `job_applications` |
| `profile_view` | 1 | User → Target | `user_interactions` |
| `job_click` | 2 | User → Target | `user_interactions` |
| `mentorship_request` / `message` | 4 | User → Target | `user_interactions` |

Notes:
- Only **pending** connection requests contribute (`WHERE status = 'pending'`).
- `user_interactions` weights are **multiplied by the row count** for that
  `(user_id, target_user_id, interaction_type)` group — repeat engagement counts more.
- Each source is queried inside a `try/except`, so a missing table is logged at debug level and
  skipped rather than failing the whole training run.
- All signals **accumulate** (`+=`), they do not overwrite.

**Model**

- `sklearn.neighbors.NearestNeighbors(metric='cosine', algorithm='brute')`
- L2-normalised interaction vectors
- `n_neighbors = min(10, n_users − 1)`
- Cosine distance converted to a 0–100 similarity score
- Trained **once at startup** in a background daemon thread, cached in a thread-safe module-level cache
- 5-minute guard prevents redundant retrains
- Manual retrain via `POST /recommendations/retrain` (admin only)

### Cold Start

A user whose interaction vector has fewer than **2 non-zero entries** (`MIN_INTERACTIONS = 2`)
receives pure rule-based recommendations. As they connect, message and apply, the ML model
gradually takes over.

### Hybrid Strategy

```
hybrid_recommendation(user_id, limit=5):

1. ml_recs = get_ml_recommendations(user_id, limit)      # [] if cold-start or model unavailable
2. final   = unique(ml_recs)          tagged source='ml'
3. if len(final) < limit:
       fetch rule_recs = get_rule_based_recommendations(user_id, limit * 2)
       append any ID not already present   tagged source='rule'
       until len(final) == limit
4. sort final by score descending
5. return final[:limit]
```

Rule-based candidates are fetched at `limit * 2` so there is headroom to discard IDs that ML
already returned. ML scores and rule scores share the same `score` field, so the final sort
mixes both scales — this is a known limitation tracked in [`docs/Tasks.md`](docs/Tasks.md).

### Interaction Matrix

```sql
CREATE TABLE IF NOT EXISTS user_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_user_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL,  -- profile_view | job_click | mentorship_request | message | connection_request
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id)
);
```

---

## 🔌 API Reference

### Connection Requests

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| POST | `/api/connection-request/send` | Login | Send a connection request |
| POST | `/api/connection-request/accept/<sender_id>` | Login | Accept a request → creates the connection |
| POST | `/api/connection-request/reject/<sender_id>` | Login | Reject a request |
| GET | `/api/connection-request/status/<user_id>` | Login | `connected` · `pending` · `received` · `none` |
| GET | `/api/connection-requests/pending` | Login | Incoming pending requests |

### Recommendations

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| GET | `/recommendations` | Login | Current user's top 5 (backward-compatible) |
| GET | `/recommendations/<user_id>` | Self or Admin | JSON recommendations for a specific user |
| POST | `/recommendations/retrain` | Admin | Force-retrain the KNN model |
| POST | `/recommendations/log` | Login | Log an interaction for future training |

```jsonc
// GET /recommendations/1
{
  "user_id": 1,
  "count": 5,
  "recommendations": [
    {
      "id": 7,
      "name": "Rahul Sharma",
      "role": "alumni",
      "branch": "BCA",
      "skills": "Python, Flask, ML",
      "score": 72.5,
      "reason": "ML: similar interactions",
      "source": "ml",
      "profile_pic": "https://ui-avatars.com/api/?name=Rahul+Sharma&background=random"
    }
  ]
}
```

### Messaging

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| GET / POST | `/api/messages/public` | Login | List / send broadcast messages |
| DELETE | `/api/messages/public/<id>` | Admin | Moderate a public message |
| POST | `/api/messages/private` | Login | Send a private message |
| GET | `/api/messages/inbox` | Login | Conversations + unread count |
| GET | `/api/messages/conversation/<user_id>/messages` | Login | Conversation history |
| POST | `/api/messages/private/<id>/read` | Login | Mark as read |
| DELETE | `/api/messages/private/<id>` | Login | Soft-delete a message |
| GET | `/api/messages/search?q=` | Login | Search public and/or private messages |
| POST | `/api/admin/messaging/lock` · `/unlock` | Admin | Toggle global messaging |
| GET | `/api/admin/messaging/status` · `/statistics` | Admin | Lock state and platform stats |
| POST | `/api/admin/messaging/suspend` · `/unsuspend` | Admin | Per-user messaging control |

### Administration

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/download-csv/<role>` | Export users as CSV (student / alumni / faculty / all) |
| GET | `/api/download-db/<type>` | Download the database file |
| POST | `/api/delete-user/<id>` | Delete a user and all related data |
| POST | `/api/approve-user/<id>` · `/api/reject-user/<id>` | Approve or reject a registration |
| GET | `/api/admin/jobs/pending-count` | Pending job approval count |
| POST | `/api/admin/jobs/toggle/<id>` | Toggle a job's active state |

### Directory & Profile

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/faculty/students` · `/api/faculty/alumni` | Faculty directory data |
| GET | `/api/alumni/<id>` · `/api/student/<id>` | Profile data for modals |
| GET | `/admin/connection-monitor/user/<id>` | Full user activity payload |

---

## ⚡ Real-Time Events

**Socket.IO rooms** — `public_chat` (all users) · `user_<id>` (a single user) · `admin_monitor` (admins only)

### Client → Server

| Event | Payload | Notes |
| --- | --- | --- |
| `send_public_message` | `{ content }` | Blocked while globally locked |
| `send_private_message` | `{ receiver_id, content }` | Blocked for suspended users |
| `mark_message_read` | `{ message_id, sender_id }` | |
| `mark_conversation_read` | `{ other_user_id }` | |
| `delete_private_message` | `{ message_id, other_user_id }` | Soft delete |
| `delete_public_message` | `{ message_id }` | **Admin only** |
| `lock_messaging` / `unlock_messaging` | `{ reason }` | **Admin only** — also hides/shows all public messages |
| `typing_public` / `stop_typing_public` | — | |
| `typing_private` / `stop_typing_private` | `{ receiver_id }` | |
| `get_online_users` | — | |
| `refresh_lock_status` | — | |
| `get_conversation_history` | `{ other_user_id, limit }` | |

### Server → Client

| Event | Trigger |
| --- | --- |
| `receive_public_message` | A public message was sent |
| `receive_private_message` | A private message was sent to you |
| `message_sent` · `read_success` · `delete_success` | Sender acknowledgement |
| `message_read` · `conversation_read` | Read receipt |
| `message_deleted` · `message_deleted_public` · `message_deleted_private` | Deletion |
| `system_locked` · `system_unlocked` · `lock_success` · `unlock_success` | Admin moderation |
| `user_typing_public` · `user_typing_private` (and stop variants) | Typing indicator |
| `user_online` · `user_offline` · `online_users` | Presence |
| `connection_request_received` | A new request arrived for you |
| `connection_status_update` | Your request was accepted or rejected |
| `admin_connection_activity` | Live connection activity feed (admins) |
| `job_approval_update` | Your job posting was approved or rejected |
| `conversation_history` · `lock_status_update` · `error` | Utility |

**Where events live**

| Source | Emits |
| --- | --- |
| `routes/websocket_routes.py` — 17 `@socketio.on` handlers | All messaging, typing, presence and lock events |
| `app.py` — REST routes emit directly | `connection_request_received` (`:3886`), `connection_status_update` (`:3945`, `:3997`), `admin_connection_activity` (`:3894`, `:3953`, `:4005`), `job_approval_update` (`:3139`, `:3169`) |

All message content is capped at **5,000 characters**, enforced independently at both the WebSocket
layer (`routes/websocket_routes.py`) and the REST layer (`routes/messaging_routes.py`).

---

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or newer
- pip
- Git
- A Gmail account with 2FA enabled — to generate an **App Password** for SMTP (required for OTP delivery)

### 1. Clone & Set Up

```bash
git clone https://github.com/<username>/alumni-hub.git
cd alumni-hub

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> Installs `numpy` and `scikit-learn` for the ML recommendation engine. The app still runs without them — the recommender simply falls back to rule-based scoring.

### 3. Configure

Create a `.env` file in the project root:

```env
SECRET_KEY=generate-a-long-random-string
FLASK_ENV=development
DB_NAME=data/college_pro.db

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your.address@gmail.com
MAIL_PASSWORD=your-16-char-google-app-password

ADMIN_EMAIL=your.address@gmail.com
BASE_URL=http://localhost:5000
```

> 🔐 **Never commit `.env`.** It is already listed in `.gitignore`.
> Generate `SECRET_KEY` with `python -c "import secrets; print(secrets.token_hex(32))"`.
>
> There is **no `.env.example` file** in the repo — the block above is the canonical reference.
> Every variable has a hard-coded fallback in `config.py` / `app.py`, which is why the app boots
> without a `.env` at all. Do not rely on those fallbacks.

### 4. Run

```bash
python app.py
```

Open **http://127.0.0.1:5000**

> **No migration step is needed.** Tables, indexes and column migrations are created automatically on first boot and re-verified on every subsequent boot.

### 5. (Optional) Database Utilities

```bash
python scripts/init_db.py                  # Rebuild the base schema from scratch — DESTROYS DATA
python scripts/init_messaging_db.py        # Create messaging tables + lock row
python scripts/init_postgres.py            # Provision a PostgreSQL schema (requires DATABASE_URL + psycopg2)
python scripts/optimize_db.py              # Add performance indexes
python scripts/check_db.py                 # Inspect the live schema
python scripts/test_email.py               # Verify SMTP connectivity
```

### First-Run Admin Account

On the very first boot, `init_db()` seeds a single admin account — but **only** if
`SELECT COUNT(*) FROM users WHERE role='admin'` returns 0.

> 🔒 **The seeded credential is intentionally not printed in this README.** It is hard-coded at
> `app.py:575-577` and `scripts/init_db.py:106-114`, and it is already exposed in this repository's
> history — treat it as **compromised**. Any deployment that uses the seeded account without changing
> the password is publicly owned.
>
> **Before first real deployment:**
> 1. Read the seed values from `app.py:575-577`
> 2. Change the admin password in the app, or delete the seeded row and create your own admin
> 3. Rotate the Gmail app password in `app.py:50` — see [Known Issues](#-known-issues) #3
> 4. Never deploy with the hard-coded fallbacks still in place
>
> This account is protected from deletion by design (`app.py:2981-2984`).

---

## 📁 Project Structure

```
alumni-hub/
├── app.py                      # Main entry — app init, User model, ~100 routes, scheduler job
├── config.py                   # Environment-driven configuration + course/department data
├── extensions.py               # Flask extension instances (Mail)
├── db_utils.py                 # Primary database connection factory
├── requirements.txt            # Python dependencies
├── vercel.json                 # Serverless deployment config
├── Procfile                    # Gunicorn entry
│
├── database/
│   └── messaging_db.py         # All messaging persistence + moderation + statistics
│
├── models/
│   └── recommendation.py       # Phase 1: rule-based scoring, job matching
│
├── services/
│   ├── recommendation_engine.py  # Phase 2: KNN collaborative filtering + hybrid merge
│   ├── admin_service.py          # Optimised admin queries, connection monitoring
│   └── profile_service.py        # Profile write logic
│
├── routes/
│   ├── messaging_routes.py       # REST messaging API
│   ├── connection_routes.py      # Connection request API
│   ├── recommendation_routes.py  # Recommendation API
│   ├── social_routes.py          # Social link pages
│   └── websocket_routes.py       # Socket.IO event handlers
│
├── utils/
│   ├── helpers.py              # OTP, uploads, phone normalisation, validation, sanitisation
│   ├── db.py                   # DB context manager + query helpers
│   └── decorators.py           # @role_required() access control
│
├── scripts/                    # DB initialisation, migrations, diagnostics (16 scripts)
│
├── static/
│   ├── css/                    # 12 layered stylesheets + design tokens
│   ├── js/                     # Animations, particle network, sparkles
│   ├── images/                 # Assets, team photos
│   └── uploads/                # User uploads (profile photos, company logos)
│
├── templates/                  # 90 Jinja2 templates
│   ├── base.html               # Master layout — SEO, navbar, footer, scripts
│   ├── common/                 # Public pages
│   ├── auth/                   # Login, register, OTP, password flows
│   ├── student/ · alumni/ · faculty/ · admin/
│   ├── messaging/              # Public + private chat
│   ├── social/                 # Social link pages
│   └── emails/                 # Transactional email templates
│
├── data/
│   └── college_pro.db          # SQLite database
│
└── docs/                       # ← Project documentation
    ├── PRD.md                  # Product requirements
    ├── Architecture.md         # System architecture
    ├── Rules.md                # Coding, security & data rules
    ├── Design.md               # Design system
    ├── Tasks.md                # Roadmap & task breakdown
    └── Memory.md               # Project knowledge base
```

---

## 🔒 Security

| Control | Implementation |
| --- | --- |
| Password storage | Werkzeug salted hashes — plaintext is never persisted or logged |
| Password policy | Minimum 8 characters via a single shared validator |
| OTP generation | `secrets.choice` — cryptographically secure, not `random` |
| OTP exposure | Never rendered to the browser; server-side logging only |
| OTP lifetime | 2 minutes (registration) · 10 minutes (password reset) |
| Reset tokens | Single-use — deleted immediately after verification |
| XSS prevention | Jinja2 autoescaping + a dedicated `sanitize_html()` helper |
| SQL injection | Parameterised queries throughout; dynamic `IN (...)` built from placeholders |
| Session security | `HttpOnly` · `Secure` in production · 1-hour lifetime |
| Access control | Per-route role checks plus a reusable `@role_required()` decorator |
| Connection-gated chat | Private chat requires an accepted connection (admins exempt) |
| File uploads | Extension whitelist · `secure_filename` · 16 MB request cap |
| Error handling | Internal errors are logged, never returned to the user |
| Super Admin | Protected from deletion at the service layer |

### Reporting a vulnerability

Open a GitHub issue describing the issue, or contact the maintainers directly. Please do not include exploit payloads targeting live data.

---

## ⚡ Performance

| Metric | Value |
| --- | --- |
| Database indexes | 25 named indexes (+11 implicit `UNIQUE` indexes) across users, connections, requests, profiles and interactions |
| Admin dashboard queries | 2 `GROUP BY` queries replace 20+ `COUNT` queries |
| Existence checks | `SELECT 1` instead of `SELECT *` |
| Concurrency | SQLite WAL mode — multiple readers with a single writer |
| Connection safety | 105 `get_db_connection()` call sites, each wrapped in `try/finally` |
| ML inference | In-memory cached model — array lookup, not a model fit |
| Animations | GPU-accelerated transforms, 60 fps target |
| Asset delivery | Warm page load under 2 s |

---

## 🚀 Deployment

### PythonAnywhere / any WSGI host (recommended)

```
web: gunicorn app:app
```

Blueprints, the scheduler and database migrations all run at **module level**, so the app is fully initialised the moment Gunicorn imports it — no separate migration step.

### Turso Cloud (hosted SQLite)

The app can run against **Turso** — a hosted SQLite-compatible database — instead of a local
`.db` file. This is the cleanest way to deploy, because a serverless filesystem no longer has to
carry the database.

**How it works.** Every module already calls `db_utils.get_db_connection()` rather than
`sqlite3.connect()` directly, so the backend is decided in one place. When `TURSO_DATABASE_URL`
is present the factory returns a remote connection; otherwise it returns the local file exactly as
before. **Local development needs no configuration and behaves identically.**

```bash
# 1. Install the driver
pip install libsql

# 2. Add to .env
TURSO_DATABASE_URL=https://alumni-hub-<you>.turso.io
TURSO_AUTH_TOKEN=<token from the Turso dashboard>
TURSO_ENGINE=libsql          # 'tursodb' for the MVCC engine

# 3. Run — no other change needed
python app.py
```

**Which driver:** Turso hosts two incompatible engines, so `TURSO_ENGINE` must match the database.

| `TURSO_ENGINE` | Database | Driver | Concurrent writes |
| --- | --- | --- | --- |
| `libsql` (default) | Created in the Turso dashboard | `libsql` | Single writer |
| `tursodb` | Created with `turso db create --tursodb` | `turso_serverless` | MVCC |

**Migrating existing data** — the CLI is the simplest path:

```bash
turso db import ./data/college_pro.db      # requires WAL journal mode
```

**Compatibility shim.** The `libsql` driver returns plain tuples and has no `row_factory`
support, while this project reads rows as `row['column']` in ~100 places. `db_utils` wraps the
remote connection so rows behave like `sqlite3.Row`. The shim also corrects two driver quirks:
`cursor.rowcount` is only accurate on a freshly created cursor, and `fetchone()` after `fetchall()`
restarts instead of returning `None`.

```bash
python scripts/test_turso_adapter.py       # 34 checks: local mode, row conversion,
                                           # rowcount, fetch semantics, SQL dump
```

**Trade-off:** remote mode makes **every query an HTTP round trip**, so pages that run several
queries get noticeably slower than local SQLite. The admin dashboard and the ML recommendation
engine are the heaviest paths. Keep `TURSO_DATABASE_URL` unset while developing.

### Vercel

`vercel.json` is included. Pair it with Turso so the database survives cold starts.

> ⚠️ Turso solves the database, **not** `static/uploads/`. The serverless filesystem is still
> ephemeral, so uploaded profile photos and company logos are lost between cold starts. Use object
> storage (S3, Cloudflare R2) before treating a Vercel deploy as durable.

### Scaling WebSockets

`SocketIO` currently runs in `threading` async mode with in-process presence tracking, which is single-instance only. For horizontal scaling, add a Redis message queue and move the presence store out of process memory.

---

## 🧪 Testing

```bash
python test_import.py                # import smoke check
python scripts/test_turso_adapter.py # 34 checks — local + Turso backend compatibility
python scripts/test_recommendations.py  # manual recommendation check
```

`scripts/test_turso_adapter.py` covers the backend layer: that local SQLite mode is unchanged,
that `row['column']` access works over the Turso driver, `rowcount`/`lastrowid` accuracy,
`fetchone`/`fetchall` semantics, NULL handling, parameterised queries, and that the admin SQL
dump restores to a byte-equivalent database.

A full unit-test suite for the app itself is still the biggest gap — see [`docs/Tasks.md`](docs/Tasks.md) §9 for the planned coverage matrix (auth flows, authorisation boundaries, connection lifecycle, recommendation cold start, messaging locks, upload rejection, OTP-leak assertions).

---

## 🗺️ Roadmap

**Recommendation intelligence**
- Weighted ensemble scoring — `α × ML_score + (1 − α) × rule_score`
- Matrix factorization (SVD / ALS) for implicit feedback at scale
- Graph Neural Network embeddings on the social graph
- Incremental retraining on new interaction events
- A/B testing harness comparing rule-only vs ML-only vs hybrid
- Semantic job matching between student bio and job description
- Offline evaluation harness — precision@k, recall@k, NDCG

**Platform**
- PostgreSQL migration for multi-instance deployment
- Redis message queue for horizontally scaled WebSockets
- Object storage for user uploads
- Full-text search (SQLite FTS5) replacing `LIKE` queries
- Push notifications and a PWA shell
- Two-factor authentication and rate limiting

**Product depth**
- Mentorship request workflow with session slots and feedback
- Event creation, capacity limits and RSVP
- Announcement targeting by role, department or batch
- Social feed (posts / comments / likes)
- Department and batch-based groups
- Dark mode
- Accessibility audit to WCAG 2.1 AA

---

## 🐛 Known Issues

Documented honestly, because a README that claims perfection is less useful than one that tells you where the edges are.

| # | Issue | Location | Severity |
| --- | --- | --- | --- |
| 1 | ~~Two DB factories resolve to different files~~ — **fixed**, messaging now shares the main factory | `database/messaging_db.py` | Resolved |
| 2 | `url_for('faculty_dashboard')` — the endpoint is actually named `dashboard_faculty`, so a faculty job post 500s | `app.py:4616` | **High** |
| 3 | A Gmail app password is hard-coded as the fallback, and the seeded admin password is in repo history | `app.py:50`, `app.py:575-577` | **High** |
| 4 | No automated unit-test suite — the Turso adapter has tests, the app does not | `test_import.py` | **High** |
| 5 | `pywhatkit` is imported **before** the admin role check, so non-admins trigger a heavy import before rejection | `app.py:3475-3476` | Medium |
| 6 | `GET /api/messages/private/<conversation_id>` returns a hard-coded placeholder — the endpoint is non-functional | `routes/messaging_routes.py:201-217` | Medium |
| 7 | Several POST handlers flash `str(e)` to the user, leaking internal detail | `app.py:1050, 1188, 1911, 2092` | Medium |
| 8 | Connection-request logic is implemented twice (in `app.py` and in the `connection_bp` blueprint), with divergent parameter names | `app.py:3809` vs `routes/connection_routes.py:11` | Medium |
| 9 | ML and rule scores share one `score` field, so the hybrid sort mixes two different scales | `services/recommendation_engine.py:432` | Medium |
| 10 | The ML model trains once at startup and never refreshes automatically | `services/recommendation_engine.py:481-489` | Medium |
| 11 | On Turso, every query is an HTTP round trip — admin dashboard and ML engine get noticeably slower | `db_utils.py` | Medium |
| 12 | `static/uploads/` is ephemeral on serverless hosts even with Turso | `app.py:68-73` | Medium |
| 13 | `app.py` is 4,875 lines with 99 routes and a 17-event WebSocket handler | `app.py` | Low |
| 14 | Online presence is stored in process memory, so it is wrong behind multiple workers | `routes/websocket_routes.py:26-79` | Low |
| 15 | The design-token stylesheet is not loaded globally; tokens are duplicated inline in several templates | `static/css/theme.css` | Low |
| 16 | `.gitignore` covers `.env` but **not** `*.db` or `static/uploads/` — real accounts and uploads are tracked | `.gitignore` | **High** |

> ⚠️ **Before publishing this repository:** the working tree currently contains live SQLite files
> (`data/college_pro.db` with real user rows, plus stale copies at the repo root) and user uploads.
> Strip or untrack them first — see [`docs/Rules.md`](docs/Rules.md) GIT-4.
>
> ```gitignore
> # add these
> *.db
> data/*.db
> static/uploads/profile_pics/
> static/uploads/logos/
> ```

Full analysis with code locations: [`docs/Memory.md`](docs/Memory.md) §9 · [`docs/Rules.md`](docs/Rules.md) §14 · P0 fix list in [`docs/Tasks.md`](docs/Tasks.md) §9

---

## 🤝 Contributing

Contributions are welcome.

1. **Fork** the repository
2. **Create a branch** — `git checkout -b feature/your-feature`
3. **Follow the project rules** in [`docs/Rules.md`](docs/Rules.md) — especially the connection-lifecycle pattern, the parameterised-SQL rule, and the design-token guidance
4. **Add or update tests** for any behaviour change
5. **Update the docs** — if you change architecture, scoring, or the schema, update the corresponding file in `docs/`
6. **Open a pull request** with a clear description of what changed and why

### Commit convention

```
feat: add job application tracking endpoint
fix: close db connection in private_chat
perf: collapse admin dashboard counts into one GROUP BY
docs: document the hybrid recommendation strategy
```

### Code of conduct

Be respectful. This is a community project — assume good intent in issues and reviews.

---

## 📄 License

Released under the **MIT License**.

```
MIT License

Copyright (c) 2026 Alumni Hub

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📚 Documentation

The full documentation set lives in [`docs/`](docs):

| Document | Read it for |
| --- | --- |
| [`docs/PRD.md`](docs/PRD.md) | Product requirements, role capabilities, functional + non-functional requirements, success metrics, out-of-scope |
| [`docs/Architecture.md`](docs/Architecture.md) | Layered design, startup sequence, DB access patterns, frontend layers, email, deployment, refactor path |
| [`docs/Rules.md`](docs/Rules.md) | Coding, database, security and data-handling rules — plus which ones the code currently violates |
| [`docs/Design.md`](docs/Design.md) | Design tokens, component patterns, per-page inventory, motion rules, accessibility checklist |
| [`docs/Tasks.md`](docs/Tasks.md) | Phase-by-phase task breakdown, testing coverage matrix, P0 blockers, effort estimates |
| [`docs/Memory.md`](docs/Memory.md) | Durable project knowledge: decisions, schema drift, verified bugs, open questions |

**Start here:** PRD → Architecture → Tasks §9 (testing gap) → Known Issues (above).

---

## 👥 Credits

Built with 💙 by the **Alumni Hub team**.

- **Team photography** — [`static/images/team/`](static/images/team)

### Built with

Flask · Flask-SocketIO · Flask-Login · SQLite · scikit-learn · NumPy · Bootstrap 5 · FontAwesome · AOS · Chart.js · Socket.IO · Vanilla Tilt

---

<div align="center">

**Alumni Hub** — Building Connections, Creating Opportunities

[⬆ Back to Top](#-alumni-hub)

</div>
