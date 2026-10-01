# Rules — Alumni Hub

> Coding, security, data and workflow rules this project follows.
> Each rule states **where it is enforced** in the code, so it can be verified rather than believed.

---

## 1. Architecture Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| AR-1 | **App bootstrap must live at module level, not inside `if __name__ == '__main__'`.** Blueprint registration, scheduler start, ML warm-up and DB migration all execute on import so Gunicorn/Vercel behave identically to `python app.py`. | `app.py:4827`, `app.py:4861` |
| AR-2 | **One responsibility per module.** `models/` = scoring logic, `services/` = business logic + ML, `routes/` = HTTP/Socket surface, `utils/` = reusable helpers, `database/` = persistence, `scripts/` = maintenance. | Directory layout |
| AR-3 | **Routes stay thin.** SQL lives in `models/`, `services/` or `database/`, never inline in a view. | `services/admin_service.py`, `database/messaging_db.py` |
| AR-4 | **Every new business-logic helper gets a module docstring** stating file purpose and a list of exported functions. | All of `utils/`, `services/`, `models/`, `routes/` |
| AR-5 | **No circular imports.** `db_utils` uses `current_app.config` (not importing from `app`) specifically to break the cycle. | `db_utils.py:7-9` docstring |
| AR-6 | **Blueprints are registered once, guarded by name check.** | `app.py:4835`, `4840`, `4843`, `4846` |
| AR-7 | **Heavy initialisation runs in a background daemon thread.** The ML model trains off the request path so the first request never blocks. | `services/recommendation_engine.py:469` |

---

## 2. Database Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| DB-1 | **All SQL is parameterised (`?` placeholders).** No string interpolation of user values into SQL. | Every `conn.execute(...)` in the codebase |
| DB-2 | **Dynamic `IN (...)` clauses build placeholders programmatically**, never concatenated values. | `models/recommendation.py:85-89`, `95-101`; `services/admin_service.py` |
| DB-3 | **Every route that opens a connection must close it in `finally`.** Pattern is fixed: `conn = None` → `try:` → `finally: if conn: conn.close()`. | All ~62 call sites; `app.py:866`, `1200`, `1292`, … |
| DB-4 | **On exception, `rollback()` before propagating or flashing.** | `app.py:185`, `2087`, `2320`, `2584` |
| DB-5 | **Rows are `sqlite3.Row`, not tuples** — enables both `row['col']` and tolerant `.get()`-style access for optional columns. | `db_utils.py:11`, `database/messaging_db.py:16` |
| DB-6 | **Read-only checks use `SELECT 1`, never `SELECT *`.** | `app.py:1720`, `3831`, `3840`, `3849`, `4033`, `4041`, `4049` |
| DB-7 | **WAL mode + `synchronous=NORMAL` + 20 s timeout on every connection.** Mandatory for concurrent Socket.IO messaging. | `db_utils.py:11-13`, `database/messaging_db.py:17-19`, `utils/db.py:44-47` |
| DB-8 | **Schema changes must be idempotent.** Use `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE … ADD COLUMN` wrapped in `try/except sqlite3.OperationalError` checking for `"duplicate column name"`, and `CREATE INDEX IF NOT EXISTS`. | `app.py:331-357`, `463-475`, `547-568`, `629-634` |
| DB-9 | **Never run a destructive migration without an explicit standalone script.** `scripts/init_db.py` deletes the DB file; nothing in the app path does. | `scripts/init_db.py:14-16` |
| DB-10 | **Connection pairs are stored canonically as `min(user_id_1, user_id_2)`.** Required by the `UNIQUE(user_id_1, user_id_2)` constraint. | `app.py:3862-3863`, `3932-3934`; `database/messaging_db.py:232-233`, `256-257`, `474-475` |
| DB-11 | **Soft delete over hard delete for messages.** Use `deleted_by_sender` / `deleted_by_receiver` / `is_hidden` flags, never `DELETE FROM`. | `database/messaging_db.py:171`, `183`, `345` |
| DB-12 | **Role-specific tables are joined with the role predicate in the `ON` clause**, not `WHERE`, to avoid row multiplication. | `services/admin_service.py:88-93`, `app.py:1626-1628`, `1809-1812` |
| DB-13 | **Aggregate queries must use a single `GROUP BY`**, never per-row or per-year `COUNT` loops. | `app.py:1634`, `1647`; `services/admin_service.py:190`, `212` |
| DB-14 | **Every hot-path column must be indexed**, and the index list lives in `init_db()` so fresh installs match migrated ones. | `app.py:547-563` |
| DB-15 | **A user can never be deleted from the platform if they own the Super Admin email.** | `app.py:2982-2984` |

