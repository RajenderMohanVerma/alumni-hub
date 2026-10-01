# 🎓 Alumni Connection Network App

A comprehensive, professional Flask-based Alumni Management System with modern dynamic UI, real-time messaging, and Instagram-style connection system. Connect students, alumni, and faculty in one unified platform.

---

## 🚀 Recent & Featured Updates (2026)

### 🏗️ Production-Level Architecture Upgrade (v5.0)

Major codebase refactoring and hardening for production readiness:

- **Modular Utilities** (`utils/`): Extracted reusable code into dedicated modules:
  - `decorators.py` — `@role_required()` decorator for role-based access control
  - `helpers.py` — Centralized `generate_otp()`, `save_profile_photo()`, `validate_password()`, `sanitize_html()`, and 6 more helper functions
  - `db.py` — `get_db()` context manager with auto-close/rollback, `query_one()`, `query_all()`, `execute_sql()`
- **Service Layer** (`services/`): Business logic separated from routes:
  - `profile_service.py` — `update_user_profile()`, `ensure_faculty_profile()`
  - `admin_service.py` — Optimized `get_role_counts()` (single GROUP BY), `get_yearly_stats()` (2 queries replace 20+)
- **26+ Bug Fixes**:
  - Fixed `User()` constructor with wrong positional args in login & OTP verification
  - Fixed `false` (Python NameError) → `False` in approve/reject user routes
  - Fixed 8+ broken template paths (missing `auth/`, `common/` prefixes)
  - Fixed OTP leaked to browser via flash messages (3 locations) — now server-logged only
  - Fixed inconsistent password validation (min 6 vs 8) — unified to 8 chars with strength check
  - Added `faculty` role redirect in OTP verification flow
- **Security Hardening**:
  - Role-based access checks added to student & alumni dashboards
  - Private chat now verifies connection before allowing access
  - Error messages no longer leak internal details (`str(e)` → safe messages)
  - Centralized password validation with `validate_password()` (min 8 chars, mixed case, digits)
- **Performance Optimization**:
  - Admin dashboard: 20+ COUNT queries replaced with 2 optimized GROUP BY queries
  - 14 database indexes added for users, connections, profiles, and interactions tables
  - `SELECT *` replaced with `SELECT 1` in existence checks
- **25 DB Connection Leak Fixes**: All routes now use `try/finally` with proper `conn.close()`
  - Fixed: `load_user`, `private_chat`, `alumni_jobs`, `admin_jobs`, `admin_toggle_job`, `admin_delete_job`, `upgrade`, `whatsapp_bridge`, `whatsapp_jump`, `compose_email`, `send_connection_request`, `accept_connection_request`, `reject_connection_request`, `get_connection_status`, `get_pending_connection_requests`
- **Blueprint Registration**: Moved from `if __name__ == '__main__'` to module level — fixes Gunicorn/production deployment
- **Logging**: Added structured `logging` module replacing `print()` statements

### 📧 Real-Time Messaging System

- **Public & Private Chat**: WebSocket-based (Flask-SocketIO) for instant updates.
- **Admin Control**: Global lock/unlock for public messaging with message moderation.
- **1-to-1 Private Chat**: Secure messaging with typing indicators and read receipts.
- **WhatsApp Integration**: Direct "💬 WhatsApp" buttons on profiles for seamless external connection.

### 🧠 Hybrid Recommendation System (Rule-Based + ML Collaborative Filtering)

- **Phase 1 — Rule-Based**: Profile matching via branch, skills, domain, passing year proximity, city, and mutual connections.
- **Phase 2 — ML Collaborative Filtering**: KNN (Cosine Similarity) on a user-interaction matrix built from connections, messages, job applications.
- **Cold Start Handling**: Users with < 2 interactions automatically fall back to rule-based recommendations.
- **Hybrid Engine**: ML results are prioritized; remaining slots filled by rule-based — deduplicated and sorted by score.
- **Performance**: Model trained once at startup (background thread), cached in memory, reused across all requests.
- **Role-Based Suggestions**: Students see Alumni, Alumni see Students.
- **One-Click Connect**: Integration with the connection system directly from recommendation cards.
- **AI Badge**: ML-powered recommendations are visually tagged with an AI badge on dashboard cards.

### 📧 Reliable Communication System

