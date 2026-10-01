# Memory — Alumni Hub

> Durable knowledge about this project: how it behaves, why it is built this way, what is true right now, and what must not be forgotten.
> Read this **before** changing anything.

---

## 1. Project Identity

| Field | Value |
| --- | --- |
| **Name** | Alumni Hub |
| **Institution** | DBIT / JIMS alumni community (Mumbai / Delhi references in copy; footer map points to JIMS Rohini, Delhi) |
| **Type** | Academic major project, MCA |
| **Version** | 1.0 (first release) |
| **Primary colour identity** | Navy `#1e3a8a` → Sky `#0ea5e9`, with amber `#f59e0b` accent |
| **Tagline** | Building Connections, Creating Opportunities |
| **Live host (in repo metadata)** | `dbitalumni.pythonanywhere.com` |
| **Team (from `static/images/team/`)** | `rajender.jpeg`, `rajender_tech.jpg`, `anushka_singh.jpg`, `shekhar_maurya.jpg` |

---

## 2. The Five Things You Must Know

### 2.1 `app.py` is 4,875 lines and is the whole app
~100 routes, the `User` model, `load_user`, `init_db()` (all schema), both email systems, all Socket.IO emits, and the APScheduler job live in this one file. Before you add a route, check whether a blueprint already covers the domain — four exist (`messaging`, `connection`, `recommendation`, `social`).

### 2.2 Bootstrap runs at module level, deliberately
Blueprint registration (`app.py:4827`) and `init_db()` (`app.py:4861`) are **outside** `if __name__ == '__main__'`. This is what makes `gunicorn app:app` and Vercel's `app.py` entry work. Do not "tidy" this into `__main__` — it will break production deployment.

### 2.3 Two DB factories point at two different files
| Factory | Resolves to |
| --- | --- |
| `db_utils.get_db_connection()` | `current_app.config['DB_NAME']` → `data/college_pro.db` |
| `database/messaging_db.get_db_connection()` | hard-coded `'college_pro.db'` → repo root |

The live data is in `data/college_pro.db` (466 lines). The repo also contains a 2-line `college_pro.db` at the root and an empty `data/alumni.db`. **Messaging reads and writes can silently hit a different file than the rest of the app.** This is the single highest-risk bug in the project.

### 2.4 Every DB connection must be closed in `finally`
The codebase pattern is unbreakable by convention:
```python
conn = None
try:
    conn = get_db_connection()
    ...
finally:
    if conn: conn.close()
```
62 call sites follow it. `routes/connection_routes.py` mostly follows it but has several early-return paths calling `conn.close()` inline — do not copy that pattern.

### 2.5 The ML model trains once and never refreshes
`services/recommendation_engine.py:469` spawns a daemon thread at import. After that, the model is cached forever unless an admin calls `POST /recommendations/retrain` or the process restarts. Users who interact after startup get no benefit until the next retrain. A scheduled retrain job was never implemented.

---

## 3. Mental Model — How a Request Flows

```
Browser
  │
  ├─ HTTP request ─► @login_required ─► load_user() ─► inline role check
  │                     (Flask-Login)     (SQLite)        (current_user.role)
  │                          │                              │
  │                          ▼                              ▼
  │                   conn = get_db_connection()      conn.close()
  │                          │ SQL (parameterised)
  │                          ▼
  │                   render_template() / jsonify()
  │
  └─ WebSocket ─► handle_* in routes/websocket_routes.py
                   guards: authenticated · role · suspension · length
                          │ messaging_db.py functions
                          ▼
                   emit(event, room=...)
                     rooms: public_chat · user_<id> · admin_monitor
```

The route layer is thin. Business logic belongs in `models/`, `services/` or `database/`.

---

## 4. Roles, Decisions and Their Rationale

### 4.1 Role Matrix