---

## 3. Security Rules

### 3.1 Authentication

| # | Rule | Enforced At |
| --- | --- | --- |
| SEC-1 | **Passwords are stored only as Werkzeug salted hashes** (`generate_password_hash`). Plaintext passwords are never persisted, never logged, never emailed. | `app.py:575`, `907`, `1121`, `2469`, `2516` |
| SEC-2 | **Minimum password length is 8 characters**, enforced by one shared function, not inline checks. | `utils/helpers.py:33 PASSWORD_MIN_LENGTH = 8`, `:199 validate_password()` |
| SEC-3 | **OTPs are 6 cryptographically random digits** from `secrets.choice`, not `random`. | `utils/helpers.py:44`, `app.py:962`, `1217`, `2342` |
| SEC-4 | **An OTP must never appear in a `flash()` message or any HTML response.** It goes to the server log only. | `app.py:1044`, `1244`, `2396` use `logger.warning(...)` |
| SEC-5 | **OTPs are time-limited** — 2 minutes for registration, 10 minutes for password reset — and expired tokens are deleted. | `app.py:987`, `1086-1092`; `app.py:2427`; `utils/helpers.py:35 OTP_EXPIRY_SECONDS` |
| SEC-6 | **Password-reset tokens are single-use** — the row is deleted on successful verification. | `app.py:2432` |
| SEC-7 | **Login enforces approval and suspension state** before creating a session. | `app.py:837` (approval), `842` (suspension) |
| SEC-8 | **Sessions are `HttpOnly`, `Secure` (production) and expire after 1 hour.** | `config.py:12-14` |

### 3.2 Authorisation

| # | Rule | Enforced At |
| --- | --- | --- |
| SEC-9 | **Every non-public route requires `@login_required`.** | All protected routes |
| SEC-10 | **Every admin route re-checks `current_user.role != 'admin'`** even when registered behind `@login_required`. | `app.py:1383`, `1401`, `1611`, `1744`, `2597`, `2628`, … |
| SEC-11 | **Ownership checks follow the pattern `current_user.id != user_id and current_user.role != 'admin'` → deny.** | `app.py:2026`, `2101`, `2193`, `2267` |
| SEC-12 | **`@role_required(*roles)` is the preferred access-control decorator**; it returns JSON 403 for `/api/` paths and a flash+redirect for HTML paths. | `utils/decorators.py:26` |
| SEC-13 | **Resource-scoped gates go beyond role checks.** Private chat requires an accepted `connections` row (admin exempt). | `app.py:1718-1726` |
| SEC-14 | **Cross-user data reads are restricted** — `/recommendations/<user_id>` is self-or-admin only. | `routes/recommendation_routes.py:64` |
| SEC-15 | **Suspended users cannot authenticate**, because `User.is_active` derives from `is_suspended`. | `app.py:259-261` |

### 3.3 Input, Output & Files