- **Gmail SMTP Integration**: High-reliability email delivery for OTPs and notifications using Gmail App Passwords (`smtp.gmail.com`).
- **Professional OTP Redesign**: Premium glassmorphic verification page with a 2-minute (120s) countdown bar and automatic backspace/focus handling.
- **Smart Registration**: Added conflict resolution for existing email records to prevent `UNIQUE constraint` errors.

### 💼 Career Board & Job Ecosystem (v2.0 Overhaul)

- **Comprehensive Recruitment Tracking**: Added 20+ new professional fields including Work Mode, Eligibility (CGPA/Batch), CTC Range, and Selection Stages.
- **Advanced Admin UI**: Modular 11-section "Add/Edit Job" interface with interactive design and dynamic "Other" field logic.
- **Enhanced Data Management**: Full support for corporate logos, company websites, and automated recruitment lifecycle status (Open/Closed/Expired).
- **Jobs Matrix Dashboard**: High-density management interface for Admins with real-time status toggling and advanced filtering.
- **Recruitment Intel**: Optimized metadata for the Smart Recommendation engine.

### 🎨 UI/UX Excellence

- **Global Responsiveness**: Fully optimized for Laptop, Tablet, and Mobile.
  - Form split layouts stack vertically on small screens.
  - Dashboard grids adapt from multi-column to single-column automatically.
  - Hero sections and font sizes scale gracefully for readability on all devices.
- **High-Performance Counters**: Stabilized numerical counters with persistent `dataset` guards to prevent re-triggering during scroll-up.
- **Toast Notifications**: Interactive notification system in `base.html` with a 5-second auto-dismiss timeout.
- **Premium Aesthetics**: Liquid wave transitions, 3D interactive tilt effects (Tilt.js), and animated mesh backgrounds.
- **Ambient Visuals**: Floating glow orbs, aurora hero effects, and staggered entrance animations.

---

## 🌟 Core Features

### ✨ Multi-Role System

- **Students**: Explore networking, career opportunities, and mentorship.
- **Alumni**: Career tracking, event registration, student mentoring, and industry networking.
- **Faculty**: Academic sharing, guidance, and relationship management.
- **Admin**: Full user management, real-time analytics, and CSV report harvesting.

### 🔗 Connection Request System

- **Instagram-Style**: Send, accept, or reject requests with real-time dashboard updates.
- **Pending Section**: Dedicated area for managing incoming connection requests.

### 🧠 Hybrid Recommendation Engine (Rule-Based + ML)

- **Phase 1 — Rule-Based Scoring**:
  - Same Branch/Department: **+5 Points**
  - Skill Overlap: **+5 Points per matching skill**
  - Same Domain: **+3 Points**
  - Passing Year Proximity: **+4 Points (≤2 yrs)**, **+2 Points (≤4 yrs)**
  - Same City: **+2 Points**
  - Mutual Connections: **+2 Points per mutual**
- **Phase 2 — ML Collaborative Filtering (KNN)**:
  - Builds a user × user interaction matrix from real data
  - Interaction weights: Connection (5), Message (4), Conn Request (3), Job Application (2)
  - KNN with Cosine Similarity finds the most similar users
  - Model trained once, cached globally, reused across requests
- **Cold Start**: Falls back to rule-based when user has < 2 interactions
- **Smart Filtering**: Excludes self, already connected users, and pending requests.
- **Top 5 Limit**: Returns top 5 recommendations with score and reason.

### 📊 Admin Control Center

- **Registration Tracking**: Automatic logging of all user registrations with role-specific meta-data.
- **Advanced Moderation**: Global messaging lock system and user account control.
- **Data Harvesting**: Export role-specific CSV reports with custom timestamps.

---

## 🛠️ Tech Stack

### Backend

- **Framework**: Flask 2.3.2 + Flask-Login
- **Real-Time**: Flask-SocketIO (WebSocket)
- **Database**: SQLite with WAL mode (High concurrency)
- **ML Engine**: scikit-learn (KNN), NumPy (interaction matrix)
- **Security**: Werkzeug (Password hashing), Secure Session Management

### Frontend

- **Design**: Vanilla CSS + Bootstrap 5 (Customized Glassmorphism)
- **Interactive**: Vanilla JS (Fetch API, Async/Await)
- **Physics/Motion**: Vanilla Tilt.js (3D Tilt), CSS Keyframes (60fps)
- **Icons**: FontAwesome 6+

---

## 📋 Prerequisites

- Python 3.7+
- pip
- Git
- Redis (Optional for scaling WebSockets)

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <repository-url>
cd "Alumni App/alumni-hub"
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: This installs `numpy` and `scikit-learn` for the ML recommendation engine.