| | Student | Alumni | Faculty | Admin |
| --- | --- | --- | --- | --- |
| Self-register | ✅ | ✅ | ✅ | ❌ seeded only |
| Needs admin approval | ❌ | ✅ | ✅ | — |
| Auto-login after OTP | ✅ | ❌ | ❌ | — |
| Sees recommendations | ✅ alumni | ✅ students | ❌ | ❌ |
| Can post jobs | ❌ | ✅ (needs approval) | ✅ (needs approval) | ✅ instant |
| Can mentor | request side | mentor side | ✅ | — |
| CSV / DB export | ❌ | ❌ | ❌ | ✅ |
| Lock messaging | ❌ | ❌ | ❌ | ✅ |
| Suspend users | ❌ | ❌ | ❌ | ✅ |
| Connection monitor | ❌ | ❌ | ❌ | ✅ |
| Retrain ML model | ❌ | ❌ | ❌ | ✅ |

### 4.2 Why these choices

**Why only `@gmail.com`?** Academic-project constraint. Simple validation, one code path (`app.py:891`).

**Why do alumni and faculty need approval?** Trust. Alumni post jobs and represent the institution publicly. `is_approved = 0` blocks login (`app.py:837`) and holds them in a queue the admin clears at `/admin/approve-requests`.

**Why is the private chat connection-gated?** Stops cold-DM spam between strangers. Enforced at `app.py:1718-1726`; admins are exempt so moderation is possible.

**Why does the recommender only match students ↔ alumni?** The graph's value is career mentoring. Faculty/admin are excluded from the ML matrix entirely (`recommendation_engine.py:90`). Faculty still appears in directory/search views.

**Why store `connections` as `min/max` instead of two rows?** The `UNIQUE(user_id_1, user_id_2)` constraint plus canonical ordering makes duplicate edges impossible without a separate direction table. Every insert path does `min()` / `max()`.

**Why `INSERT OR REPLACE` / `INSERT OR IGNORE` for profiles and conversations?** OTP verification can be retried after an interrupted registration; profile rows must not duplicate. `INSERT OR REPLACE` at `app.py:1132-1151`, `INSERT OR IGNORE` for connections.

**Why soft-delete messages?** Community archives matter. `is_hidden` / `deleted_by_sender` / `deleted_by_receiver` preserve data while removing it from the relevant view.

**Why are OTPs logged but never flashed?** The app must still be demoable when Gmail is rate-limited. `logger.warning(f'... OTP: {otp}')` at `app.py:1044`, `1244`, `2396`. **Strip this in production.**

**Why is the admin dashboard visually different from user dashboards?** Control-room aesthetic — dark hero `#030712`, JetBrains Mono, indigo/purple accents — to signal "this is an operator surface, not a community surface". Intentional, but it means two palettes exist in one product.

**Why a 2-minute registration OTP but a 10-minute reset OTP?** Registration is usually completed immediately; password reset may involve fetching a second code. Documented at `app.py:1015` vs `app.py:2372`.

**Why is `message_search_index` created but unused?** Reserved for an FTS migration. Currently `LIKE '%q%'` is used (`messaging_db.py:402`).

**Why does `scripts/init_postgres.py` exist but nothing use Postgres?** Vercel deployment was attempted. `config.py:31` reads `DATABASE_URL`, but `db_utils.py:10` hard-codes `sqlite3.connect()`. **The Postgres path is incomplete.**

---

## 5. Scoring Logic to Remember

### 5.1 Rule-Based Recommendations (`models/recommendation.py`)
```
Same branch                     +5
Skill overlap                   +5 per matching skill (case-insensitive, comma-split)
Same current_domain             +3
Passing year within 2 years     +4
Passing year within 4 years     +2
Same city                       +2
Mutual connections              +2 per mutual
─────────────────────────────────────
Excluded: self, accepted connections, pending requests
Target role: student→alumni, alumni→student
Output: top 5 sorted by score desc, each with a `reason` string
```

### 5.2 ML Weights (`services/recommendation_engine.py:44`)
```
Accepted connection   5   bidirectional
Private message       4   sender → receiver
Connection request    3   sender → receiver  (pending only)
Job application       2   student → job poster

user_interactions type weights:
  profile_view         1     job_click              2
  connection_request   3     mentorship_request     4
  message              4     (× occurrence count)

Cold start threshold: MIN_INTERACTIONS = 2
Cosine similarity → score = (1 − distance) × 100, clamped at 0
```

### 5.3 Job Recommendation
Pure skill-set intersection between `users.skills` and `jobs.required_skills`, top 5. No weighting, no semantic matching.

---

## 6. File-by-File Memory