| # | Rule | Enforced At |
| --- | --- | --- |
| SEC-16 | **Jinja2 autoescaping is on (never disable it).** Explicit HTML escaping of user content goes through `sanitize_html()` → `markupsafe.escape`. | `utils/helpers.py:189` |
| SEC-17 | **Registration accepts only `@gmail.com` addresses.** | `app.py:891-893` |
| SEC-18 | **Every form field is trimmed and required-checked before use**, with an explicit missing-field list. | `app.py:919-925`, `936-943`, `952-959` |
| SEC-19 | **Uploads are restricted to an extension whitelist** (`png`, `jpg`, `jpeg`, `gif`) and sanitised with `secure_filename`. | `app.py:67`, `81`; `utils/helpers.py:31`, `52`, `78` |
| SEC-20 | **Request body is capped at 16 MB** to prevent memory-exhaustion uploads. | `app.py:76` |
| SEC-21 | **Upload directories are created on startup if missing.** | `app.py:71-74`; `utils/helpers.py:82`, `110` |
| SEC-22 | **Internal error detail is never returned to the user.** Use `safe_error_message()` or a generic message; log the full trace server-side. | `utils/helpers.py:177`; `app.py:396`, `768`, `1762` |
| SEC-23 | **Secrets must come from environment variables.** Never commit `.env`. | `config.py:8`, `app.py:45-52`; `.gitignore` contains `.env` |
| SEC-24 | **Phone numbers must not be exposed in rendered HTML.** WhatsApp contact goes through a server-side bridge route. | `app.py:4353` bridge → `app.py:4372` jump → `templates/contact_bridge.html` |
| SEC-25 | **Credentials are never hard-coded.** ⚠️ Currently violated: `app.py:50` `MAIL_PASSWORD` fallback and `app.py:575` seed admin password are both in source. Must be externalised before deployment. | `app.py:50`, `575`; `README.md` §4 |
| SEC-26 | **The seeded Super Admin credential must be rotated before any real deployment.** | `README.md:204-208` |

---

## 4. Frontend Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| FE-1 | **Every page extends `base.html`.** No standalone full HTML documents outside `base.html`. | All 60+ templates |
| FE-2 | **Role-aware navbar items live in `base.html`**, branching on `current_user.role`. Adding a role means adding a branch there. | `base.html:228-530` |
| FE-3 | **CSS is layered, not inlined.** Page-specific styles go into a dedicated file under `static/css/`; only truly one-off rules use a scoped `<style>`. | 13 files in `static/css/` |
| FE-4 | **Reuse the design tokens from `theme.css` `:root`** instead of hard-coding hex values in new components. | `static/css/theme.css:1-66` |
| FE-5 | **Icons come from FontAwesome 6**; never inline custom SVG icon markup. | `base.html:41` |
| FE-6 | **Bootstrap 5 is the layout system.** Custom CSS may restyle Bootstrap, not fight it. | `base.html:44` |
| FE-7 | **Interactive data uses `fetch()` with `async/await`** and handles the JSON error branch. | `templates/messaging/*.html`, dashboards |
| FE-8 | **Real-time features must use Socket.IO rooms/events defined in `websocket_routes.py`.** Do not invent new event names ad hoc. | `routes/websocket_routes.py` |
| FE-9 | **Animations must be GPU-accelerated** (transform/opacity only) to hold 60 fps. | `static/css/animations.css` |
| FE-10 | **Scroll-triggered counters guard against re-trigger** using a `dataset` flag. | `static/js/animations.js`; documented in README |
| FE-11 | **Every page must carry the full SEO block** (description, keywords, OG, Twitter, canonical). | `base.html:8-32` |
| FE-12 | **Layout must remain responsive down to 360 px.** Grids collapse, split forms stack, hero typography scales. | Media queries across `static/css/*` |
| FE-13 | **User-facing notifications use the `alerts-container` block with an auto-dismiss timeout**, not `alert()`. | `base.html:733-747` |

---

## 5. Email Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| MAIL-1 | **All outbound mail goes through `send_email()` or Flask-Mail.** Never call `smtplib` inline from a route. | `app.py:104 send_email()` |
| MAIL-2 | **Email failure must never break the user flow.** Wrap sends in `try/except`, log a warning, continue. | `app.py:801-804`, `1109`, `188`, `3866-3869` |
| MAIL-3 | **Never embed a secret in an email body or subject.** | — |
| MAIL-4 | **Emails that contain user-supplied text must not render it as raw HTML** (Jinja2 templates escape; inline f-string HTML must escape user values). | `templates/emails/*.html` |
| MAIL-5 | **Every OTP / transactional email includes an expiry notice and a security warning.** | `app.py:1015`, `1020` |
| MAIL-6 | **Sender identity is fixed as `('ALUMNI HUB', MAIL_DEFAULT_SENDER)`** for consistency. | `app.py:52`, `routes/connection_routes.py:105` |
| MAIL-7 | **SMTP credentials are read from env and stripped of surrounding quotes** before use. | `app.py:118-121` |

---