### 3. Initialize Databases

```bash
# Initialize main user database
python app.py  # Initial run creates tables
# Migrate to Recommendation System schema
python migrate_db.py
# Initialize messaging specific tables
python init_messaging_db.py
```

### 4. Configuration (.env)

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_secret_key
MAIL_USERNAME=alumnihub26@gmail.com
MAIL_PASSWORD=jxrp_rghf_qcow_xfne
```

### 5. Run Application

```bash
python app.py
```

Visit `http://localhost:5000`

---

## 📝 Default Admin Credentials

- **EMAIL**: `admindbit195@college.edu`
- **PASSWORD**: `admindbit195@`

---

- **[RECOMMENDATIONS.md](file:///d:/RajenderMohan_BCA/BCA_Major_Project/alumni-hub/RECOMMENDATIONS.md)**: Detailed technical documentation for the scoring engine and AI roadmap.

---

## 📁 Project Architecture

```
alumni-hub/
├── database/            # DB Helpers (messaging_db.py, etc.)
├── models/              # Core Logic
│   └── recommendation.py    # Phase 1: Rule-Based Engine + backward-compat wrapper
├── services/            # Business Logic & ML Services
│   ├── recommendation_engine.py  # Phase 2: KNN Collaborative Filtering + Hybrid
│   ├── profile_service.py        # Profile update & faculty profile logic
│   └── admin_service.py          # Optimized admin dashboard queries
├── utils/               # Reusable Utilities (NEW in v5.0)
│   ├── decorators.py    # @role_required() access control decorator
│   ├── helpers.py       # OTP, file upload, validation, sanitization helpers
│   └── db.py            # DB context manager, query_one(), query_all()
├── routes/              # API & Page Routes
│   └── recommendation_routes.py  # /recommendations/<user_id>, /retrain, /log
├── scripts/             # DB Migrations & Utilities
├── static/              # Assets (JS, CSS, Images)
├── templates/           # Jinja2 Layouts
├── app.py               # Main Application Entry (SocketIO + DB init)
├── db_utils.py          # Database connection utility
├── requirements.txt     # Python dependencies (incl. numpy, scikit-learn)
└── .env                 # Environment Config
```

---

## 🔒 Security Summary

- ✅ **Password Hashing** — Werkzeug salt-based hashing
- ✅ **Password Strength** — Minimum 8 chars, mixed case, digits required (`validate_password()`)
- ✅ **Secure Mail** — TLS/SSL Gmail SMTP integration
- ✅ **XSS Protection** — Automatic Jinja2 escaping + `sanitize_html()`
- ✅ **Role Access Control** — `@role_required()` decorator + per-route checks
- ✅ **Connection-Gated Chat** — Private chat requires verified connection
- ✅ **OTP Security** — OTPs server-logged only, never exposed to browser
- ✅ **Safe Error Messages** — Internal errors hidden from users
- ✅ **Duplicate Prevention** — Unique database constraints
- ✅ **DB Connection Safety** — All routes use `try/finally` with `conn.close()`

---

## 📊 Performance Statistics

- **Database Indexes**: 14 indexes on high-traffic columns (users, connections, profiles, interactions)
- **Optimized Queries**: Admin dashboard uses GROUP BY instead of per-year COUNT loops (20+ → 2 queries)
- **Concurrency**: SQLite WAL mode enabled for simultaneous messaging
- **Connection Safety**: All 62 `get_db_connection()` calls wrapped in `try/finally`
- **Performance**: GPU-accelerated 60fps animations
- **Load Times**: Optimized asset delivery < 2s

---

---

## 🧠 Recommendation System — Full Architecture & Logic

The Alumni Hub features a **two-phase hybrid recommendation engine** combining rule-based scoring with ML collaborative filtering.

### **Phase 1 — Rule-Based Scoring Engine** (`models/recommendation.py`)

Deterministic scoring based on profile similarity:

| Factor             | Points        | Description                     |
| ------------------ | ------------- | ------------------------------- |
| Same Branch        | +5            | Department/branch match         |
| Skill Match        | +5 per skill  | Comma-separated skill overlap   |
| Passing Year       | +4 / +2       | Within 2 years / within 4 years |
| Same Domain        | +3            | Shared professional domain      |
| Same City          | +2            | Geographic proximity            |
| Mutual Connections | +2 per mutual | Social graph proximity          |

**Key function**: `get_rule_based_recommendations(user_id, limit=5)`

### **Phase 2 — ML Collaborative Filtering** (`services/recommendation_engine.py`)

KNN with Cosine Similarity on a user-interaction matrix.

#### Interaction Matrix Construction (`build_interaction_matrix()`)

Weighted signals from real database tables:

| Interaction Source  | Weight | Direction            | DB Table              |
| ------------------- | ------ | -------------------- | --------------------- |
| Accepted Connection | 5      | Bidirectional        | `connections`         |
| Private Message     | 4      | Sender → Receiver    | `private_messages`    |
| Connection Request  | 3      | Sender → Receiver    | `connection_requests` |
| Job Application     | 2      | Student → Job Poster | `job_applications`    |
| Custom Interactions | 1–4    | User → Target        | `user_interactions`   |

#### Model Training (`train_knn_model()`)

- Uses `sklearn.neighbors.NearestNeighbors` with `metric='cosine'`
- L2-normalized interaction vectors
- `n_neighbors = min(10, n_users - 1)`
- **Trained once at startup** in a background thread
- Cached in global `_model_cache` — reused across all requests
- Retrainable via `POST /recommendations/retrain` (admin only)

#### ML Recommendations (`get_ml_recommendations(user_id)`)

- Queries KNN for nearest neighbors
- Converts cosine distance to similarity score (0–100)
- Excludes already connected / pending users
- Cross-role matching: students see alumni, alumni see students

### **Hybrid Strategy** (`hybrid_recommendation(user_id)`)

```
1. Try ML recommendations first
2. If ML returns < 5 results (cold start / sparse data)
   → Fill remaining slots with rule-based recommendations
3. Deduplicate by user ID (ML takes priority)
4. Sort by score descending → return top 5
```

### **Cold Start Handling**

Users with fewer than 2 interactions in the matrix automatically receive **pure rule-based** recommendations. As they interact (connect, message, apply to jobs), ML gradually takes over.

### **API Endpoints** (`routes/recommendation_routes.py`)

| Method | Endpoint                     | Auth  | Description                                 |
| ------ | ---------------------------- | ----- | ------------------------------------------- |
| GET    | `/recommendations`           | Login | Current user's top 5 (backward compat)      |
| GET    | `/recommendations/<user_id>` | Login | JSON with recommendations for specific user |
| POST   | `/recommendations/retrain`   | Admin | Force retrain the KNN model                 |
| POST   | `/recommendations/log`       | Login | Log a user interaction (profile_view, etc.) |

**Sample JSON Response** (`GET /recommendations/1`):

```json
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

### **Dashboard Integration**

Both student and alumni dashboards call `get_recommended_users(current_user)` which auto-delegates to the hybrid engine. Recommendation cards display:

- Score badge (green for ML, blue for rule-based)
- **AI badge** on ML-powered recommendations
- Reason tag (e.g., "3 skill match, Same branch")
- One-click Connect button

### **Database Table** (`user_interactions`)

```sql
CREATE TABLE IF NOT EXISTS user_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_user_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL,  -- profile_view, job_click, mentorship_request, message, connection_request
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id)
);
```

### **Future Scope**

- 🔮 **Deep Learning**: Graph Neural Networks (GNN) for richer social graph embeddings
- ⚡ **Real-Time Updates**: Incremental model retraining on new interaction events
- 🎯 **Weighted Ensemble**: `α × ML_score + (1 − α) × rule_score` tunable hybrid
- 🧪 **A/B Testing**: Framework for comparing algorithm quality
- 📈 **Matrix Factorization**: SVD / ALS for implicit feedback at scale
- 🤖 **Contextual Bandits**: Exploration vs exploitation for recommendation diversity

---

## 💼 Career Board & Job Matching Ecosystem

The platform features a robust Job Board designed to bridge the gap between Alumni professional networks and Student career aspirations.

### **Functional Components**

1.  **Job Posting Hub (Alumni)**: A secure form capturing title, company, description, and required skill tags.
2.  **Recommendation Grid (Student)**: A personalized view highlighting jobs matching user skills.
3.  **Job-to-Student Scoring**:
    - **Skill Match**: Set-intersection analysis on `required_skills` vs `user_skills`.
    - **Semantic Boost**: AI matching between Student bio and Job description.

---

**Status**: ✅ Production Ready | **Version**: 5.0 | **Last Updated**: June 2026
