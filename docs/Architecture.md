# Architecture — Alumni Hub

> Derived from the actual codebase at version 1.0.
> Stack: Flask + Flask-SocketIO + SQLite (raw `sqlite3`) + Jinja2 + Bootstrap 5 + scikit-learn.

---

## 1. Architectural Style

Alumni Hub follows a **layered monolith** style with an emerging service / utility split:

```
┌──────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  Jinja2 templates (base.html master layout)                  │
│  templates/common · student · alumni · faculty · admin ·     │
│  auth · messaging · social · emails                          │
│  Bootstrap 5 + FontAwesome + AOS + Chart.js + Socket.IO JS   │
└──────────────────────────────────────────────────────────────┘
                              ▲ render_template / jsonify
┌──────────────────────────────────────────────────────────────┐
│                      ROUTING LAYER                           │
│  app.py  (≈100 in-app routes, monolithic)                    │
│  routes/messaging_routes.py     → messaging_bp  (/api)       │
│  routes/connection_routes.py    → connection_bp (/api/...)   │
│  routes/recommendation_routes.py→ recommendation_bp (/)      │
│  routes/social_routes.py        → social_bp (/social)        │
│  routes/websocket_routes.py     → Socket.IO event handlers   │
└──────────────────────────────────────────────────────────────┘
                              ▲ function calls
┌──────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                            │
│  services/admin_service.py         admin queries/monitoring  │
│  services/profile_service.py       profile write logic       │
│  services/recommendation_engine.py ML collaborative filtering│
│  models/recommendation.py          rule-based scoring + jobs  │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                         │
│  db_utils.get_db_connection()   primary connection factory   │
│  utils/db.py  get_db/query_one/query_all/execute_sql         │
│  database/messaging_db.py       messaging CRUD + context mgr │
│  SQLite 19 tables, WAL mode, 25 named indexes                 │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                        │
│  config.py  env-driven configuration + static data           │
│  extensions.py  mail (Flask-Mail instance)                   │
│  utils/helpers.py  OTP, uploads, validation, sanitisation    │
│  utils/decorators.py  @role_required()                       │
│  APScheduler  periodic_profile_reminder job                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Component Map

| Path | Responsibility | LOC |
| --- | --- | --- |
| `app.py` | App factory-ish bootstrap, `User` model, `load_user`, `init_db()`, ~100 routes, email sender, socketio emits, scheduler job | 4,875 |
| `config.py` | `Config` / `DevelopmentConfig` / `ProductionConfig`, `COURSE_CATEGORIES`, `DEPARTMENTS`, `SEMESTERS` | 214 |
| `extensions.py` | Single `mail = Mail()` extension object | 2 |
| `db_utils.py` | `get_db_connection()` factory using `current_app.config['DB_NAME']` | 14 |
| `models/recommendation.py` | Phase-1 rule-based scoring, `get_recommended_users()` wrapper, `get_recommended_jobs()` | 257 |
| `services/recommendation_engine.py` | Phase-2 KNN/cosine collaborative filtering, hybrid merge, background training | 489 |
| `services/admin_service.py` | `get_role_counts`, `get_yearly_stats`, `get_admin_job_stats`, `get_all_connections`, `get_connection_activity`, `get_user_statistics` | 293 |
| `services/profile_service.py` | `update_user_profile()`, `ensure_faculty_profile()` | 88 |
| `database/messaging_db.py` | Lock, suspension, public/private messages, conversations, search, stats + own context manager | 527 |
| `routes/messaging_routes.py` | REST mirror of all messaging operations | 528 |
| `routes/connection_routes.py` | Blueprint connection request API + email templates | 330 |
| `routes/websocket_routes.py` | All Socket.IO handlers, room management, presence | 448 |
| `routes/recommendation_routes.py` | 4 recommendation endpoints | 132 |
| `routes/social_routes.py` | 5 social link pages | 23 |
| `utils/helpers.py` | OTP, uploads, phone normalisation, timestamp parsing, error sanitisation, HTML escape, password validation, job form extraction | 244 |
| `utils/db.py` | `get_db()` context manager + `query_one/all/execute_sql` | 79 |
| `utils/decorators.py` | `@role_required(*roles)` with HTML/JSON dual failure modes | 57 |
| `scripts/*.py` | 14 maintenance scripts: init, migrate, optimise, debug, test | ~700 |

---

## 3. Startup Sequence

`app.py` executes top-to-bottom at import, so the order matters (important for Gunicorn / Vercel):

```
1. Imports (Flask, SocketIO, LoginManager, Mail, APScheduler, blueprints, services)
2. logging.basicConfig(...)  → logger
3. load_dotenv()
4. app = Flask(__name__)
5. env = os.getenv('FLASK_ENV', 'development')
   app.config.from_object(config[env])        # config.py
6. SMTP settings from env                     # app.py:45-52
7. socketio = SocketIO(app, cors_allowed_origins="*",
                       ping_timeout=60, ping_interval=25,
                       async_mode='threading')
8. mail.init_app(app)
9. scheduler = APScheduler(); init_app; start()
10. Create upload directories (static/uploads, static/uploads/company_logos)
11. app.config['MAX_CONTENT_LENGTH'] = 16 MB
12. login_manager = LoginManager(); init_app; login_view = 'login'
13. @app.template_filter('initials')
14. ~100 @app.route definitions registered
15. @scheduler.task('interval', id='periodic_profile_reminder', days=2)
16. MODULE LEVEL blueprint registration                # app.py:4827
      messaging_bp  → /api
      setup_websocket_handlers(socketio)
      social_bp     → /social
      connection_bp → /api/connection-request
      recommendation_bp → /
17. init_recommendation_engine(app=app)               # background thread trains KNN
18. with app.app_context(): init_db()                 # idempotent schema migration
19. if __name__ == '__main__': socketio.run(app, debug=..., host='0.0.0.0', port=5000)
```

**Key design choice:** steps 16 and 18 are at module level (not inside `__main__`). This makes `gunicorn app:app` and Vercel's `app.py` entry work identically — schema always exists, blueprints always registered, ML model always warmed.

---

## 4. Data Access Architecture

### 4.1 Two Connection Factories (intentional duplication)

| Factory | Location | DB source | Used by |
| --- | --- | --- | --- |
| `get_db_connection()` | `db_utils.py:4` | `current_app.config['DB_NAME']` → `data/college_pro.db` | All `app.py` routes, `models/`, `services/` |
| `get_db_connection()` | `database/messaging_db.py:14` | hard-coded `'college_pro.db'` (repo root) | `routes/messaging_routes.py`, `routes/websocket_routes.py` |
| `get_db()` | `utils/db.py:31` | `current_app.config.get('DB_NAME')` | *(available, not yet adopted)* |

> ⚠️ **Operational note.** The two factories point at **different physical files** on disk: `data/college_pro.db` vs `./college_pro.db`. The repo currently contains `college_pro.db` (2 lines), `data/college_pro.db` (466 lines — the live DB) and `data/alumni.db` (empty). Unifying all three onto `data/college_pro.db` is a required cleanup item.

All three apply the same pragmas:
```python
conn = sqlite3.connect(db_name, timeout=20.0)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")      # concurrent readers + one writer
conn.execute("PRAGMA synchronous=NORMAL")   # durability/throughput trade-off
```

`sqlite3.Row` enables both index access (`row['col']`) and `.keys()` — used by the tolerant field readers (`app.py:274`, `app.py:825`, `routes/connection_routes.py:47`).

### 4.2 Connection Lifecycle Rules

- **Rule 1** — Every route uses `conn = None` then `try: conn = get_db_connection()` … `finally: if conn: conn.close()`.
- **Rule 2** — Exceptions call `conn.rollback()` before re-raising or flashing.
- **Rule 3** — Reads that need only existence use `SELECT 1` instead of `SELECT *`.
- **Rule 4** — Role-gated tables are joined conditionally with `AND u.role = 'student'` in the ON clause (see `services/admin_service.py:88-93`) to avoid cross-role row multiplication.

### 4.3 Schema Migration Strategy

`init_db()` (`app.py:298`) is **idempotent and additive**:

1. `CREATE TABLE IF NOT EXISTS` for all 20 tables.
2. `ALTER TABLE … ADD COLUMN` for 12 `users` columns, guarded by catching `sqlite3.OperationalError` containing `"duplicate column name"`.
3. Same guarded pattern for `connection_requests.accepted_at`, `updated_at` and 27 `jobs` columns.
4. `CREATE INDEX IF NOT EXISTS` for 15 hot-path indexes.
5. `UPDATE jobs SET approval_status='approved' WHERE approval_status IS NULL OR ''` — backfill.
6. Seeds Super Admin only if `SELECT COUNT(*) FROM users WHERE role='admin'` is 0.

This means **no external migration tool (Alembic) is required** — a real strength for the deployment targets in use, but also a source of schema drift (see §10).

### 4.4 Indexing Strategy

25 named indexes (plus 11 implicit `UNIQUE` indexes) across `users`, `connection_requests`, `connections`, `student_profile`, `alumni_profile`, `faculty_profile`, `user_activity`, `user_interactions`, `registration_log`, `password_resets`.

Hot queries and their index:
| Query | Index |
| --- | --- |
| `SELECT * FROM users WHERE email = ?` | `idx_users_email` + `sqlite_autoindex_users_1` (UNIQUE) |
| `WHERE role = ? ORDER BY id DESC` | `idx_users_role` |
| `WHERE receiver_id = ? AND status = 'pending'` | `idx_connection_requests_receiver (receiver_id, status)` |
| `WHERE sender_id = ? AND receiver_id = ? AND status='pending'` | `idx_connection_requests_sender (sender_id, status)` |
| `WHERE (user_id_1 = ? AND user_id_2 = ?) OR (… reversed)` | `idx_connections_user1`, `idx_connections_user2` |
| `GROUP BY strftime('%Y', created_at), role` | `idx_users_created_at` |

> **Duplicate indexes observed:** `idx_connections_u1`/`idx_connections_u2` (from `scripts/optimize_db.py`) coexist with `idx_connections_user1`/`idx_connections_user2` (from `app.py:553-554`), and `idx_connreq_*` overlap `idx_connection_requests_*`. `scripts/optimize_db.py` and the in-app migration should be consolidated.

---

## 5. Authentication & Authorization Architecture

```
Request
  │
  ├─ @login_required ──────────────► unauthenticated ─► redirect url_for('login')
  │
  ├─ Flask-Login session ─► user_loader ─► load_user(user_id)
  │        SELECT * FROM users WHERE id = ?
  │        builds User(id, name, email, role, profile_pic, phone,
  │                    is_verified, is_suspended, branch, passing_year,
  │                    current_domain, skills, interests, city, company, bio)
  │        profile_pic fallback → https://ui-avatars.com/api/...
  │        User.is_active → not is_suspended   (suspension kills the session)
  │
  ├─ @role_required('admin', 'faculty')      utils/decorators.py
  │        not authenticated        → redirect login
  │        role not in allowed set  → JSON 403 if path startswith /api/
  │                                   else flash + redirect home
  │
  └─ inline guards (majority of routes)
           if current_user.role != 'admin': flash/403
           if current_user.id != user_id and current_user.role != 'admin': deny
           if current_user.role not in ('student','alumni','faculty'): deny
```

**Authorisation philosophy:** defence in depth. The `@role_required()` decorator exists and is correct, but the codebase primarily relies on explicit inline `if current_user.role != …` checks inside each view. This is consistent and auditable but duplicated ~60 times — a candidate for gradual migration to the decorator.

**Extra gates beyond role:**
- Private chat requires an accepted `connections` row (`app.py:1718`).
- Alumni/faculty profiles are editable only by owner or admin.
- `/recommendations/<user_id>` requires self or admin (`routes/recommendation_routes.py:64`).
- `POST /recommendations/retrain` is admin-only.
- All `/admin/*` routes check `current_user.role != 'admin'`.
- `DELETE /api/delete-user/<id>` refuses to delete the Super Admin email.

---

## 6. Recommendation Engine Architecture

```
                ┌─────────────────────────────────────┐
                │ get_recommended_users(current_user)  │  models/recommendation.py:193
                └──────────────┬──────────────────────┘
                               │ delegates
                               ▼
                ┌─────────────────────────────────────┐
                │ hybrid_recommendation(user_id, 5)   │  services/recommendation_engine.py:381
                └───┬─────────────────────────────┬───┘
                    │ 1st                          │ if < 5 results
                    ▼                             ▼
   ┌────────────────────────────┐   ┌──────────────────────────────┐
   │ get_ml_recommendations()   │   │ get_rule_based_recommendations()
   │  • cold-start guard        │   │  • branch      +5           │
   │    count_nonzero(vec) < 2  │   │  • skills      +5 per match  │
   │  • kneighbors(cosine)      │   │  • domain      +3           │
   │  • exclude self/connected/ │   │  • year ≤2 → +4, ≤4 → +2    │
   │    pending                 │   │  • city        +2           │
   │  • cross-role filter       │   │  • mutuals     +2 each      │
   │  • similarity = (1-d)*100  │   │  • sort desc, top 5         │
   └────────────┬───────────────┘   └──────────────┬───────────────┘
                │                                  │
                └────────► dedupe by user_id ───────┘
                                │
                                ▼
                 sort by score desc → top 5 → dashboard cards
                                │
                  ML cards get an "AI" badge (source == 'ml')
```

### 6.1 Interaction Matrix Construction

`services/recommendation_engine.py:68` builds a dense `numpy.float32` matrix of shape `(n_users, n_users)` where `n_users` counts **only student + alumni** users (faculty and admin are excluded from the recommender population).

Weight sources are accumulated, not overwritten:
```
matrix[i][j] += WEIGHT_CONNECTION (5)        for connections (bidirectional)
matrix[i][j] += WEIGHT_MESSAGE (4)           for private_messages (directional)
matrix[i][j] += WEIGHT_CONN_REQUEST (3)      for pending connection_requests
matrix[i][j] += WEIGHT_JOB_APPLICATION (2)   for job_applications via jobs.posted_by
matrix[i][j] += type_weight × count          for user_interactions grouped counts
```
Every source except `connections` is wrapped in `try/except` and logs at DEBUG if the table does not exist — so a partially migrated database still trains.

### 6.2 Model Lifecycle

| Concern | Implementation |
| --- | --- |
| Trainer | `sklearn.neighbors.NearestNeighbors(n_neighbors=min(10, n-1), metric='cosine', algorithm='brute')` |
| Preprocessing | `sklearn.preprocessing.normalize(matrix, axis=1, norm='l2')` |
| Cache | Module-global `_model_cache` dict with `knn_model`, `interaction_matrix`, `user_id_to_idx`, `idx_to_user_id`, `last_trained`, `threading.Lock` |
| Trigger | `init_recommendation_engine(app)` spawns a daemon thread at import; runs inside `app.app_context()` |
| Guard | Non-forced retrains within 300 s are skipped |
| Manual retrain | `POST /recommendations/retrain` (admin) → `train_knn_model(force=True)` |
| Failure mode | `ImportError` (no sklearn) or `matrix.shape[0] < 2` → returns `False`, logs a warning, hybrid falls back to rule-based |
| Interaction logging | `POST /recommendations/log` → `log_interaction(user_id, target_user_id, type)`; failures are swallowed so they never break the UI |

### 6.3 Complexity Notes
- Matrix is `O(n²)` memory. At 10 users this is trivial; at 10,000 users it is ~400 MB — the reason `Future Scope` in the source mentions SVD/ALS/GNN.
- Brute-force KNN is `O(n)` per query — fine for moderate n, the documented upgrade path.

---

## 7. Real-Time Architecture

```
┌──────────────┐        Socket.IO (threading async_mode)        ┌──────────────┐
│ Browser A    │◄──────────────────────────────────────────────►│ Flask-SocketIO│
│ private_chat │   rooms: user_A, user_B, public_chat            │   server      │
└──────────────┘                                                └──────┬───────┘
                                                                          │
┌──────────────┐   emit('receive_private_message', room=user_B)         │
│ Browser B    │◄──────────────────────────────────────────────           │
└──────────────┘                                                        │
                                                                          ▼
                                                              ┌────────────────────┐
                                                              │  database/         │
                                                              │  messaging_db.py   │
                                                              │  (SQLite + WAL)    │
                                                              └────────────────────┘
```

**Room strategy**
| Room | Members | Purpose |
| --- | --- | --- |
| `public_chat` | Every authenticated user | Broadcast messages, presence, global lock events |
| `user_<id>` | One user, all their tabs | Private messages, job approval updates, connection status |
| `admin_monitor` | Admins only (`websocket_routes.py:46`) | Live connection-request activity feed |

**Handler registration** — all handlers are defined inside `setup_websocket_handlers(socketio)` (`routes/websocket_routes.py:23`) and bound with the `@socketio.on(...)` decorator. This is called once at import from `app.py:4838`.

**Guard pattern** — every handler opens with `if not current_user.is_authenticated: emit('error', ...); return`. Admin-only handlers add `or current_user.role != 'admin'`. Unauthenticated `connect` returns `False`, which refuses the socket handshake.

**Presence** — module-level `online_users: dict` keyed by `user_id`, storing `{id, name, role, session_id, connected_at}`. Note this is **per-process**, so it is incorrect behind multiple workers — a Redis-backed store is the documented upgrade.

**Hybrid delivery** — HTTP REST (`/api/messages/*`) and WebSocket events both call the same `database/messaging_db.py` functions, so any client style works.

---

## 8. Frontend Architecture

### 8.1 Template Hierarchy

```
base.html                       ← master layout: <head> meta/SEO, navbar,
  │                                alerts, scroll-to-top, footer, scripts
  ├── common/                   home, about, services, events, contact, faq,
  │                             privacy_policy, terms_conditions, report_issue
  ├── auth/                     login, register, verify_otp, forgot_password,
  │                             reset_password_final, change_password
  ├── student/                  dashboard, profile, edit_profile, network,
  │                             messages, mentorship, jobs, notifications,
  │                             settings, upgrade
  ├── alumni/                   dashboard, profile, edit_profile, network,
  │                             messages, mentorship, jobs, post_job, spotlight,
  │                             events, notifications, settings, upgrade,
  │                             meet_register, meet_view
  ├── faculty/                  dashboard, profile, edit_profile, events,
  │                             announcements, notifications, settings, reports
  ├── admin/                    dashboard_admin, admin_view_users,
  │                             admin_approve_requests, admin_registrations,
  │                             admin_analytics, admin_stats, admin_events,
  │                             admin_messaging_control, connection_monitor,
  │                             jobs, add_job, edit_job, profile_admin,
  │                             edit_admin_profile, reports, whatsapp_broadcast
  ├── messaging/                dashboard (public chat), private_chat
  ├── social/                   linkedin, facebook, instagram, youtube, github
  ├── emails/                   base_email, request_email, accepted_email
  └── (root-level)              events, jobs, network, messages, mentorship,
                                notifications, settings, post_job, spotlight,
                                announcements, upgrade, search_network,
                                compose_email, contact_bridge, complete_profile,
                                coming_soon
```

**Note on duplication:** the root-level `events.html`, `jobs.html`, `network.html`, `messages.html`, `mentorship.html`, `notifications.html`, `settings.html`, `spotlight.html`, `announcements.html`, `post_job.html`, `upgrade.html` are near-copies of the role-specific versions under `student/` and `alumni/`. Route functions resolve which one to render based on `current_user.role` (see `app.py:4620 list_jobs()`, `app.py:4506 network()`). Consolidating to a single `base.html` + role partials would remove ~1,500 lines of duplicated markup.

### 8.2 CSS Layering (13 files)

| File | Scope |
| --- | --- |
| `style.css` | Core layout, navbar, footer, cards, buttons (loaded on every page via `base.html`) |
| `theme.css` | Design-token layer: colours, gradients, typography, spacing scale, radii, shadows, transitions, keyframes, utility classes. **Not currently linked from `base.html`** — the tokens it defines are duplicated inline in several templates. |
| `navbar-professional.css` | Smart-scroll navbar, pill links, mobile overlay menu |
| `ui-enhancements.css` | Glassmorphism cards, alerts, badges, modals, toasts |
| `animations.css` | 60 fps keyframe library (fade/slide/scale/mesh/blob) |
| `home-premium.css`, `home-enhancements.css` | Landing page |
| `about-enhancements.css` | About / team section |
| `contact-enhancements.css` | Contact form |
| `services-enhancements.css` | Services page |
| `social_pages.css` | Social link pages |
| `student-dashboard-animations.css` | Student dashboard motion |

**Design token source of truth (`theme.css` `:root`)**
```
--primary #1e3a8a   --secondary #0ea5e9   --accent #f59e0b
--success #10b981   --danger    #ef4444   --dark    #0f172a
gradients: primary #1e3a8a→#0ea5e9, secondary #f59e0b→#ef4444
spacing: xs .25 / sm .5 / md 1 / lg 1.5 / xl 2 / 2xl 3 rem
radius: sm 8 / md 12 / lg 15 / xl 20 px
shadow: sm/md/lg/xl ramps
transition: fast .2s / normal .3s / slow .5s ease
fonts: Outfit + Plus Jakarta Sans (+ JetBrains Mono on admin)
```

Per-page **scoped token blocks** also exist inline (e.g. `--cm-*` in `connection_monitor.html`, `--terminal-*` in `dashboard_admin.html`, `--glass-*`), which is a local override pattern rather than a global system.

### 8.3 JavaScript (4 files + CDN)

| File | Contents |
| --- | --- |
| `animations.js` | `ScrollAnimator` (IntersectionObserver, threshold 0.1, `-100px` bottom margin), `TypingEffect`, counter animation with `requestAnimationFrame` |
| `network-animation.js` | Particle network canvas — 60 particles, 150 px link distance, 200 px mouse-repel radius, per-canvas instances on `.network-canvas` |
| `sparkles.js` | Cursor sparkles / ambient micro-interactions |
| `bootstrap.bundle.min.js` | Vendored Bootstrap JS |
| CDN | Socket.IO 4.5.4, Chart.js, AOS 2.3.1, Vanilla Tilt 1.7.0 |

Inline scripts inside `base.html` handle: AOS init, active nav-link highlighting, smart scroll (hide down / show up), mobile overlay toggle with body-scroll lock, magnetic navbar branding, and back-to-top. Toast/alert rendering uses Bootstrap dismissible alerts with a 5 s auto-dismiss.

Counter animations are guarded with a `dataset` flag so scrolling back up does not re-trigger the count (documented in the README).

---

## 9. Email Architecture

Two coexisting mechanisms:

**A. Raw SMTP helper** — `send_email(to, subject, html)` at `app.py:104`
```
smtplib.SMTP(smtp.gmail.com, 587, timeout=10)
  → starttls()
  → login(MAIL_USERNAME, MAIL_PASSWORD)   # strips surrounding quotes
  → send_message(MIMEMultipart('alternative') with MIMEText('text/html'))
returns (bool, message); three except branches: SMTPAuthenticationError, SMTPException, generic
```
Used for: registration OTP, OTP resend, forgot-password OTP, contact form (admin + user), issue report, connection lifecycle emails (`send_connection_email`), user-to-user composed email, and the scheduled reminder job.

**B. Flask-Mail** — `extensions.mail` used by `routes/connection_routes.py` with `templates/emails/request_email.html` and `accepted_email.html`, sender `('ALUMNI HUB', MAIL_DEFAULT_SENDER)`.

> ⚠️ `MAIL_PASSWORD` has a **hard-coded fallback** in `app.py:50` and the README documents the real app-password in plaintext. This must be removed and rotated before any deployment.

Email inventory:
| Trigger | Recipient | Template |
| --- | --- | --- |
| Registration OTP | New user | inline HTML (`app.py:997`) |
| Resend OTP | New user | inline HTML (`app.py:1224`) |
| Password reset OTP | User | inline HTML (`app.py:2349`) |
| Connection request | Receiver | `send_connection_email(action='request')` / `emails/request_email.html` |
| Connection accepted | Sender | `action='accepted'` / `emails/accepted_email.html` |
| Connection rejected | Sender | `action='rejected'` |
| Mutual connect | Receiver | `action='mutual'` |
| Contact form | Admin + requester | inline HTML (`app.py:691`, `746`) |
| Issue report | Admin | inline HTML (`app.py:4280`) |
| Compose email | Any user | inline HTML with profile + WhatsApp bridge + LinkedIn signature (`app.py:4428`) |
| Profile reminder (every 2 days) | All non-suspended users | inline HTML (`app.py:4786`) |

---

## 10. Known Architectural Debt

| # | Issue | Location | Impact |
| --- | --- | --- | --- |
| 1 | `app.py` is 4,875 lines with ~100 routes in one module | `app.py` | Maintainability; merge conflicts; hard to test |
| 2 | Two connection factories pointing at **different DB files** | `db_utils.py:9` vs `database/messaging_db.py:10` | Messaging tables can silently diverge from app tables |
| 3 | Duplicate blueprint implementations of the same endpoints | `app.py:3809+` vs `routes/connection_routes.py` | Divergent behaviour (cooldown, id-vs-request_id parameterisation) |
| 4 | `utils/db.py` context manager exists but is unused | `utils/db.py` | Two connection styles coexist |
| 5 | `@role_required()` exists but is imported and barely used | `app.py:25`, `utils/decorators.py` | ~60 inline role checks instead |
| 6 | Duplicate indexes | `scripts/optimize_db.py` vs `app.py:547` | Wasted write throughput |
| 7 | In-memory `online_users` dict | `routes/websocket_routes.py:20` | Breaks with multiple workers |
| 8 | `async_mode='threading'` + `cors_allowed_origins="*"` | `app.py:55` | Single-process only; permissive CORS |
| 9 | ~1,500 lines of duplicated templates | root-level vs role folders | Two sources of truth per page |
| 10 | `theme.css` tokens not globally linked; duplicated inline | `static/css/theme.css` vs templates | Design drift |
| 11 | Schema drift — live DB `users` table has different column set than `init_db()` `CREATE` statement | `data/college_pro.db` | Fresh installs differ from migrated installs |
| 12 | `models/recommendation.py` live schema differs from `scripts/init_db.py` (e.g. `connections.user1_id` vs `user_id_1`) | `scripts/init_db.py` | Migration scripts are stale |
| 13 | No test suite | `test_import.py` is a 2-line import smoke check | No regression safety net |
| 14 | `print()` still present alongside `logger` | `app.py` (many), `routes/connection_routes.py`, `websocket_routes.py` | Inconsistent observability |
| 15 | `get_private_msgs` returns a hard-coded placeholder | `routes/messaging_routes.py:201-217` | Endpoint is non-functional |
| 16 | ML model never refreshes after startup | `services/recommendation_engine.py` | Stale recommendations until manual retrain/restart |

---

## 11. Deployment Architecture

### 11.1 Primary target — PythonAnywhere / any WSGI host
```
Procfile:  web: gunicorn app:app

gunicorn
  └─ imports app.py (module level)
       ├─ registers all blueprints + socket handlers
       ├─ starts APScheduler
       ├─ spawns ML training thread
       └─ runs init_db() (idempotent migrations)
```
Static assets live in `static/uploads/` on the persistent filesystem — profile photos and company logos persist.

### 11.2 Secondary target — Vercel
```json
{ "version": 2,
  "builds":   [{ "src": "app.py", "use": "@vercel/python" }],
  "routes":   [{ "src": "/(.*)", "dest": "app.py" }],
  "env":      { "FLASK_ENV": "production" } }
```
With `FLASK_ENV=production`, `config.py` loads `ProductionConfig`, which reads `DATABASE_URL`. But `db_utils.get_db_connection()` calls `sqlite3.connect()` unconditionally — **there is no PostgreSQL driver wired into the runtime path**. `scripts/init_postgres.py` can provision a Postgres schema via `psycopg2`, but nothing consumes it. Vercel + a managed Postgres database is therefore an **incomplete** path.

Additionally, serverless invocations get an ephemeral filesystem: `data/college_pro.db` and `static/uploads/` resets between cold starts.

### 11.3 Environment variables

| Variable | Required | Default in code |
| --- | --- | --- |
| `SECRET_KEY` | ✅ production | `dev-key-change-in-production` |
| `FLASK_ENV` | — | `development` |
| `DB_NAME` | — | `data/college_pro.db` |
| `MAIL_SERVER` | — | `smtp.gmail.com` |
| `MAIL_PORT` | — | `587` |
| `MAIL_USE_TLS` | — | `True` |
| `MAIL_USERNAME` | ✅ for OTP | `alumnihub26@gmail.com` |
| `MAIL_PASSWORD` | ✅ for OTP | ⚠️ hard-coded |
| `ADMIN_EMAIL` | — | `alumnihub26@gmail.com` |
| `BASE_URL` | — | `http://localhost:5000` |
| `DATABASE_URL` | Vercel only | — |

---

## 12. Request Lifecycle — Worked Examples

### 12.1 Student loads dashboard
```
GET /student/dashboard
 → @login_required ─► Flask-Login calls load_user(session user_id)
      └─ get_db_connection() → SELECT * FROM users WHERE id = ?
      └─ build User (avatar fallback), close conn
 → role guard: current_user.role in ('student','admin')
 → try:
      conn = get_db_connection()
      5 queries: alumni list · faculty list · own student_profile
                 · pending connection_requests · other students
      recommendations = get_recommended_users(current_user)
         └─ hybrid_recommendation → cached KNN query (or train if cold)
              └─ SELECT … FROM users WHERE id = ? per neighbour
      render_template('student/dashboard.html', …)
   finally: conn.close()
```

### 12.2 Student sends a connection request
```
POST /api/connection-request/send  {"receiver_id": 7}
 → @login_required → role-agnostic (any authenticated role)
 → validate receiver_id ≠ self
 → SELECT * FROM users WHERE receiver_id          → 404 if missing
 → SELECT 1 FROM connections (both orderings)     → 400 'Already connected'
 → SELECT 1 FROM connection_requests (pending)    → 400 'Request already sent'
 → SELECT 1 FROM connection_requests (reverse, pending)
      └─ mutual found → UPDATE status='accepted' + INSERT connections (min/max)
                        + send_connection_email(action='mutual')
                        → 200 {'status': 'connected'}
 → INSERT INTO connection_requests (sender, receiver, 'pending')
 → send_connection_email(action='request')
 → socketio.emit('connection_request_received', room=f'user_{receiver_id}')
 → socketio.emit('admin_connection_activity',   room='admin_monitor')
 → 200 {'status': 'pending'}
   finally: conn.close()
```

### 12.3 Message delivery
```
Browser → socket.emit('send_private_message', {receiver_id, content})
 → handle_send_private_message (websocket_routes.py:201)
      guards: authenticated · not suspended · receiver_id present
              · content non-empty · len ≤ 5000 · not self
 → send_private_message(sender, receiver, content)      # messaging_db.py:218
      INSERT INTO private_messages
      INSERT OR IGNORE INTO conversations (min, max)
      UPDATE conversations SET last_message_id, last_message_at
 → emit('receive_private_message', room=f'user_{receiver_id}')
 → emit('message_sent', to sender)
Client-side follow-up:
 socket.emit('typing_private', {receiver_id})   → user_typing_private
 socket.emit('mark_message_read', {message_id, sender_id})
      → UPDATE private_messages SET is_read=1, read_at=…
      → emit('message_read', room=f'user_{sender_id}')
```

---

## 13. Architectural Strengths

1. **Module-level bootstrap** — schema, blueprints and ML warm-up all run on import, so `python app.py`, `gunicorn` and Vercel all behave identically.
2. **Idempotent self-migrating schema** — no migration tool to run on every deploy.
3. **Uniform connection lifecycle** — `try/finally` + `close()` is applied without exception across 62 call sites.
4. **Layered extraction done properly** — `utils/`, `services/`, `models/`, `database/`, `routes/` are real separations, not folders of stubs.
5. **Graceful ML degradation** — a missing sklearn install or a sparse matrix never breaks the app; it silently falls back to rule-based scoring.
6. **Real-time and REST share one persistence layer** — messaging works from either transport.
7. **Cold-start-aware recommender** — explicit `MIN_INTERACTIONS` threshold rather than empty results.
8. **Optimised admin analytics** — 20+ round trips collapsed into 2 `GROUP BY` queries.
9. **Layered visual design** — scoped CSS tokens + 13-file stylesheet split keeps page-level styling isolated.
10. **Privacy-aware WhatsApp bridge** — raw phone numbers are never exposed in HTML; a server-side redirect page mediates.

---

## 14. Recommended Refactor Path

```
Phase 1 — Unify the data layer
  • Point database/messaging_db.py at current_app.config['DB_NAME']
  • Delete stale college_pro.db copies; adopt utils/db.get_db() everywhere
  • Remove duplicate indexes; consolidate index creation in init_db()

Phase 2 — Split app.py
  routes/public.py · auth.py · dashboards.py · profiles.py
  routes/jobs.py · admin.py · alumni_meet.py · misc.py
  Move send_email + send_connection_email into services/email_service.py

Phase 3 — Collapse duplicate implementations
  • Choose either app.py's connection endpoints or routes/connection_routes.py
  • Collapse root-level templates into role folders with shared partials

Phase 4 — Adopt the abstractions that already exist
  • Replace inline role checks with @role_required()
  • Replace remaining print() with logger

Phase 5 — Production hardening
  • Rotate + externalise MAIL_PASSWORD and Super Admin credentials
  • Add rate limiting on /login, /verify-otp, /resend-otp
  • Add a real test suite (pytest + Flask test client)
  • Add Alembic (or keep self-migration but reconcile schemas)
  • Move to PostgreSQL for multi-instance deployment
  • Redis for Socket.IO message queue + presence when scaling out
```