## 6. Recommendation / ML Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| ML-1 | **The engine is two-phase and must stay two-phase.** Phase 1 (rule-based) is always available; Phase 2 (ML) is an enhancement layered on top. | `models/recommendation.py`, `services/recommendation_engine.py` |
| ML-2 | **ML must never be a hard dependency.** Missing numpy/scikit-learn, an empty matrix, or a training error must degrade to rule-based silently. | `services/recommendation_engine.py:253`, `:219`, `:219`, `models/recommendation.py:205-210` |
| ML-3 | **The model is trained once and cached**, with a 5-minute guard on non-forced retrains. | `services/recommendation_engine.py:203-207` |
| ML-4 | **Training must never run on the request path.** Only the admin retrain endpoint may do it synchronously; startup uses a daemon thread. | `services/recommendation_engine.py:477-488`, `routes/recommendation_routes.py:93` |
| ML-5 | **Cold start is explicit.** A user with fewer than `MIN_INTERACTIONS = 2` signals gets no ML results and falls through to rule-based. | `services/recommendation_engine.py:50`, `:298` |
| ML-6 | **Interaction weights are named module constants**, never inline magic numbers. | `services/recommendation_engine.py:44-47` |
| ML-7 | **Every recommendation must exclude self, accepted connections and pending requests.** | `models/recommendation.py:62-77`, `services/recommendation_engine.py:312-327` |
| ML-8 | **Matching is cross-role: students see alumni, alumni see students.** Faculty/admin are never recommended. | `models/recommendation.py:55-59`, `services/recommendation_engine.py:334`, `348` |
| ML-9 | **Every recommendation carries a numeric `score`, a human-readable `reason`, and a `source` tag** (`'ml'` or `'rule'`). | `models/recommendation.py:169-180`, `services/recommendation_engine.py:354-365`, `416`, `426` |
| ML-10 | **Results are deduplicated by user id and sorted by score descending, capped at the requested limit.** | `services/recommendation_engine.py:410-438` |
| ML-11 | **The ML cache is guarded by a `threading.Lock`** because training can be triggered from the background thread and an admin request simultaneously. | `services/recommendation_engine.py:61`, `203` |
| ML-12 | **Interaction logging must be best-effort** — a failure must never break the calling UI. | `services/recommendation_engine.py:129-131`, `routes/recommendation_routes.py:131` |

---

## 7. Logging Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| LOG-1 | **Use the `logging` module, not `print()`, for diagnostics.** A module-level `logger = logging.getLogger(__name__)` per file. | `app.py:35-36`, `utils/helpers.py:26`, `utils/db.py:27`, `services/*.py`, `models/recommendation.py:22`, `routes/recommendation_routes.py:23` |
| LOG-2 | **Never log secrets, passwords, OTPs intended for users, or full DB dumps.** ⚠️ Currently violated: `app.py:1044`, `1244`, `2396` log the OTP. This is intentional for local recovery but must be removed in production. | `app.py:1044`, `1244`, `2396` |
| LOG-3 | **Errors get `logger.error(...)`; degraded-but-handled states get `logger.warning(...)`; expected-absent resources get `logger.debug(...)`.** | `services/recommendation_engine.py:134`, `148`, `170`, `219`; `utils/helpers.py:170`, `182` |
| LOG-4 | **Every error handler must return a safe, user-readable message.** | `utils/helpers.py:177 safe_error_message()` |
| LOG-5 | **Log format is centralised at app start.** | `app.py:35` `logging.basicConfig(...)` |

---

## 8. Validation Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| VAL-1 | **Validate server-side.** Client-side JS validation is a UX convenience only, never the authority. | `app.py:2043-2045`, `2120-2122`, `2210-2212` |
| VAL-2 | **On validation failure, re-render the form with existing data — never silently redirect and lose input.** | `app.py:2050`, `2127`, `2217` |
| VAL-3 | **Missing required fields are enumerated by name** so the user knows exactly what to fix. | `app.py:924`, `938`, `953` |
| VAL-4 | **Message content is capped at 5,000 characters** and empty content is rejected at both HTTP and Socket layers. | `routes/messaging_routes.py:78`, `174`; `routes/websocket_routes.py:101`, `222` |
| VAL-5 | **Self-targeting is always rejected** — connection requests, messages, conversations. | `app.py:3818`, `4026`; `routes/messaging_routes.py:180`, `284`; `routes/websocket_routes.py:226` |
| VAL-6 | **Phone numbers are normalised to a canonical `+91XXXXXXXXXX` form** before use in links. | `utils/helpers.py:122 normalize_phone()`; `app.py:3452-3456`, `3488-3503` |
| VAL-7 | **JSON API responses always include an explicit success flag and error message.** | All `routes/*.py` and `jsonify` calls in `app.py` |