| File | Remember |
| --- | --- |
| `app.py` | 4,875 lines. `send_email()` at :104 is the SMTP workhorse. `init_db()` at :298 is the whole schema. Module-level bootstrap at :4827–:4866. |
| `config.py` | `DB_NAME` default `data/college_pro.db`. `SESSION_COOKIE_SECURE = True` base, `False` in dev. `COURSE_CATEGORIES` has 8 categories × UG/PG/Diploma — used for register dropdowns. |
| `db_utils.py` | 14 lines. Uses `current_app` specifically to avoid importing `app`. |
| `database/messaging_db.py` | Own context manager, own `DB_NAME`. All messaging persistence. 527 lines. |
| `models/recommendation.py` | Phase-1 scoring. `get_recommended_users()` is the dashboard entry point and auto-delegates to hybrid. |
| `services/recommendation_engine.py` | Phase-2 ML. `_model_cache` global at :55. Locks at :61 and :203. |
| `services/admin_service.py` | `get_all_connections()` uses role predicates in `ON` clauses — copy that pattern. |
| `services/profile_service.py` | Only 88 lines; `update_user_profile()` is barely called (routes still do inline SQL). |
| `utils/helpers.py` | `PASSWORD_MIN_LENGTH = 8`, `OTP_LENGTH = 6`, `OTP_EXPIRY_SECONDS = 600` are the constants of record. |
| `utils/db.py` | Correct, documented, **unused**. Decide: adopt or delete. |
| `utils/decorators.py` | `@role_required()` imported at `app.py:25` but not actually applied to any route. |
| `routes/connection_routes.py` | Blueprint API — **duplicates** `app.py:3809+`. Pick one. |
| `routes/messaging_routes.py` | REST mirror of the Socket.IO surface. `get_private_msgs` is a placeholder. |
| `routes/websocket_routes.py` | `online_users` is a module-level dict → single-process only. |
| `routes/recommendation_routes.py` | Cleanest route file in the project. Use it as the template. |
| `templates/base.html` | 997 lines. Navbar branches on role at :228–:530. |
| `static/css/theme.css` | The intended design-token source. **Not linked from `base.html`.** |
| `templates/student/dashboard.html` | 2,399 lines — largest template. Hero + completeness + recommendations + 3 directories. |

---

## 7. Live Database Snapshot

`data/college_pro.db` — 19 tables, 25 named indexes (+11 implicit `UNIQUE` indexes).

| Table | Rows |
| --- | --- |
| `users` | 10 |
| `student_profile` | 6 |
| `alumni_profile` | 2 |
| `faculty_profile` | 1 |
| `registration_log` | 3 |
| `user_activity` | 11 |
| `connection_requests` | 2 |
| `jobs` | 1 |
| `password_resets` | 5 |
| `messaging_lock` | 1 |
| `connections` | 0 |
| `private_messages` | 0 |
| `public_messages` | 0 |
| `conversations` | 0 |
| `job_applications` | 0 |
| `user_interactions` | 0 |
| `alumni_meet_registration` | 0 |
| `temp_users` | 0 |
| `message_search_index` | 0 |

**Implications:**
- `connections` is empty → the ML matrix has no weight-5 signal.
- `user_interactions` is empty → `POST /recommendations/log` is not being called from the UI.
- `job_applications` is empty → the job-apply feature exists in schema but has no route.
- `private_messages` / `public_messages` are empty → messaging has not been exercised end-to-end in this DB.
- ⚠️ This file contains **real names, emails and phone numbers** and is tracked in git. Strip before publishing.

---

## 8. Schema Drift — The Live DB Is Not What `init_db()` Creates

`CREATE TABLE IF NOT EXISTS` means the live table definition wins on every existing install. The live `users` table has columns appended by `ALTER TABLE`:

```
… created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
, is_verified BOOLEAN DEFAULT 0, otp_code TEXT
, is_approved BOOLEAN DEFAULT 1, is_suspended BOOLEAN DEFAULT 0
, branch TEXT, passing_year INTEGER, current_domain TEXT
, skills TEXT, interests TEXT, city TEXT, company TEXT, bio TEXT
```

