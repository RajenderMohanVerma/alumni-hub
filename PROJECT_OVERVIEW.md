# 🎓 ALUMNI HUB — Comprehensive Project Master Overview

> **Version:** 1.0 (Production-Ready Academic Release)  
> **Type:** Academic Major Project (MCA — Master of Computer Applications)  
> **Brand & Mission:** *"Connecting Generations — Building Connections, Creating Opportunities"*  
> **Core Architecture:** Monolithic Flask Core + Modular Domain Blueprints + Event-Driven Socket.IO + SQLite (WAL Mode) + Scikit-Learn Hybrid Recommendation Engine  
> **Primary Live Target:** `alumnihub.com` / PythonAnywhere / Vercel Serverless  
> **Last Updated:** November 2026

---

## 📑 Table of Contents

1. [Executive Summary & Project Identity](#1-executive-summary--project-identity)
2. [High-Level System Architecture](#2-high-level-system-architecture)
3. [Database Architecture & Schema Reference](#3-database-architecture--schema-reference)
4. [Authentication, Security & Session Management](#4-authentication-security--session-management)
5. [User Roles & Comprehensive Workflow Maps](#5-user-roles--comprehensive-workflow-maps)
6. [Recommendation Engine (Rule-Based + Collaborative Filtering)](#6-recommendation-engine-rule-based--collaborative-filtering)
7. [Real-Time WebSocket & Messaging Engine](#7-real-time-websocket--messaging-engine)
8. [Career Hub, Placements & Opportunity Lifecycle](#8-career-hub-placements--opportunity-lifecycle)
9. [UI/UX Design System, Theming & Mobile Navigation Architecture](#9-uiux-design-system-theming--mobile-navigation-architecture)
10. [Full Route & API Catalog](#10-full-route--api-catalog)
11. [Configuration, Deployment & Maintenance Toolkit](#11-configuration-deployment--maintenance-toolkit)
12. [Recent Overhauls & Delivered Milestones (Phase 5)](#12-recent-overhauls--delivered-milestones-phase-5)
13. [Engineering Rules, Known Debt & System Invariants](#13-engineering-rules-known-debt--system-invariants)
14. [Future Roadmap & Scaling Strategy](#14-future-roadmap--scaling-strategy)

---

## 1. Executive Summary & Project Identity

### 1.1 The Core Problem
Higher education institutions routinely lose contact with their graduates the day they leave campus. Traditional methods fail due to:
- Static, obsolete alumni email spreadsheets maintained manually by placement cells.
- Fragmented unofficial WhatsApp groups that lack privacy, verification, and persistence.
- Students having zero structured access to verified alumni industry insights, resume critiques, or direct job referrals.
- Faculty mentors and administrators possessing no automated real-time telemetry over alumni career trajectories or placement success metrics.

### 1.2 The Alumni Hub Solution
**Alumni Hub** is a multi-tenant, role-aware institutional ecosystem designed to bridge students, alumni, faculty, and administrators into an interactive professional circle. It combines:
1. **Instagram-Style Social Graph:** Bidirectional follow/connect invitations, profile discovery, and activity signals.
2. **Real-Time Communication:** End-to-end WebSocket chat (direct 1-on-1 dialogue with typing indicators and soft-delete safeguards, plus global community chat).
3. **ML-Powered Networking:** A scikit-learn collaborative filtering engine coupled with rule-based heuristics that recommends alumni mentors and peer scholars based on skill overlap, department alignment, and graduation recency.
4. **Moderated Opportunity Desk:** A 30+ field career pipeline where alumni and faculty submit verified openings, administrators review and approve them, and students apply directly or connect with referrers.
5. **Mobile-First Glassmorphism UI:** Responsive layout with role-adaptive themes (Emerald for Faculty, Sky/Navy for Students, Amber for Alumni, Indigo for Admins) featuring persistent sticky mobile chrome and zero-shift layout locks.

### 1.3 Project Identity & Metadata
| Property | Value | Notes |
| :--- | :--- | :--- |
| **System Name** | **Alumni Hub** | Academic / Enterprise Alumni Management Network |
| **Target Institution** | Institution-Neutral College Campus | Configurable branding, logo, and departmental trees |
| **Release Version** | **1.0** (with Phase 5 UX Overhauls) | Fully tested and verified production release |
| **Technology Stack** | Python 3.7+ / Flask 2.3.2 / SQLite (WAL) | Lightweight, single-process, zero-external-DB dependency |
| **Lead Developer** | Rajender Mohan Verma (MCA) | Architecture, Backend, Frontend & ML Pipelines |
| **Collaborators** | Team Alumni Hub | Core module testing, data validation, and asset curation |
| **Primary Theme Colors** | Deep Navy (`#1e3a8a`) & Sky (`#0ea5e9`) | Accented with Amber (`#f59e0b`) and Emerald (`#10b981`) |

---

## 2. High-Level System Architecture

### 2.1 Architectural Pattern
The application follows a **Monolithic Core with Modular Domain Blueprints** (Hybrid MVC). While `app.py` historically anchors the core routing, initialization, and error handling, four specialized domain Blueprints and auxiliary services modularize complex operations:

```
                                  [ Browser / Client ]
                                            │
                             ┌──────────────┴──────────────┐
                             ▼                             ▼
                    HTTP / HTTPS Requests          WebSocket Connections
                    (REST & Jinja Pages)         (Flask-SocketIO / Engine.IO)
                             │                             │
                             ▼                             ▼
                     [ WSGI Gateway ]               [ WSGI Gateway ]
                  (Gunicorn / Vercel WSGI)       (Gunicorn Eventlet/Gevent)
                             │                             │
                             └──────────────┬──────────────┘
                                            ▼
                                    [ Flask Core App ]
                                       (app.py: 4,875 LOC)
                                            │
     ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
     ▼                  ▼                   ▼                   ▼                  ▼
[ Auth & Sessions ] [ Domain Blueprints ] [ ML Engine ]   [ WebSocket Hub ]  [ Email System ]
Flask-Login / OTP   - messaging_routes   recommendation_   websocket_routes  SMTP SSL (Gmail)
Centralized Rules   - connection_routes      engine        Rooms & Broadcast  Background Worker
                    - recommendation_r.     (SciKit)
                    - social_routes
     │                  │                   │                   │                  │
     └──────────────────┴───────────────────┼───────────────────┴──────────────────┘
                                            ▼
                               [ Data Persistence Layer ]
                                SQLite 3 (WAL Mode Enabled)
                              ┌─────────────┴─────────────┐
                              ▼                           ▼
                     [ college_pro.db ]          [ college_pro.db ]
                   (data/college_pro.db)         (Root: Messaging DB)
```

### 2.2 Component Directory Breakdown
```
alumni-hub/
├── app.py                      # Master monolithic core (routes, auth, models, startup)
├── config.py                   # Environment-driven configuration (Dev, Test, Prod)
├── db_utils.py                 # Thread-safe SQLite connection factory with Row factories
├── extensions.py               # Shared extension singletons (SocketIO, Mail, LoginManager)
├── requirements.txt            # Explicit dependency pins
├── Procfile                    # Production process definition (gunicorn app:app)
├── vercel.json                 # Vercel serverless deployment & routing rewrite rules
│
├── routes/                     # Domain-specific route controllers (Blueprints)
│   ├── connection_routes.py    # Follow/connect, accept, reject, withdraw actions
│   ├── messaging_routes.py     # 1-on-1 conversations, unread counters, chat history
│   ├── recommendation_routes.py# Recommended peers and mentors API endpoints
│   ├── social_routes.py        # Social feeds, posts, likes, and comment interactions
│   └── websocket_routes.py     # Socket.IO event handlers, real-time message routing
│
├── services/                   # Business logic and computation engines
│   ├── admin_service.py        # Analytics aggregation, user state governance
│   ├── profile_service.py      # Profile completeness, schema mutation helpers
│   └── recommendation_engine.py# Hybrid Collaborative Filtering + Scikit ML Model
│
├── models/                     # Data transfer objects and schema representation
│   └── recommendation.py       # Recommendation data structures and scoring models
│
├── database/                   # Secondary database factories
│   └── messaging_db.py         # Dedicated messaging storage factory & queries
│
├── data/                       # Live database directory
│   ├── college_pro.db          # Active production database file
│   └── uploads/                # User profile avatars, job attachments, and resumes
│
├── static/                     # Static presentation assets
│   ├── css/                    # 13 scoped stylesheets (navbar, theme, cards, chat)
│   ├── js/                     # Client runtime scripts (Socket.IO client, pwa, search)
│   └── images/                 # App logo, default avatars, empty-state illustrations
│
├── templates/                  # 90+ Jinja2 HTML templates partitioned by audience
│   ├── base.html               # Global master skeleton with responsive chrome & drawers
│   ├── admin/                  # Administrative control consoles and audit tables
│   ├── alumni/                 # Alumni dashboard, spotlight showcase, giving-back desk
│   ├── auth/                   # Login, multi-step OTP signup, password recovery
│   ├── common/                 # Public landing, about, contact, event listings
│   ├── emails/                 # HTML email templates (OTP, invites, alerts)
│   ├── faculty/                # Faculty command console, academic networks, dashboard
│   ├── messaging/              # Real-time dual-pane messenger and room interfaces
│   └── student/                # Student dashboard, network explorer, job applications
│
├── docs/                       # Technical specifications and maintenance manuals
│   ├── Architecture.md         # In-depth architectural blueprint
│   ├── Design.md               # Visual design system, color tokens, and layout guidelines
│   ├── Memory.md               # Durable engineering invariants and decision rationale
│   ├── PRD.md                  # Detailed Product Requirements Document
│   ├── Rules.md                # Non-negotiable security, database, and style guidelines
│   └── Tasks.md                # Project work breakdown and historical phase snapshots
│
└── scripts/                    # 20+ automated maintenance, migration, and test scripts
```

### 2.3 Application Startup Sequence
1. **Environment Load:** `python-dotenv` parses `.env` before any imports execute (`config.py:4`).
2. **Configuration Binding:** `app.config.from_object(config_by_name[env])` loads session timeouts, cryptographic keys, and database paths.
3. **Extension Initialization:** `login_manager.init_app(app)`, `socketio.init_app(app, cors_allowed_origins="*")`, and `mail.init_app(app)`.
4. **Database Initialization:** `init_db()` runs automatically at module level on launch (`app.py:4861`), executing DDL statements for 20 tables and 26 indexes with `CREATE TABLE IF NOT EXISTS` idempotency.
5. **Blueprint Registration:** `messaging_bp`, `connection_bp`, `recommendation_bp`, and `social_bp` mount under their designated URL prefixes.
6. **Background Scheduling:** `APScheduler` initializes periodic cleanup tasks (expiring dormant OTPs and invalidating stale password tokens).

---

## 3. Database Architecture & Schema Reference

### 3.1 Dual-Factory Connection Model
Alumni Hub utilizes two distinct connection factories for operational stability:

```
                   ┌────────────────────────────────────────────────────────┐
                   │               Flask Application Context                │
                   └───────────────────────────┬────────────────────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
     [ db_utils.get_db_connection() ]             [ database.messaging_db.get_db_connection() ]
                       │                                               │
              Resolves dynamic path:                          Resolves explicit path:
       current_app.config['DB_NAME']                        'college_pro.db' in repo root
        → data/college_pro.db                                          │
                       │                                               │
                       ▼                                               ▼
         [ Main Relational Storage ]                    [ Messaging Isolated Storage ]
        (Users, Jobs, Networks, Events)                (Direct Messages, Conversations)
```

**SQLite Pragmas Applied on Every Connection:**
- `PRAGMA foreign_keys = ON;` (Enforces referential integrity on cascading deletes).
- `PRAGMA journal_mode = WAL;` (Write-Ahead Logging allows concurrent reads alongside active writes).
- `PRAGMA synchronous = NORMAL;` (Maximizes write throughput while preserving ACID boundaries).
- `conn.row_factory = sqlite3.Row;` (Provides column-name dictionary indexing on result sets).

### 3.2 Master Relational Tables (20 Entities)
| # | Table Name | Purpose | Key Foreign Keys & Constraints |
| :--- | :--- | :--- | :--- |
| 1 | `users` | Core identity & credentials | Unique email, role discriminator (`student`, `alumni`, `faculty`, `admin`) |
| 2 | `profiles` | Extended profile for students/alumni | `user_id` → `users(id)` ON DELETE CASCADE |
| 3 | `faculty_profiles` | Dedicated academic credentials for faculty | `user_id` → `users(id)` ON DELETE CASCADE |
| 4 | `connections` | Instagram-style social graph links | `sender_id`, `receiver_id` → `users(id)`, status (`pending`, `accepted`, `rejected`) |
| 5 | `conversations` | Dual-user messaging thread headers | `user1_id`, `user2_id` → `users(id)`, unique pair index |
| 6 | `messages` | Individual 1-on-1 chat logs | `conversation_id`, `sender_id`; contains `is_read`, `deleted_by_*` |
| 7 | `jobs` | Job board & placement postings | `posted_by` → `users(id)`, status (`pending`, `approved`, `rejected`) |
| 8 | `job_applications` | Student opportunity applications | `job_id` → `jobs(id)`, `user_id` → `users(id)` |
| 9 | `events` | Campus reunions, meets & seminars | `organizer_id` → `users(id)`, timestamps, venue coordinates |
| 10 | `event_rsvps` | Event attendance registration | `event_id` → `events(id)`, `user_id` → `users(id)` |
| 11 | `mentorship_requests`| Formal student-alumni mentorship | `student_id`, `alumni_id` → `users(id)`, goals, meeting notes |
| 12 | `announcements` | Circulars & official broadcasts | `author_id` → `users(id)`, target audience discriminator |
| 13 | `notifications` | Real-time user alert feed | `user_id` → `users(id)`, action URL, read receipt boolean |
| 14 | `password_resets` | Single-use recovery tokens | `user_id` → `users(id)`, 10-minute validity expiry |
| 15 | `email_verifications`| Staged signup OTP registry | Unique email, 6-digit cryptographic code, 2-minute TTL |
| 16 | `recommendations` | Cached ML-generated peer pairings | `user_id`, `recommended_id` → `users(id)`, float match score |
| 17 | `feed_posts` | Community bulletin board posts | `author_id` → `users(id)`, textual body, media path |
| 18 | `post_comments` | Discussion threads on feed posts | `post_id` → `feed_posts(id)`, `author_id` → `users(id)` |
| 19 | `post_likes` | Upvotes & appreciation signals | `post_id` → `feed_posts(id)`, `user_id` → `users(id)` |
| 20 | `admin_audit_logs` | Security and moderation log | `admin_id` → `users(id)`, action timestamp, target entity, IP |

---

## 4. Authentication, Security & Session Management

```
                                  [ Registration Workflow ]
                                             │
                                     Enter Valid Gmail
                                             │
                                             ▼
                             Generate Cryptographic 6-Digit OTP
                                (2-Minute In-Memory TTL)
                                             │
                                             ▼
                             Transmit via TLS Email (Flask-Mail)
                                             │
                                             ▼
                                     User Submits OTP
                                             │
                             ┌───────────────┴───────────────┐
                             ▼                               ▼
                      [ OTP Invalid ]                 [ OTP Valid ]
                   Flash Error & Re-enter                    │
                                                             ▼
                                                Execute Password Policy
                                               (8+ Chars, High Entropy)
                                                             │
                                                             ▼
                                                  Hash with Werkzeug SHA-256
                                                             │
                                                             ▼
                                                 Create User Entity in DB
                                                             │
                                  ┌──────────────────────────┴──────────────────────────┐
                                  ▼                                                     ▼
                         [ Role: Student ]                                   [ Role: Alumni / Faculty ]
                       Immediate Active State                                Locked: Pending Admin Approval
                     Redirect to Profile Wizard                            Display Gate Screen until Verified
```

### 4.1 Staged Registration Security
- **Email Validation:** Account creation is restricted to verified email domains.
- **Pre-Registration Sandbox:** Registration entries stay in temporary storage; the record is committed to `users` **only after** OTP confirmation.
- **Cryptographic OTPs:** Generated via `secrets.randbelow()` (not pseudo-random `random.randint`), hashed or scrubbed post-validation.
- **Anti-Brute Force:** Staged OTP verification allows a maximum of 3 failed attempts before invalidating the transaction.

### 4.2 Authentication & Password Safeguards
- **Password Hashes:** Computed via `werkzeug.security.generate_password_hash` utilizing PBKDF2 with SHA-256 and salted iterations. Plaintext passwords never touch database logs or debug printouts.
- **Centralized Password Policy:** A uniform validator enforces minimum 8 characters across registration, profile settings, and password recovery (`app.py:1260`).
- **Session Protection:** Session cookies are configured with `HttpOnly=True`, `SameSite='Lax'`, and `Secure=True` in production environments, mitigating XSS session hijacking.

### 4.3 Authorization & Role Enforcement
Every endpoint enforces authorization through two defensive rings:
1. **Ring 1 — Identity:** `@login_required` confirms an active authenticated session.
2. **Ring 2 — Capability:** Explicit programmatic role assertions (`if current_user.role != 'faculty': abort(403)`).
3. **Ownership Verification:** Dynamic entities (editing user profiles, removing jobs, viewing private messages) verify that the requesting user's ID matches the resource's `user_id` or possesses administrative status.

---

## 5. User Roles & Comprehensive Workflow Maps

```
                          ┌─────────────────────────────────────┐
                          │         ALUMNI HUB PLATFORM         │
                          └──────────────────┬──────────────────┘
                                             │
         ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
         ▼                   ▼                               ▼                   ▼
    🎓 STUDENT           🎮 ALUMNI                       👨‍🏫 FACULTY          🛡️ ADMIN
 • Academic Networks  • Career Mentorship             • Faculty Console   • User Governance
 • Peer Connections   • Job Board Submissions         • Academic Networks • Job Moderation
 • Resume Uplink      • Spotlight Profiles            • Event Spotlight   • Live Broadcasts
 • Opportunity Board  • Campus Meets & RSVPs          • Student Roster    • System Telemetry
 • Direct Messenger   • Student Dialogue              • Direct Messaging  • Security Audits
```

### 5.1 Student Journey
- **Dashboard (`/student/dashboard`):** Real-time analytics displaying connection tallies, profile completeness gauge, upcoming campus events, and AI-suggested mentors.
- **Networks (`/network`):** Discover departmental peers, seniors, and professors. Features 12 cards per page with directional arrow pagination, instant keyword search, and an active filter between "All Campus Network" and "My Connections".
- **Mentorship (`/mentorship`):** Direct booking workflow with verified alumni working in top-tier tech companies.
- **Career Hub (`/jobs`):** Browse verified job and internship openings with salary bands, required skill stacks, and 1-click external application or referrer connection.

### 5.2 Alumni Journey
- **Dashboard (`/alumni/dashboard`):** Metric command center showing student mentorship requests, campus reunion invitations, and posted job applicant tallies.
- **Post Job / Referral (`/post-job`):** Form interface allowing alumni to publish vacancies in their organizations with eligibility requirements and internal referral links.
- **Alumni Spotlight (`/alumni/spotlight`):** Showcase portfolio displaying career milestones, startup founding journeys, and notable institutional achievements.

### 5.3 Faculty Journey
- **Command Console (`/faculty/dashboard`):** Real-time academic analytics tracking student counts across BCA, MCA, and Engineering, quick placement metrics, and a 9-item paginated departmental roster.
- **Academic Networks (`/network`):** Faculty view showing interconnected student scholars and alumni colleagues.
- **Campus Events Spotlight:** Dedicated events management and visibility desk for department seminars, guest lectures, and tech workshops.
- **Student Mentoring & Messages:** Direct messaging channels with students requesting career guidance, thesis mentorship, or institutional recommendations.

### 5.4 Administrator Journey
- **Governance Console (`/admin/dashboard`):** High-altitude telemetry showing user distributions, active WebSocket connections, system logs, and security alarms.
- **User Approval Matrix (`/admin/users`):** Verify credentials of registering alumni and faculty before releasing system capabilities. Ability to suspend or purge offending accounts.
- **Job Approval Queue (`/admin/jobs`):** Multi-stage moderation desk reviewing submitted vacancies before public listing.
- **Broadcast System (`/admin/broadcast`):** Instant system announcements and WhatsApp deep-link notifications sent to selected student batches.

---

## 6. Recommendation Engine (Rule-Based + Collaborative Filtering)

### 6.1 Architectural Workflow
The recommendation subsystem (`services/recommendation_engine.py`) operates as a hybrid pipeline combining heuristic rules with statistical machine learning:

```
                            [ Candidate Corpus (Users) ]
                                         │
                                         ▼
                           [ Level 1: Hard Heuristic Filter ]
                           - Exclude current user & existing connections
                           - Filter out pending incoming/outgoing invites
                           - Filter out blocked or suspended users
                                         │
                                         ▼
                        [ Level 2: Scikit-Learn TF-IDF Vectorizer ]
                       - Extract normalized token vectors from Skills
                       - Compute Pairwise Cosine Similarity:
                              cos(θ) = (A · B) / (||A|| ||B||)
                                         │
                                         ▼
                          [ Level 3: Weighted Rule Scorer ]
                       ┌─────────────────────────────────────┐
                       │ Score Factor             Weight     │
                       ├─────────────────────────────────────┤
                       │ Cosine Skill Match       40%        │
                       │ Department Matching      25%        │
                       │ Batch Proximity          20%        │
                       │ Mutual Connections       15%        │
                       └─────────────────────────────────────┘
                                         │
                                         ▼
                        [ Level 4: Top-K Ranking & Serialization ]
                       - Sort candidate matches in descending order
                       - Cache in thread-safe memory (_model_cache)
                       - Return Top 5 - 10 recommendations to UI
```

### 6.2 Model Lifecycle & Concurrency
- **Thread Safety:** Model training and cache invalidation are synchronized through a `threading.Lock()` instance, preventing race conditions during concurrent user logins.
- **Cold-Start Resilience:** If a new user possesses zero skill tags and no connections, the engine gracefully falls back to department-level batch recency, returning active scholars rather than empty states.
- **Cache Persistence:** The trained TF-IDF matrix resides in memory, invalidating only when an authenticated user modifies their profile skills or establishes a new connection.

---

## 7. Real-Time WebSocket & Messaging Engine

### 7.1 WebSocket Topography (`routes/websocket_routes.py`)
Powered by Flask-SocketIO with Engine.IO protocol negotiation, the real-time hub manages 15 incoming event listeners and 27 outgoing broadcast emitters:

```
                                [ Socket.IO Gateway ]
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
    [ Room: user_<id> ]           [ Room: public_chat ]         [ Room: admin_monitor ]
  - Direct 1-on-1 Messages      - Global Community Dialogue   - Real-Time Connection Watch
  - Live Typing Indicators      - Public Announcements        - System Telemetry & Logs
  - Read Receipt Confirmations  - Active Member Presence      - Security Violation Alerts
  - Friend Request Alerts
```

### 7.2 Message Lifecycle & Soft-Delete Architecture
1. **Transmission:** Sender emits `send_private_message` payload with recipient ID and ciphertext body.
2. **Authentication:** Server extracts session credentials; rejects payload if `current_user` is unauthenticated.
3. **Storage:** Record is committed to `messages` via `database/messaging_db.py`.
4. **Relay:** Message is emitted exclusively to the target's dedicated private room `user_<recipient_id>`.
5. **Soft-Delete Governance:** Messages implement dual-flag soft-deletion (`deleted_by_sender`, `deleted_by_recipient`). A record is physically purged from disk only when **both** participants execute a delete operation.

---

## 8. Career Hub, Placements & Opportunity Lifecycle

### 8.1 30+ Field Enterprise Schema
Every job opportunity (`jobs` table) captures comprehensive operational data:
- **Core Metadata:** Title, Company Name, Industry Sector, Job Role, Employment Type (Full-time, Internship, Remote, Hybrid).
- **Compensation:** Exact CTC / Stipend figures, Currency, Perks, Signing Bonus indicators.
- **Eligibility:** Eligible Courses (BCA, MCA, B.Tech), Passing Batches (e.g. 2024, 2025, 2026), Minimum CGPA cutoff, Active Backlog tolerance.
- **Requisites:** Mandatory skills list, Experience required (in years), Job Description (rich text), Application Deadline.
- **Action Triggers:** Direct URL, HR Contact Email, Alumni Referrer Badge (`posted_by`).

### 8.2 Moderation Pipeline
```
  [ Alumni / Faculty Posts Job ]
                 │
                 ▼
       Status: `pending` ───────────► [ Hidden from Public Student View ]
                 │
                 ▼
   [ Admin Reviews in Queue ]
                 │
        ┌────────┴────────┐
        ▼                 ▼
   [ Approved ]      [ Rejected ]
        │                 │
        ▼                 ▼
 Status: `approved`    Status: `rejected`
 Visible on Board      Archived with Reason
 Email Sent to Submitter
 WhatsApp Broadcast Triggered
```

---

## 9. UI/UX Design System, Theming & Mobile Navigation Architecture

### 9.1 Visual Design Tokens
Source: `static/css/theme.css` & `static/css/navbar-professional.css`.

| Token / Element | Design Specification | Usage |
| :--- | :--- | :--- |
| **Primary Navy** | `#1e3a8a` / `linear-gradient(135deg, #1e3a8a, #0ea5e9)` | Desktop headers, primary action CTAs |
| **Faculty Emerald** | `#021a12` (Base), `#047857` (Surface), `#34d399` (Accent) | Faculty console, mobile drawer, badge tags |
| **Alumni Amber** | `#d97706` / `#f59e0b` | Giving back CTAs, referral stars, badges |
| **Student Sky** | `#0284c7` / `#38bdf8` | Scholar tags, learning paths, discovery |
| **Glassmorphism** | `background: rgba(255,255,255,0.92); backdrop-filter: blur(16px)` | Floating navbar, metric cards, modal dialogs |
| **Border Radii** | `12px` (Buttons), `16px` (Cards), `24px` (Pills/Drawers) | Modern fluid curvature |

### 9.2 Mobile Navigation Drawer Architecture
Following user feedback and mobile testing, the mobile navigation drawer was overhauled to eliminate design flaws:

```
┌────────────────────────────────────────────────────────┐
│ [Logo] ALUMNI HUB   [Role: FACULTY]                [✕] │ ◄── Sticky Topbar (position: sticky; top: 0)
├────────────────────────────────────────────────────────┤     Stationary Close Button (Never scrolls away)
│ ┌────────────────────────────────────────────────────┐ │
│ │ [DK] Dr. Manjot Kaur                               │ │ ◄── Coordinate-Locked Avatar (56px x 56px)
│ │      Information Technology • Academic Guide       │ │     Single element (Zero layout shifts)
│ ├────────────────────────────────────────────────────┤ │
│ │ [Dashboard]  [Networks]  [Post Job]  [Messages]    │ │ ◄── 4 Quick-Action Floating Tiles
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ ▼ ACADEMIC WORKSPACE                                   │
│   • Faculty Dashboard                                │ │
│   • Academic Networks (Connected Scholars & Peers)   │ │
│   • Connection Requests                              │ │
│                                                        │
│ ▼ PLACEMENTS & OPPORTUNITIES                           │
│   • Post Job / Referral                              │ │
│   • Browse Opportunities                             │ │
│   • Campus Events & Meets                            │ │
│                                                        │
│ ▼ COMMUNICATIONS & REPORTS                             │
│   • Direct Messages Inbox                            │ │
│   • Campus Announcements                             │ │
│   • Academic Reports & Stats                         │ │
│                                                        │
│ ▼ FACULTY CONFIGURATION                                │
│   • Edit Faculty Profile                             │ │
│   • Change Password                                  │ │
│   • Sign Out                                         │ │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 📅 CAMPUS EVENTS SPOTLIGHT                         │ │ ◄── Redesigned Emerald Spotlight Card
│ │ Academic Meets, Conferences & Reunions             │ │     (Replaces stray un-styled white box)
│ │ [ Explore All Campus Events → ]                    │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 📥 Download Alumni Hub App (PWA)         [Install] │ │ ◄── Themed Dark Emerald PWA Banner
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

**Key Mobile Engineering Fixes Delivered:**
1. **Containing Block Trap Eliminated:** Elements inside containers with CSS `backdrop-filter: blur(28px)` lose window-relative `position: fixed`. The close button was redesigned into `.mobile-drawer-topbar` with `position: sticky; top: 0; z-index: 100005`, guaranteeing it stays fixed and clickable at all times.
2. **Avatar Coordinate Lock:** Rendered avatars use `position: absolute; top: 0; left: 0; 56px x 56px`, conditioning out duplicate image/initial stacks and preventing button overlap.
3. **Events Spotlight Card:** Replaced an isolated, un-themed white button with an emerald glassmorphism feature banner accented with purple glow, live schedule indicator, and directional arrow.

---

## 10. Full Route & API Catalog

### 10.1 Web Navigation & Controller Routes (`app.py`)
| Endpoint / URL | HTTP Methods | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `/` | GET | Public | Dynamic landing page with counters, spotlight, and features |
| `/login` | GET, POST | Public | User authentication endpoint with role dashboard routing |
| `/register` | GET, POST | Public | Multi-step OTP registration gate for Gmail accounts |
| `/verify_otp` | GET, POST | Public | Cryptographic 6-digit OTP verification endpoint |
| `/logout` | GET | Authenticated | Invalidates session cookie, purges server cache, redirects |
| `/forgot_password` | GET, POST | Public | Single-use password reset OTP generation |
| `/student/dashboard` | GET | Student | Student analytics, mentor suggestions, event roster |
| `/alumni/dashboard` | GET | Alumni | Alumni giving-back desk, mentorship queue, job manager |
| `/faculty/dashboard` | GET | Faculty | Academic analytics, 9-card student roster, quick actions |
| `/admin/dashboard` | GET | Admin | Platform control room, user tables, audit monitors |
| `/network` | GET | Authenticated | **Networks Hub** (12 cards/page, search, scope switcher) |
| `/faculty/network` | GET | Faculty | Alias route to Networks Hub |
| `/directory` | GET | Authenticated | Backward-compatible alias to Networks Hub |
| `/jobs` | GET | Authenticated | Career Hub with filters by course, type, and CTC |
| `/post-job` | GET, POST | Alumni / Faculty | Multi-field job and referral submission portal |
| `/events` | GET | Authenticated | Campus reunions, technical webinars, and schedule RSVPs |
| `/mentorship` | GET, POST | Student / Alumni | Mentorship request booking and confirmation manager |
| `/profile` | GET, POST | Authenticated | View and edit own personal profile, resume, and avatar |

### 10.2 Domain Blueprints
- **Messaging Blueprint (`/messages`):** Handled in `routes/messaging_routes.py`. Loads recent conversation partners, dual-pane message threads, and marks inbound unread signals.
- **Connection Blueprint (`/connections`):** Handled in `routes/connection_routes.py`. Handles `send_request`, `accept_request`, `reject_request`, `cancel_request`, and connection status queries.
- **Recommendation Blueprint (`/recommendations`):** Handled in `routes/recommendation_routes.py`. Serves JSON arrays of scored student and alumni pairings.
- **Social Blueprint (`/social`):** Handled in `routes/social_routes.py`. Renders community feed posts, media uploads, likes, and nested comment trees.

### 10.3 Real-Time WebSocket Events (`routes/websocket_routes.py`)
| Event Name | Direction | Payload | Description |
| :--- | :--- | :--- | :--- |
| `connect` | Inbound | Session Context | Negotiates WebSocket transport; joins user-specific room |
| `disconnect` | Inbound | Session Context | Cleans up active presence; announces offline status |
| `send_private_message`| Inbound | `{recipient_id, message}` | Persists and relays direct 1-on-1 dialogue |
| `new_private_message` | Outbound | `{message_id, sender_id, text, time}` | Delivers incoming message to target's active room |
| `typing_status` | Inbound | `{recipient_id, is_typing}` | Emits real-time typing indicators |
| `typing_indicator` | Outbound | `{sender_id, is_typing}` | Displays typing animation in active chat pane |
| `message_read` | Inbound | `{message_id, sender_id}` | Updates database read state |
| `message_read_receipt`| Outbound | `{message_id}` | Turns checkmarks blue in sender's active window |
| `admin_monitor_stream`| Outbound | `{event_type, payload, timestamp}` | Streams live platform activity to Admin Console |

---

## 11. Configuration, Deployment & Maintenance Toolkit

### 11.1 Environment Configuration (`.env`)
```ini
# Flask Secret & Environment
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=generate-a-strong-hex-key-here-with-secrets-token-hex-32

# Database Configuration
DATABASE_URL=sqlite:///data/college_pro.db
DB_NAME=data/college_pro.db

# Mail Server (TLS)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-institutional-email@gmail.com
MAIL_PASSWORD=your-16-character-app-password
MAIL_DEFAULT_SENDER=your-institutional-email@gmail.com

# System Admin Seed Credentials
ADMIN_EMAIL=admin@alumnihub.local
ADMIN_DEFAULT_PASSWORD=SetSecureInitialPassword123!
```

### 11.2 Production Server Execution
```bash
# Install pinned dependencies
pip install -r requirements.txt

# Run with Gunicorn WSGI Worker (Production)
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app

# Run Local Development Server
python app.py
```

### 11.3 Maintenance & Validation Suite (`scripts/`)
| Script Name | Purpose | Execution |
| :--- | :--- | :--- |
| `init_db.py` | Standalone schema creation and indexing verification | `python scripts/init_db.py` |
| `check_db.py` | Integrity check of tables, foreign key constraints, and user records | `python scripts/check_db.py` |
| `test_email.py` | Verifies SMTP TLS authentication and OTP delivery | `python scripts/test_email.py` |
| `test_recommendations.py`| Validates scikit-learn recommendation scores and output ranks | `python scripts/test_recommendations.py` |
| `optimize_db.py` | Runs `VACUUM`, `ANALYZE`, and WAL checkpoint on SQLite | `python scripts/optimize_db.py` |
| `validate-all.ps1 / .sh` | Automated verification script testing agents, syntax, and templates | `bash scripts/validate-all.sh` |

---

## 12. Recent Overhauls & Delivered Milestones (Phase 5)

During recent design, mobile responsiveness, and naming alignment cycles, the following production enhancements were completed and merged:

1. **Networks Nomenclature Overhaul:**
   - User-facing references across the application were migrated from *"Directory"* to **"Networks"** (`/network`).
   - The interface now reflects mutual connections, professional networks, and scholar circles.
   - Added routing aliases (`@app.route('/faculty/network')`, `@app.route('/directory')`) ensuring zero broken bookmarks.
   - `/network` updated with a 12-item card limit, directional next/prev arrow pagination, and scope switching between "All Campus Network" and "My Connections (Network)".

2. **Sticky Mobile Navigation Chrome:**
   - Overcame CSS containing-block traps caused by parent `backdrop-filter: blur(28px)`.
   - Built `.mobile-drawer-topbar` (`position: sticky; top: 0; z-index: 100005`) ensuring the logo, role badge, and Close (`✕`) button remain visible during deep scrolling.
   - Dynamic theme toggling: High-contrast light mode for general/student users; luxury dark-emerald mode for faculty.

3. **Avatar Coordinate-Lock Architecture:**
   - Eliminated vertical layout stacking collisions where fallback avatars overlapped the "Dashboard" action tile.
   - Child avatars are now coordinate-locked (`position: absolute; top: 0; left: 0; 56px x 56px`), with backend fallback colors assigned by role (`047857` Emerald for Faculty).

4. **Faculty Campus Events Spotlight Banner:**
   - Replaced a detached, plain white button with an emerald glassmorphism feature card (`.faculty-drawer-event-card`).
   - Integrated purple accent glow, live schedule indicator pulse, and clear call-to-action link.
   - Synchronized the PWA installation card with the drawer's dark emerald aesthetic.

5. **Faculty Dashboard Roster Pagination:**
   - Implemented 9-item pagination with live search and previous/next page navigation controls.

---

## 13. Engineering Rules, Known Debt & System Invariants

### 13.1 Non-Negotiable System Invariants
1. **Module-Level Bootstrap:** Blueprint registration (`app.py:4827`) and `init_db()` (`app.py:4861`) **MUST** stay at the module level outside `if __name__ == '__main__'`. Gunicorn and Vercel WSGI loaders require this for startup.
2. **Explicit Connection Teardowns:** Every database connection opened via `get_db_connection()` **MUST** use a `try...finally: conn.close()` block. Leaked SQLite handles cause file locks and concurrency stalls.
3. **Template Inheritance:** Every HTML view **MUST** extend `base.html`. Standalone HTML documents break session banners, CSRF tokens, and navigation drawers.
4. **Zero Plaintext Secrets:** Passwords, OTP tokens, and session secrets must never be logged or echoed in plaintext.

### 13.2 Known Technical Debt
- **Monolithic `app.py`:** At ~4,875 lines, `app.py` contains legacy endpoints alongside modern blueprints. Continued extraction into modular blueprints (e.g. `auth_bp`, `admin_bp`, `jobs_bp`) is recommended.
- **Dual DB Paths:** Messaging uses a hard-coded path to root `college_pro.db`, while the main application targets `data/college_pro.db`. Unifying messaging queries under `data/college_pro.db` is an identified refactor target.
- **Automated Test Coverage:** Smoke tests exist (`test_import.py`), but automated unit testing for edge-case HTTP status codes and concurrent WebSockets should be expanded.

---

## 14. Future Roadmap & Scaling Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ALUMNI HUB FUTURE PHASES                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
[ Phase 6 — Storage & DB ]  [ Phase 7 — ML Scale ]     [ Phase 8 — Mobile PWA ]
• PostgreSQL Migration      • Real-time Retraining     • Offline PWA Caching
• Supabase / Neon Support   • Matrix Factorization     • Web Push Notifications
• AWS S3 / Cloudinary Media • Natural Language Resume  • Native Capacitor Wrap
  Storage for Resumes & Avatars Matcher & Skills Graph • Biometric Quick Login
```

- **Phase 6 — Database Scale:** Transition from SQLite WAL to hosted PostgreSQL (e.g., Supabase or AWS RDS) with connection pooling via PgBouncer. Move user resume uploads from local disk to S3/Cloudflare R2.
- **Phase 7 — Intelligent Matching Engine:** Upgrade the recommendation engine with neural embedding models (e.g., sentence-transformers) to compute semantic similarity between student career aspirations and alumni job descriptions.
- **Phase 8 — Native Mobile Experience:** Package the optimized responsive frontend into a progressive web application (PWA) with native service worker push notifications for incoming connection requests and direct messages.

---

<div align="center">

**Alumni Hub — Connecting Generations, Building Connections, Creating Opportunities**  
*Comprehensive Documentation Catalog: [Architecture.md](docs/Architecture.md) • [Design.md](docs/Design.md) • [Memory.md](docs/Memory.md) • [PRD.md](docs/PRD.md) • [Rules.md](docs/Rules.md) • [Tasks.md](docs/Tasks.md)*

</div>