---

## 9. Code Style Rules

| # | Rule |
| --- | --- |
| STY-1 | 4-space indentation, no tabs. |
| STY-2 | snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants. |
| STY-3 | Type hints on utility and service function signatures where the codebase already does (`utils/helpers.py`, `utils/db.py`). |
| STY-4 | Docstrings on every module in `utils/`, `services/`, `models/`, `routes/`, `database/`, `scripts/`. |
| STY-5 | Imports grouped: stdlib → third-party → local, separated by blank lines. |
| STY-6 | Explicit `logger = logging.getLogger(__name__)` instead of relying on the root logger. |
| STY-7 | Prefer f-strings for message formatting. |
| STY-8 | Section banner comments for long files: `# ---- SECTION ----` (matches `app.py`, `utils/helpers.py`). |
| STY-9 | No dead code — if a table or route is a placeholder, either implement it or remove it. ⚠️ Currently violated by `get_private_msgs` placeholder (`routes/messaging_routes.py:201-217`) and the unused `message_search_index` table. |
| STY-10 | Comments explain *why*, not *what*. |

---

## 10. Git & Collaboration Rules

| # | Rule | Evidence |
| --- | --- | --- |
| GIT-1 | **Never commit `.env`** — it holds `SECRET_KEY` and mail credentials. | `.gitignore` |
| GIT-2 | **Never commit `__pycache__/`.** | Present in the working tree but should be ignored |
| GIT-3 | **Uploaded user media (`static/uploads/`) is gitignored in principle** — only `.gitkeep` should be tracked. | `static/uploads/.gitkeep` exists; ⚠️ 17 uploaded files are currently tracked |
| GIT-4 | **Never commit real user data.** `data/college_pro.db` currently contains 10 real user rows, real emails and phone numbers. Must be stripped or gitignored before publishing. | `data/college_pro.db` |
| GIT-5 | **Write conventional, imperative commit messages** (`fix: close db connection in private_chat`). |
| GIT-6 | **One logical change per commit.** |
| GIT-7 | **Never commit binary `.db` diffs** — add `*.db` to `.gitignore` and ship `scripts/init_db.py` as the source of truth. | `scripts/init_db.py` exists for exactly this |
| GIT-8 | **Branch per feature**, merge via PR with review. |

---

## 11. Testing Rules

| # | Rule | Current State |
| --- | --- | --- |
| TST-1 | Every new route must have at least one success + one failure-path test using `app.test_client()`. | ❌ No test suite exists |
| TST-2 | Test role authorisation explicitly: student must get 403 on admin routes, alumni must get 403 on student-only routes. | ❌ Not covered |
| TST-3 | Test connection lifecycle end-to-end: send → pending → accept → connection row exists → private chat unlocked. | ❌ Not covered |
| TST-4 | Test recommendation cold start and hybrid merge determinism. | `scripts/test_recommendations.py` exists (63 lines) |
| TST-5 | Test that OTP never appears in any response body. | ❌ Not covered |
| TST-6 | Run `python test_import.py` (import smoke check) before any push. | ✅ Exists |
| TST-7 | Manually verify DB connections are closed (no `database is locked` under concurrent load). | Manual |

---

## 12. Deployment Rules