The live `jobs` table is a single-line `CREATE` plus 27 `ALTER TABLE` appends. Meanwhile `scripts/init_db.py` creates a **different, older** schema — notably `connections(user1_id, user2_id)` instead of `connections(user_id_1, user_id_2)`.

**Consequence:** a fresh install and a migrated install are not identical. Anything that assumes a column exists (without the guarded `ALTER`) will work on the dev machine and fail on a fresh clone.

---

## 9. Known Bugs (Verified in Code)

| # | Bug | Location | Impact |
| --- | --- | --- | --- |
| B1 | `url_for('faculty_dashboard')` — the endpoint is named `dashboard_faculty` | `app.py:4616` | **500 BuildError when a faculty member posts a job.** |
| B2 | `get_private_msgs(conversation_id)` returns a hard-coded placeholder | `routes/messaging_routes.py:201-217` | Endpoint is non-functional. |
| B3 | Messaging and app read different DB files | `database/messaging_db.py:10` vs `db_utils.py:9` | Silent data divergence. |
| B4 | `pywhatkit` is imported **before** the admin role check | `app.py:3475-3476` | Non-admins trigger a heavy import before being rejected. |
| B5 | POST exceptions flash `str(e)` to the user | `app.py:1050`, `1188`, `1911`, `2092` | Leaks internal detail, contradicting the project's own `safe_error_message()` rule. |
| B6 | Root-level and role templates duplicate the same pages | `templates/*.html` vs `templates/student|alumni/*.html` | Two sources of truth; fixes applied to one are missed in the other. |
| B7 | `scripts/optimize_db.py` creates indexes that duplicate `init_db()` indexes | `scripts/optimize_db.py` | Wasted write throughput. |
| B8 | ML model never refreshes after startup | `services/recommendation_engine.py` | Stale recommendations. |
| B9 | `online_users` presence is per-process | `websocket_routes.py:20` | Wrong presence under multiple workers. |
| B10 | `theme.css` never loaded | `base.html:56-60` | Design tokens are dead code; every page redefines them. |
| B11 | OTP values written to logs | `app.py:1044`, `1244`, `2396` | Security issue in production. |
| B12 | Mail password hard-coded + published in README | `app.py:50`, `README.md` §4 | Credential exposure. |

---

## 10. Environment & Credentials

```env
SECRET_KEY=<random>
FLASK_ENV=development          # or production
DB_NAME=data/college_pro.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<gmail address>
MAIL_PASSWORD=<16-char Google App Password>
ADMIN_EMAIL=<inbox for contact form + issue reports>
BASE_URL=http://localhost:5000
```

**Seeded Super Admin:** `admindbit195@college.edu` / `admindbit195@` — created by `init_db()` only when zero admin rows exist (`app.py:571-577`). Also hard-coded in `scripts/init_db.py:87`. **Rotate before any real deployment.**

**Gmail note:** `MAIL_PASSWORD` must be a Google **App Password** (16 chars, spaces stripped by `app.py:118-121`), not the account password. Two-factor on the Gmail account is mandatory to generate one.

---

## 11. How to Run

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000  (host 0.0.0.0, port 5000, allow_unsafe_werkzeug)
```

No migration step is required — `init_db()` runs on every boot. If the schema is corrupt:
```powershell
python scripts\init_db.py          # drops and rebuilds (destroys data)
python scripts\init_messaging_db.py
python scripts\optimize_db.py
```

Note: `requirements.txt` does **not** list `pywhatkit`, `psycopg2` or `Flask-SQLAlchemy`. `pywhatkit` is imported lazily and will fail at `/admin/whatsapp-send-api` if not installed. `psycopg2` is only needed for `scripts/init_postgres.py`.

---

## 12. Conventions Worth Preserving

- **Logger per module:** `logger = logging.getLogger(__name__)` at the top of every utility/service/model/route file.
- **Section banners in long files:** `# ───────── SECTION ─────────` (see `app.py`, `utils/helpers.py`, `websocket_routes.py`).
- **Docstrings on every non-trivial module**, with an explicit function list at the top (`utils/helpers.py:1-15`, `services/admin_service.py:1-11`).
- **Backward-compatibility wrappers** where a function was moved: `get_recommended_users()` wraps `hybrid_recommendation()` (`models/recommendation.py:193`).
- **Defensive `get_field(key)` readers** for columns that may not exist on older databases (`app.py:274`, `825`; `connection_routes.py:47`). Ugly, but intentional.
- **Role predicates in `ON` clauses** rather than `WHERE` (`admin_service.py:88-93`) — avoids cross-join row multiplication.
- **Backward-compatible migrations in the script layer**: scripts operate on `data/college_pro.db` *and* `data/alumni.db` (`migrate_jobs_v2.py:3`).

---

## 13. What This Project Is Actually Good At

Worth saying plainly, because it is genuinely strong work for an academic project:

1. **Consistent connection hygiene** — every route closes its connection, with no exceptions found.
2. **Real abstraction layers** — `utils/`, `services/`, `models/`, `database/`, `routes/` are real separations, not decorative folders.
3. **Graceful ML degradation** — missing scikit-learn, empty matrix, or fewer than 2 interactions all fall back cleanly. The recommender never breaks the app.
4. **A complete social lifecycle** — request → mutual → accept/reject → connection → gated chat → read receipts. Nothing is stubbed in that chain.
5. **Full-stack real-time** — WebSocket rooms, presence, typing indicators, admin monitoring, and a REST mirror over one persistence layer.
6. **Self-healing schema** — 19 tables and 25 named indexes maintained automatically on every boot with zero deploy steps.
7. **Coherent visual identity** — tokenised design, layered CSS, motion with intent, responsive down to mobile.
8. **Sensible query optimisation** — 20+ dashboard round trips collapsed into 2 `GROUP BY` queries, with indexes to match.

---

## 14. What to Watch For When Editing

| If you touch… | Then check… |
| --- | --- |
| `app.py` imports at the top | Circular imports with `db_utils`, `models`, `services` |
| `init_db()` | Every migration stays idempotent and guarded |
| `config.py` | `ProductionConfig` still reads `DATABASE_URL`; `SESSION_COOKIE_SECURE` untouched |
| `base.html` | All four role branches stay in sync; mobile menu mirrors desktop links |
| A new route | `@login_required` + explicit role check + `try/finally` close |
| `recommendation_engine.py` | `_model_cache` lock is held; cold start still returns `[]` |
| `websocket_routes.py` | Every handler has the auth guard; new events documented on both sides |
| `messaging_db.py` | Soft-delete flags respected in every `SELECT` (`is_hidden`, `deleted_by_*`) |
| A profile page | Owner-or-admin check present; photo upload validated |
| A job form field | Added to **both** `init_db()` column list and `extract_job_form_data()` |
| CSS | Uses `theme.css` tokens; new file linked from `base.html` |
| Any template | Extends `base.html`; no standalone document |

---

## 15. Open Questions for the Owner

1. Which deployment is authoritative right now — PythonAnywhere or Vercel? `vercel.json` exists but the Postgres path is unfinished, and `sitemap.xml` still points at PythonAnywhere.
2. Is `college_pro.db` at the repo root intentional, or leftover from the messaging factory's hard-coded path?
3. Should `job_applications` be wired up (the table exists, no route exists), or removed?
4. Should the feed (`posts`/`comments`/`likes`) be built or the defensive deletes removed?
5. Should `@role_required()` be adopted project-wide, or the inline checks formalised as the convention?
6. Is the `nav-dark-mode` class on `<body>` meant to become dark mode, or is it dead?
7. Should `data/college_pro.db` be committed at all, given it contains real PII?

---

## 16. Quick Reference Card

```
START        python app.py                    → http://127.0.0.1:5000
ADMIN        admindbit195@college.edu / admindbit195@
DB           data/college_pro.db   (live)     college_pro.db (root, stale)   data/alumni.db (empty)
ENTRY        app.py            NOT app.py:__main__ — module level is intentional
ROUTES       ~100 in app.py  +  4 blueprints
TABLES       20                INDEXES 26
ML           services/recommendation_engine.py   — trains once, cached forever
RT           routes/websocket_routes.py         — rooms: public_chat · user_<id> · admin_monitor
RULES        docs/Rules.md
DESIGN       docs/Design.md    TOKENS  static/css/theme.css (NOT LINKED)
TESTS        test_import.py only — real suite does not exist
BIGGEST RISK two DB files, hard-coded mail password, no tests
```