| # | Rule | Evidence |
| --- | --- | --- |
| DEP-1 | **Rotate the seeded Super Admin password and the mail app-password before first real deployment.** | `README.md:204-208`, `app.py:575` |
| DEP-2 | **`SECRET_KEY` must be set explicitly in production** — never rely on the dev default. | `config.py:8` |
| DEP-3 | **`SESSION_COOKIE_SECURE = True` in production** (already set in `Config`, overridden only in `DevelopmentConfig`). | `config.py:12`, `25` |
| DEP-4 | **Serve via Gunicorn (`Procfile`), not the Flask dev server.** | `Procfile` |
| DEP-5 | **Migrations run automatically on boot** — no separate deploy step. | `app.py:4861` |
| DEP-6 | **Static uploads require a persistent filesystem.** Serverless needs an external object store. | `vercel.json` limitation |
| DEP-7 | **Do not deploy to Vercel until a real PostgreSQL driver is wired into `get_db_connection()`.** | `vercel.json`, `config.py:31`, `scripts/init_postgres.py` |
| DEP-8 | **`DEBUG` must be `False` in production.** | `config.py:28` |
| DEP-9 | **Keep `robots.txt` and `sitemap.xml` in sync with the live domain** when deploying to a new host. | Currently hard-coded to `dbitalumni.pythonanywhere.com` |

---

## 13. Performance Rules

| # | Rule | Enforced At |
| --- | --- | --- |
| PF-1 | **No `COUNT(*)` inside a Python loop.** Use one `GROUP BY`. | `app.py:1634`, `1647` |
| PF-2 | **No N+1 query patterns.** Pre-fetch related sets in one query and join in Python. | `models/recommendation.py:96-109` pre-fetches all candidate connections |
| PF-3 | **Cap result sets.** `LIMIT 50` on user search, `LIMIT 5` on recommendations, `LIMIT 50/100/200` on messages. | `app.py:3563`, `models/recommendation.py:183`, `routes/messaging_routes.py:106` |
| PF-4 | **Cache expensive computation** (the KNN model) in module scope rather than per-request. | `services/recommendation_engine.py:55` |
| PF-5 | **Lazy-load heavy/optional imports** inside the function that needs them. | `app.py:3475` (`import pywhatkit`), `services/recommendation_engine.py:210` (sklearn) |
| PF-6 | **Use `SELECT 1` for existence checks.** | `app.py:1720` and connection endpoints |
| PF-7 | **Keep SQLite pragmas tuned for concurrency** — WAL + `synchronous=NORMAL` + 20 s timeout. | `db_utils.py:11-13` |
| PF-8 | **Index any column used in a `WHERE`, `ORDER BY` or `GROUP BY` on a hot table.** | `app.py:547-563` |
| PF-9 | **Move work off the request thread** for anything over ~100 ms. | ML training in a daemon thread |

---

## 14. Rules That Are Currently Violated (Action Required)

| # | Rule | Violation | Fix |
| --- | --- | --- | --- |
| SEC-25 | No hard-coded credentials | `app.py:50` mail password fallback; `README.md` §4 publishes it | Move to `.env`, rotate the app password |
| SEC-26 | Rotate seeded admin | `admindbit195@college.edu` / `admindbit195@` is public | Force a password change on first admin login |
| DB-3 | One DB file | `db_utils` → `data/college_pro.db`; `messaging_db` → `./college_pro.db` | Point both at `current_app.config['DB_NAME']` |
| DB-14 | No duplicate indexes | `idx_connections_u1/u2` vs `idx_connections_user1/user2`; `idx_connreq_*` vs `idx_connection_requests_*` | Consolidate in `init_db()`, drop the rest |
| LOG-2 | Don't log OTPs | `app.py:1044`, `1244`, `2396` | Keep for local dev, strip in production |
| LOG-1 | Use logging | ~60 `print()` calls remain in `app.py`, `connection_routes.py`, `websocket_routes.py` | Convert during refactor |
| STY-9 | No dead code | `get_private_msgs` placeholder; unused `message_search_index`; `utils/db.py` unused; `send_user_activity` unused | Implement or delete |
| TST-1 | Tests required | No automated tests | Add pytest + `app.test_client()` |
| GIT-4 | No real user data | `data/college_pro.db` holds 10 real accounts | Strip PII or gitignore |
| DEP-7 | No serverless deploy yet | No Postgres driver in the runtime path | Add psycopg2 branch in `get_db_connection()` |
| AR-5 | Thin routes | `app.py` holds ~100 routes + all SQL | Split into `routes/*.py` blueprints |
| — | Working bug | `app.py:4616` `url_for('faculty_dashboard')` — endpoint is `dashboard_faculty` | Fix to `dashboard_faculty` |
| — | Working bug | `app.py:4616` is only reached when faculty posts a job | Test the faculty job-posting path |