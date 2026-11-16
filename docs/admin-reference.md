# Alumni Hub — Admin Area Reference

> Read-only reference for viva preparation. Source: `/home/hatch/workspace/alumni-hub-checkout`
> (GitHub main, commit `e176ddf`). Nothing was edited, deleted or pushed while
> compiling these notes.
>
> Project: **Alumni Hub v1.0** (MCA Major Project) — Flask 2.3.2 + SQLite (WAL) +
> Flask-SocketIO + Scikit-Learn. Lead developer / backend: Rajender Mohan Verma.
> Live: https://alumni-hub-psi.vercel.app/ · Repo: https://github.com/RajenderMohanVerma/alumni-hub

## 0. Admin overview (short version)

**Who the admin is.** The Super Admin is the root authority of the whole
platform. Only an admin can: approve or reject alumni/faculty registrations,
approve or reject job postings, suspend users or messaging, moderate the
public chat, monitor live connections, send WhatsApp broadcasts, export the
user database, and view analytics, registrations, events and incident tickets.
Students, alumni and faculty can never reach these pages — every admin route
is guarded by `@login_required` plus a `current_user.role != 'admin'` check
(flash + redirect home, or JSON 403 for API routes; `abort(403)` is **not**
used anywhere in the admin routes).

**Where admin code lives.**

| Layer | Files |
|---|---|
| Templates (15 files) | `templates/admin/*.html` — 14,278 lines total |
| Routes | `app.py` — 23 routes under `/admin/*`, plus admin-only `/api/admin/*` routes |
| Service layer | `services/admin_service.py` — 293 lines, 6 functions |
| Shell / nav | `templates/base.html` (3,155 lines) — admin desktop nav, user pill, mobile drawer |
| Messaging APIs | `routes/messaging_routes.py` (blueprint, prefix `/api`), `database/messaging_db.py` |

**Design system (shared by all 15 admin pages).** Every admin template
`{% extends 'base.html' %}`, loads Google Fonts **Outfit / Plus Jakarta Sans /
JetBrains Mono** and `static/css/admin-luxury.css?v=2.4`, and uses Font
Awesome icons. The shell is `.admin-page-wrapper` → 3 ambient orbs
(`.admin-ambient-ball admin-ball-1/2/3`) → `.admin-container` → dark
holographic hero card (`.admin-hero-card`) with an `.admin-live-badge` and a
pulsing `.live-pulse-dot`.

- **Indigo (admin primary):** `#4f46e5` / `#6366f1`; role colours — student
  sky/blue `#0284c7`, alumni amber `#f59e0b` / `#d97706`, faculty emerald
  `#10b981` / `#059669`, admin purple `#7c3aed` / `#4f46e5`, danger rose
  `#ef4444`.
- **Hero:** dark navy gradient `linear-gradient(135deg, #0b1329 0%, #172554 48%,
  #0f172a 100%)`, holographic title gradient `#38bdf8 → #818cf8 → #c084fc`
  (`.text-holographic-adm`), white cards, 18–28 px radii, soft shadows,
  hover lift `translateY(-5px)`.
- **Glassmorphism** (strongest on Analytics): `rgba(17,24,39,0.72)` panels,
  `backdrop-filter: blur(16px)`, `1px rgba(255,255,255,0.08)` borders.
- **Admin badge:** shield icon (`fa-shield-alt` / `fa-shield-halved`), ADMIN
  tag in obsidian `#0f172a` with amber-gold `#fbbf24` text; green pulse beacon
  (`admin-pulse-beacon`, `#10b981`, 2 s pulse) on the logo, "Security Active".
- **Charts:** Chart.js 4.4.1 CDN, used on Dashboard, Analytics and Stats
  only. **Live features are uneven** — see the per-page notes and §4: only
  the Connection Monitor uses Socket.IO; Messaging Control polls every 15 s;
  Reports polls every 12 s; Dashboard/Analytics/Stats are server-rendered on
  load ("Live" badges are presentation labels, except the dashboard clock
  and particle canvas).

**Admin route catalogue (23 routes, `app.py`).**

| Line | Method | Route | Function | Renders / returns |
|---|---|---|---|---|
| 1468 | GET | `/admin/profile/<int:user_id>` | `admin_profile` | `admin/profile_admin.html`, `user` |
| 1493 | GET | `/admin/users/<role>` | `admin_view_users` | `admin/admin_view_users.html`, `users, role, stats` |
| 1522 | GET | `/admin/approve-requests` | `admin_approve_requests` | Same template, `role='pending'` |
| 1739 | GET | `/admin/dashboard` | `dashboard_admin` | `admin/dashboard_admin.html`, `users, a_count, s_count, f_count, event_total, chart_data` |
| 1870 | GET | `/admin/messaging-control` | `admin_messaging_control` | `admin/admin_messaging_control.html` (no context) |
| 1881 | GET | `/admin/connection-monitor` | `admin_connection_monitor` | `admin/connection_monitor.html`, `records, role_filter, search, total_records` |
| 1915 | GET | `/admin/connection-monitor/user/<int:user_id>` | `admin_connection_monitor_user` | JSON `{'user': payload}` |
| 2383 | GET, POST | `/admin/profile/<int:user_id>/edit` | `edit_admin_profile` | `admin/edit_admin_profile.html` |
| 2670 | GET | `/admin/verify-user/<int:user_id>/<action>` | `verify_user` | JSON or flash+redirect (approve/block) |
| 2712 | GET | `/admin/analytics` | `admin_analytics` | `admin/admin_analytics.html`, `stats` dict |
| 2756 | GET | `/admin/registrations` | `admin_registrations` | `admin/admin_registrations.html`, `registrations, stats, current_filter, search_query` |
| 2816 | GET | `/admin/export/registrations` | `admin_export_registrations` | CSV download |
| 3196 | GET | `/admin/jobs` | `admin_jobs` | `admin/jobs.html`, `jobs, pending_jobs, stats` |
| 3250 | POST | `/admin/jobs/approve/<int:job_id>` | `admin_approve_job` | JSON + Socket.IO emit |
| 3279 | POST | `/admin/jobs/reject/<int:job_id>` | `admin_reject_job` | JSON + Socket.IO emit |
| 3352 | GET, POST | `/admin/jobs/add` | `admin_add_job` | `admin/add_job.html` |
| 3441 | GET, POST | `/admin/jobs/edit/<int:job_id>` | `admin_edit_job` | `admin/edit_job.html`, `job` |
| 3527 | GET, POST | `/admin/whatsapp-broadcast` | `admin_whatsapp_broadcast` | `admin/whatsapp_broadcast.html`, `users, selected_role, message, auto_start` |
| 3589 | POST | `/admin/whatsapp-send-api` | `admin_whatsapp_send_api` | JSON (pywhatkit send) |
| 3644 | POST | `/admin/jobs/delete/<int:job_id>` | `admin_delete_job` | Flash + redirect `admin_jobs` |
| 4996 | GET | `/admin/reports` | `admin_reports` | `admin/reports.html`, `tickets, total_count, pending_count, in_progress_count, resolved_count` |
| 5205 | GET | `/admin/events` | `admin_events` | `admin/admin_events.html` (no context) |
| 5213 | GET | `/admin/stats` | `admin_stats` | `admin/admin_stats.html` (no context) |

Adjacent admin-only API routes (not under `/admin/*`): `POST
/api/admin/jobs/toggle/<id>` (`app.py:3329`, flips `is_active`),
`GET /api/admin/reports/live` (5073), `POST
/api/admin/reports/<id>/status` (5113), `POST
/api/admin/reports/<id>/delete` (5150), `POST /api/approve-user/<id>`
(5167), `POST /api/reject-user/<id>` (5184, deletes profile rows + user),
`POST /api/delete-user/<id>` (3090, admin-only, protected super-admin
accounts return 403). Messaging APIs live under `/api/admin/messaging/*`
in `routes/messaging_routes.py` (blueprint registered in `app.py:5317`,
prefix `/api`).

---

## 1. Dashboard — Executive Command Center

- **Route:** `GET /admin/dashboard` — `app.py:1739`, `dashboard_admin()`
  (lines 1739–1831). `@login_required`; non-admins redirected home. DB
  connection closed in `finally`.
- **Template:** `templates/admin/dashboard_admin.html` — **2,988 lines** (largest
  admin page). Title: `Admin Dashboard • Executive Command Center`.
- **Assets:** Outfit / Plus Jakarta Sans / JetBrains Mono; `css/home-premium.css?v=2.3`,
  `css/admin-luxury.css?v=2.4`; Chart.js 4.4.1 CDN at the bottom.
- **Hero:** badge `ADMIN COMMAND CENTER • LIVE CONTROL`; H1 `Welcome Back,
  {{ current_user.name }}` (name span `id="typingName"` — no typing script
  exists, the name is just rendered). Subtitle: *"Complete campus ecosystem
  administration. Monitor community enrollments, approve credentials, oversee
  recruitment drives, and inspect real-time platform metrics."* Hero card
  `.admin-hero-card` — dark navy gradient, 2 px `rgba(56,189,248,0.25)`
  border, 30 px radius, `<canvas id="networkCanvas">` particle network
  (opacity 0.32, ≤30 particles), and a glass **System Time clock box**
  (`.admin-clock-box`, live JS clock `id="dynamicClock"` / date
  `id="dynamicDate"`, pills `Turso / SQLite` and `256-Bit SSL`, `ACTIVE`
  badge). Hero buttons: Send Broadcast → messaging control; Pending
  Approvals → approve-requests; Job Matrix → admin jobs; WhatsApp →
  whatsapp-broadcast.
- **Layout in order:**
  1. Hero command terminal (above).
  2. Four VIP Role Matrix stat cards (`.admin-matrix-card`, clickable, top
     accent strips blue/amber/green/purple): Students `{{ s_count }}` (78%
     bar), Alumni `{{ a_count }}` (65%), Faculty `{{ f_count }}` (50%),
     Event Registrations `{{ event_total }}` (82%). Link to user directory
     per role / admin events.
  3. Quick Control Deck (`.action-deck-grid`, 4 cols → 2 on mobile) — 8
     tiles: Approvals, All Users, Jobs Board, Broadcasts, WhatsApp Desk,
     Events Desk, Connection Graph, Deep Analytics.
  4. Analytics & Growth Center — `5-Year User Growth Trajectory` (line
     chart) + `Role Ratio` (doughnut), badge `Live Real-Time Feed`.
  5. User Directory & Governance (`.directory-vip-module`,
     `id="userDirectoryModule"`) — Cards/Table view toggle (`btnViewCards` /
     `btnViewTable`, `setDirectoryViewMode()`; preference in `localStorage`
     key `admin_dir_view_mode`), role quick-chips (All / Students / Alumni /
     Faculty / Admins), search `#userSearch` (*"Search name, email,
     department..."*), role select `#roleFilter`, date `#dateFilter`, sort
     `#sortFilter` (Newest/Oldest/Name A–Z/Z–A), desktop table `#usersTable`
     (User Profile, Role, Department & Batch, Date & Status, Actions) and a
     separate mobile cards grid `#mobileUsersGrid` (≤768 px). Pagination:
     **12 per page** (`PAGE_SIZE = 12`), max 5 page numbers with `...`.
     Empty state `#noUserResults` ("No Members Found").
  6. Data Export & Backup Center (`.export-vip-module`) — tabs `#exportTabs`:
     **CSV Spreadsheets** (`#csvExports`): Student Registry, Alumni
     Directory, Omni-Registry Master — `downloadData('student'|'alumni'|'all',
     'csv')` → `/api/download-csv/<role>`; **Database Backups**
     (`#dbExports`): Primary Database (`college_pro.db`, `RESTRICTED`) and
     Secondary Database (`alumni.db`, `ENCRYPTED`) — `downloadData(..., 'db')`
     → `/api/download-db/<db_type>` (route at `app.py:3013`).
  7. Scripts — live clock (1 s interval), particle canvas, Chart.js init,
     directory filter/sort/paginate engine, `copyUserEmail()`,
     `confirmDelete(id, name, btn)` → `POST /api/delete-user/<id>` then
     reload, `downloadData()`.
- **Backend data passed** (`render_template`, ~`app.py:1825`): `users` (all
  users `ORDER BY id DESC`, with `department` via
  `COALESCE(student/alumni/faculty department, 'N/A')`, `batch_info` =
  student semester or alumni pass year, `profile_pic`, `phone`,
  `created_at`), `a_count`, `s_count`, `f_count` (one `GROUP BY role`
  query), `event_total` (sum of yearly `alumni_meet_registration` counts —
  counts registrations, not events), `chart_data` =
  `{'years': [current_year-4 … current_year], 'students': [...], 'alumni':
  [...], 'faculty': [...]}` (one `strftime('%Y', created_at)` GROUP BY
  query; events query in try/except `sqlite3.OperationalError`). Note:
  `events_data` is computed but **not** passed to the template.
- **Actions:** No `<form>` — all actions are links/buttons/JS: per-role
  profile links, per-user View (eye) and Delete (trash, confirm dialog
  *"Are you sure you want to delete member: …? This action cannot be
  undone."*), mobile-card WhatsApp (`https://wa.me/<phone>`), `mailto:`,
  `tel:`, 1-tap copy-email capsule, CSV/DB downloads. Protected super-admin
  accounts show a `PROTECTED` badge instead of delete (mobile view gives a
  `Console` link to `admin_profile`).
- **Charts (Chart.js 4.4.1):** `#growthChart` — line, 3 datasets Students
  (#0284c7), Alumni (#f59e0b), Faculty (#10b981), `tension: 0.38`, `fill:
  true`, labels = 5-year `chart_data.years`; data fed via hidden `<div
  id="chart-data">` (`data-years`, `data-students-growth`, … `| tojson`,
  parsed with `JSON.parse`). `#userChart` — doughnut, Students/Alumni/
  Faculty, data `[s_count, a_count, f_count]`, colours
  `['#0284c7', '#f59e0b', '#10b981']`, `cutout: '72%'`, legend bottom.
- **Live features:** live clock, particle canvas, animated progress bars,
  client-side directory search/filter/sort/pagination (no server round-trip).
  **No Socket.IO in this template.**

## 2. Platform Analytics — Ecosystem Intelligence Suite

- **Route:** `GET /admin/analytics` — `app.py:2712`, `admin_analytics()`
  (2712–2755). `@login_required`; non-admins redirected home. Uses a
  `safe_query_count()` helper (returns 0 on error). On exception:
  `flash('Error: …', 'danger')` → redirect to `dashboard_admin`.
- **Template:** `templates/admin/admin_analytics.html` — **1,060 lines**.
  Title: `Platform Analytics • Ecosystem Intelligence Suite`.
- **Hero:** badge `INTELLIGENCE RADAR • REAL-TIME PLATFORM TELEMETRY`; H1
  `Institutional` + holographic `Analytics & Telemetry`; subtitle about
  high-altitude executive telemetry over enrolment, mentoring pipelines,
  career opportunities and engagement. Buttons: **Export Report**
  (`window.print()`), **Command Center** → dashboard, **Deep Velocity** →
  admin stats. Period pills (All-Time / Current Term / Last 30 Days,
  `switchPeriod()`) — **cosmetic only**: they toggle the active pill and
  pulse the KPI cards; they do not refilter any data.
- **Layout in order:**
  1. Hero (`.admin-hero-card`, glass dark, top rainbow strip
     `linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #34d399)`).
  2. Six KPI cards (`.kpi-grid`, 6 → 3 → 2 → 1 responsive; `.kpi-card`
     glassmorphic, top `.kpi-accent-bar`): Total Accounts (`kpiTotalUsers`,
     meta `{{ verified_users }} Verified`), Alumni Network, Active Students,
     Faculty Guides, Career Openings (meta `{{ job_applications }} Applied`),
     Active Links (meta `{{ online_users }} Online`). Each has an arrow link
     to the relevant admin page.
  3. Dual charts row: left `Demographic Composition` (doughnut, col-lg-5)
     with 4-way legend strip and `{{ total_users }} TOTAL` badge; right
     `Ecosystem Vitality Radar` (col-lg-7) with Bar/Polar toggle
     (`btnChartBar` / `btnChartPolar`, `setChartType('bar'|'polarArea')`),
     footer *"Calibrated live from production database"* / *"Edge
     Connected"*.
  4. Bottom row: left `Community Density Breakdown` (col-lg-7) — 4
     `.density-item` rows (Students/Alumni/Faculty/Administrative Core),
     each with icon, count / total (pct%), animated gradient progress bar
     (percentages computed in-template); right `Segment Inspection Hub`
     (col-lg-5) — 5 `.segment-link-card` links: Inspect Student/Alumni/
     Faculty Directory, Connection Monitor Radar (`{{ accepted_connections }}
     active peer links`), Broadcast & Community Desk. Footer: *"Enterprise
     Grade Telemetry • Encrypted Realtime Shard"*.
  5. Script — `initDemographicsDonut()`, `initEcosystemVitalityChart(type)`,
     `switchPeriod()`, `animateKPIValues()` (800 ms count-up, 25 ms steps).
- **Design:** **Full dark theme** — page `#0b0f17` with radial glows,
  glassmorphism throughout (`.admin-glass-card`: `rgba(17,24,39,0.72)`,
  `backdrop-filter: blur(16px)`, `1px rgba(255,255,255,0.08)` border,
  1.25 rem radius); three fixed blurred ambient orbs (`blur(90px)`,
  opacity 0.35, sky/violet/emerald). Accents: blue `#0284c7`, amber
  `#f59e0b`, green `#10b981`, purple `#8b5cf6`, cyan `#06b6d4`, rose
  `#f43f5e`. White text `#f1f5f9`, muted `#94a3b8`. Live badge sky
  `#38bdf8` with pulsing dot. `@media print` block (white background, hides
  orbs/period bar/print-excluded buttons via `.btn-no-print`).
- **Backend data passed:** a single dict `stats` (12 keys, all
  `safe_query_count` SQL counts): `total_users`, `students`, `alumni`,
  `faculty`, `admin`, `verified_users` (`is_verified=1`),
  `meet_registrations` (`alumni_meet_registration`), `active_jobs`
  (`jobs`), `job_applications`, `accepted_connections` /
  `pending_connections` (`connection_requests` by status — note:
  `pending_connections` is computed but **never used** in the template),
  `online_users` (`user_activity WHERE online_status='online'`).
  Template accesses via `stats.get('…', 0)`.
- **Actions:** No forms. Export Report (print), Command Center, Deep
  Velocity, period pills (cosmetic), Bar/Polar chart toggle, KPI arrow
  links, 5 segment-inspection links.
- **Charts (Chart.js 4.4.1):** `#demographicsDonutChart` — doughnut,
  Students/Alumni/Faculty/Admin, data from JS `analyticsData` (values from
  `stats`), colours `['#38bdf8', '#fbbf24', '#34d399', '#c084fc']`,
  `borderColor: '#0f172a'`, `cutout: '72%'`, legend hidden, tooltip shows
  `value (pct%)`. `#ecosystemVitalityChart` — **bar** (default) or
  **polarArea** (toggle destroys/recreates via `vitalityChartInstance.destroy()`),
  7 labels: Students, Alumni, Faculty, Jobs, Job Apps, Connections, Meet
  Regs; per-bar colours sky/amber/emerald/cyan/indigo/rose/purple,
  `borderRadius: 8`; dark grid/ticks (`#94a3b8`).
- **Live features:** KPI count-up on load; Bar/Polar switcher; period pills
  (visual pulse only). **No Socket.IO**; "live" is branding — data is
  server-rendered on page load, no polling or WebSocket.

## 3. Platform Stats — Telemetry (static demo page)

- **Route:** `GET /admin/stats` — `app.py:5213`, `admin_stats()`
  (5213–5221). `@login_required`; non-admins get `flash('Access denied!',
  'danger')` → redirect home.
- **Template:** `templates/admin/admin_stats.html` — **206 lines**. Title:
  `Platform Telemetry • Statistical Performance Matrices`.
- **Hero:** badge `TELEMETRY MATRIX • HISTORICAL PERFORMANCE CHARTS`; H1
  `Platform Performance` + holographic `Statistics`; subtitle about monthly
  registration velocities, retention cohorts and demographic ratios.
  Buttons: Command Center → dashboard, Analytics Radar → analytics.
- **Layout:** hero (`.admin-hero-card`, 3 ambient orbs) → four Mini Metric
  Nodes (`.admin-stat-node`, accent bars blue/amber/green/purple): Total
  Ecosystem Base **1,250**, Verified Alumni **850**, Active Learners
  **350**, Faculty Leaders **50** → dual charts row: left (col-lg-8)
  `Monthly Member Onboarding Velocity` (`<canvas id="userGrowthChart">`,
  280 px), right (col-lg-4) `Role Share` (`<canvas id="roleDistChart">`,
  280 px).
- **Backend data passed: None.** `render_template('admin/admin_stats.html')`
  with no variables. **All numbers are hardcoded literals** — the 1,250 /
  850 / 350 / 50 stat nodes and both charts' datasets are static, not live
  database values. This is the key viva point: the page is a static
  demo/telemetry mock-up.
- **Actions:** only the two hero navigation links. No forms, filters or actions.
- **Charts (Chart.js 4.4.1):** `#userGrowthChart` — line, labels
  `['JAN','FEB','MAR','APR','MAY','JUN']`, data `[65, 59, 80, 81, 56, 155]`
  (hardcoded), `borderColor: '#0284c7'`, fill `rgba(2,132,199,0.08)`,
  `tension: 0.38`, `borderWidth: 3`, legend hidden, y-axis `beginAtZero`.
  `#roleDistChart` — doughnut, labels `['ALUMNI','STUDENTS','FACULTY']`,
  data `[850, 350, 50]` (hardcoded, matches the stat nodes), colours
  `['#f59e0b', '#0284c7', '#10b981']`, `borderWidth: 3`, white borders,
  `cutout: '70%'`, `hoverOffset: 10`, legend bottom.
- **Live features:** none — no Socket.IO, clock, counters or polling.

## 4. User Directory — Directory Control

- **Routes:** `GET /admin/users/<role>` — `app.py:1493`,
  `admin_view_users`; `GET /admin/approve-requests` — `app.py:1522`,
  `admin_approve_requests` (same template, forced `role='pending'`).
  Both `@login_required`; non-admin → redirect home.
- **Template:** `templates/admin/admin_view_users.html` — **1,841 lines**.
  Title: `Directory Control • Enterprise User Management • Alumni Hub`.
- **Backend data passed:** `users` (`SELECT * FROM users …`; `role='all'`
  → all by `id DESC`; `role='pending'` → `is_approved = 0` by `created_at
  DESC`; else `WHERE role = ?`), `role`, `stats` dict =
  `{total, student, alumni, faculty, pending}` (5 separate `COUNT(*)`
  queries). Row fields used: `id, name, email, phone, role, is_approved,
  profile_pic, branch, company, city, created_at`.
- **Hero:** badge `DIRECTORY MATRIX • ENTERPRISE USER MANAGEMENT`; H1
  `Institutional User Directory`; subtitle about full-spectrum governance
  over students, alumni, faculty and admins — real-time filtering, 1-click
  approvals, profile dossiers, credential control. Buttons: Command Center
  → dashboard; Community Group (WhatsApp green gradient `#25d366→#128c7e`);
  Approvals Queue → approve-requests, with red badge showing
  `stats.pending` when > 0.
- **Layout in order:**
  1. Hero, with role filter pills: All Accounts / Students / Alumni /
     Faculty / Pending Review (Pending pill shows `stats.pending` badge).
  2. Telemetry KPI deck (`.adm-kpi-grid`, **5 clickable cards**,
     `data-role`, `onclick="filterByRolePill('…')"`; active card
     `active-kpi`): Total Registered (`#statValTotal`), Students, Alumni
     Network, Faculty Staff, Pending Approval (amber, `fa-clock fa-spin`
     when pending > 0).
  3. Command Control Dock (`.admin-card`): search `#userSearch`
     (*"Search by name, email, phone, role, company…"*, clear button),
     view switcher `#btnViewCards` / `#btnViewTable`, Refresh
     (`location.reload()`), **Export CSV** (`exportUsersToCSV()`); mobile
     quick-chip track; selects `#filterRoleSelect`, `#filterStatusSelect`
     (All/Active Verified/Pending Approval), `#sortSelect` (Newest/Oldest/
     Name A–Z/Z–A); counter `#totalUsersCount` ("N Total Records").
  4. Main Records Container — heading "Enrolled Participants Directory" +
     **Multi-Select** button `#btnToggleSelectMode`. Two views of the same
     `{% for user in users %}` loop:
     - **Cards view** `#usersCardsWrap` (`.user-cards-grid`,
       `repeat(auto-fill, minmax(320px, 1fr))`): `.adm-user-card`
       (`.pending-card` = amber gradient `#fffbeb→#ffffff` when
       `is_approved == 0`); 48 px avatar (photo or `.adm-user-initials
       initials-{role}` — student sky `#0284c7→#0369a1`, alumni amber
       `#f59e0b→#d97706`, faculty emerald `#10b981→#059669`, admin violet
       `#8b5cf6→#6d28d9`); role badge + status badge (`.badge-status-pending`
       amber / `.badge-status-verified` emerald); name, email (JetBrains
       Mono + copy button), `tel:` quick-call; meta box (Account ID,
       Dept/Branch, Company, Enrolled date); action deck: approve banner
       `.btn-adm-approve-banner` (emerald, "Approve & Authorize", pending
       only), Direct Chat → `/messages?user_id={{id}}`, Full Profile →
       student/alumni/faculty profile (admin → profile), Quick Inspect →
       `openUserInspectModal(id)`, Purge (red trash) — **hidden for
       protected accounts** (replaced by `.adm-protected-pill`
       "Protected").
     - **Dense table view** `#usersTableWrap` (`#usersTable`, hidden on
       mobile): columns User Profile | Role Classification | Academic /
       Work | Onboarding Date | Verification Status | Administrative
       Controls. Row classes `.user-row`, `table-warning` when pending;
       same actions as pill buttons.
     - Both rows carry data attributes `data-id/data-name/data-email/
       data-phone/data-role/data-approved/data-created/data-branch/
       data-company/data-city` (JS `extractUsersData()`).
     - Empty states: `#noUserResults` ("No Matching Users Found" + Reset
       Filters) and `{% else %}` "No Records Found …".
  5. Floating Bulk Action Dock `#admBulkBar` (fixed bottom, dark
     `rgba(15,23,42,0.95)` + blur, slides in with `.show`):
     `#selectAllCheckbox`, `#selectedCountText` ("0 Selected"),
     **Approve** (`batchApproveSelected()`), **Export**
     (`batchExportSelected()`), close. Checkboxes `.adm-card-checkbox`
     (22 px, `accent-color: #4f46e5`) appear only in
     `.selection-mode-active`.
  6. Quick Dossier Inspection Modal `#userInspectModal` (Bootstrap modal,
     dark gradient header `#0f172a→#1e293b`, mobile bottom-sheet, drag
     handle): avatar 76 px, name, role/status badges, info grid (ID, email,
     phone, branch, company, city, joined); dynamic buttons (Full Web
     Profile, Direct Chat, Copy Email). Toast container
     `#admToastContainer` (auto-dismiss 3,200 ms).
- **Actions / endpoints (client-side JS, no `<form>` POSTs):** 1-click
  approve `GET /admin/verify-user/<id>/approve` with header
  `X-Requested-With: XMLHttpRequest` (on success swaps badge to VERIFIED,
  removes banner, decrements `#statValPending`); batch approve loops the
  same endpoint per id; purge `POST /api/delete-user/<id>` (confirm dialog,
  fades/removes card+row); CSV export is fully client-side
  (`exportUsersToCSV()` / `batchExportSelected()`, headers: Account ID,
  Full Name, Email, Phone, Role, Department/Branch, Company, City,
  Verification Status, Joined Date).
- **Live features:** none — no Socket.IO, polling or Chart.js. All
  filtering/search/sort is client-side (`applyFilters()` matches query
  against id+name+email+phone+role+branch+company+city). Mobile
  auto-switches to cards view (< 768 px).
- **Related route — verify-user:** `GET /admin/verify-user/<int:user_id>/<action>`
  (`app.py:2670`, `verify_user`). **GET only, no `methods=`.**
  `action == 'approve'` → `UPDATE users SET is_approved = 1`;
  `action == 'block'` → `DELETE FROM users WHERE id = ?` (despite the
  name, "block" hard-deletes); anything else → no-op. AJAX →
  `{'success': True, 'message': …, 'action': …, 'user_id': …}`; otherwise
  flash + redirect to `request.referrer` or `admin_view_users(role='all')`.
  Non-admin → JSON 403 if XHR/JSON, else flash + redirect home. **State-
  changing GET, no CSRF token.**
- **Related route — delete-user:** `POST /api/delete-user/<int:user_id>`
  (`app.py:3090`, `delete_user`) — admin-only, 404 if missing, **403 for
  protected super-admin accounts**; cascades deletes across profile tables,
  then returns JSON.

## 5. Connection Monitor — Link Intelligence

- **Route:** `GET /admin/connection-monitor` — `app.py:1881`,
  `admin_connection_monitor`. Admin-only (flash + redirect
  `dashboard_admin`). Query params: `?role=all|student|alumni` (validated,
  default `all`), `?search=` (passed through; template search is
  client-side).
- **Template:** `templates/admin/connection_monitor.html` — **1,813 lines**.
  Title: `Connection Monitoring & Link Intelligence • Admin Hub`.
- **Backend data passed:** `records` (from
  `services/admin_service.py:124 get_connection_activity(conn, role_filter,
  search)`), `role_filter`, `search`, `total_records=len(records)`. Each
  record (from `get_all_connections`, joining `connection_requests` →
  sender/receiver `users` + student/alumni/faculty profiles): `id,
  sender_id, receiver_id, status, request_sent_at, request_accepted_at`,
  per-side `name/email/role/department/skills/current_domain/passing_year/
  company`, plus `sender_stats/receiver_stats` (`get_user_statistics`),
  `sender_activity/receiver_activity` (`{last_login, online_status}` from
  `user_activity`, default `'offline'`), `messages_exchanged` (COUNT from
  `private_messages` both directions). KPI pending/accepted/rejected/
  online/message totals are **computed in-template** with a Jinja
  `namespace` looped over `records` (online counts *both* endpoints, so
  one link can add 2); acceptance rate = `accepted/(accepted+rejected)*100`
  rounded to 1 dp (100.0% if none decided).
- **Hero:** own wrapper `.cm-page-wrapper` (bg `#f8fafc`, `padding-top:
  145px` desktop / 115px mobile, max-width 1360px `.cm-container`);
  ambient orbs `.cm-ambient-orb.cm-orb-1` (sky `#0284c7`, 520 px) /
  `.cm-orb-2` (violet `#7c3aed`, 460 px), blurred, opacity 0.12. Header
  card `.cm-header-card` (white, 24 px radius, 4 px top gradient
  `#0284c7→#4f46e5→#7c3aed`): live pill `.cm-live-pill` "CONNECTION
  INTELLIGENCE CORE • LIVE TELEMETRY" with pulsing radar dot
  (`.cm-radar-dot`, 1.8 s keyframes); H1 `Connection Monitoring Dashboard`
  (gradient span `#0284c7→#4f46e5`); subtitle about real-time oversight of
  student-alumni networking requests, message exchanges, credentials and
  live engagement. Buttons: **Sync Radar** `#btnSyncFeed`
  (`syncLiveFeed()`), **Export CSV** (`exportConnectionsToCSV()`),
  **Admin Hub** (gradient `#0284c7→#4f46e5`) → dashboard.
- **Layout in order:**
  1. Header card (above).
  2. KPI deck `.cm-kpi-grid` — **6 cards** (6 → 3 @ ≤1200 px → 2 @ ≤640 px),
     clickable, `.active` = sky border + `#f0f9ff` bg: Total Connections
     `#kpiCountAll`, Pending, Accepted Links, Declined, Messages Exchanged
     (filter `active-chat`), Acceptance Rate `#kpiCountRate` (pill "HEALTH",
     `fa-chart-line`). Each has tinted icon wrap, pill
     (ALL/PENDING/CONNECTED/DECLINED/VOLUME/HEALTH), number in JetBrains
     Mono, animated count-up (`animateKpiCounters()`, 20 steps × 25 ms,
     staggered 40 ms).
  3. Live Radar Presence Strip `.cm-radar-strip` (white, green left border
     5 px `#10b981`): "LIVE TELEMETRY" + "Active Network Radar: **N**
     participants currently online" (`#liveOnlineCount`); right side
     `#feedSyncTimestamp` ("Sync Status: Operational • Real-time
     Connected").
  4. Search & Filter Bar Dock `.cm-filter-card`: search `#cmSearchInput`
     (*"Search by name, email, department, role…"*, clear
     `#cmSearchClear`), role select inside GET form `#roleForm`
     (All / Student Initiated / Alumni Initiated, `onchange` submits);
     sort `#cmSortSelect` (recent/oldest/messages/sender); chips
     `#cmStatusChips`: All Records, Pending, Accepted, Declined, Active
     Online (green dot), Active Chats (>0 Msgs); counter
     `#filterResultsCount` ("Showing **N** of **M** links") + Reset Filters.
  5. Desktop table `.cm-table-card` (hidden < 992 px) — columns: Link
     Status & Timeline | Initiator (Sender) | Recipient (Receiver) |
     Social Footprint | Live Presence | Chat Volume | Deep Inspect. Rows
     `.cm-record-row` in `#cmDesktopTableBody`, data attrs
     `data-status/data-sender-online/data-receiver-online/data-search-text/
     data-messages/data-sent-at/data-sender-name`. Status pills
     `.cm-status-pill.pill-connected` (emerald) / `.pill-pending` (amber)
     / `.pill-declined` (red); "Sent: …" + "Linked: …"; user brief
     `.cm-user-brief` with 40 px gradient avatar (sender
     `#0284c7→#0369a1`, receiver `#0ea5e9→#0284c7`), name/email, role badge
     + department; Social Footprint = "FirstName: **N** links • **N**
     followers"; Live Presence = `.cm-online-dot.online` (green `#10b981`
     + halo) / `.offline` (grey `#94a3b8`); Chat Volume `.cm-msg-counter`
     (`.has-msgs` = blue when > 0); Deep Inspect buttons "Sender" /
     "Receiver" → `openProfileModal(sender_id|receiver_id)`.
  6. Mobile Cards Feed `.cm-mobile-feed` (`display:none` ≥ 992 px):
     `.cm-mobile-card.status-{accepted|pending|rejected}` (4 px left status
     bar green/amber/red), pathway box `.cm-mobile-pathway` (sender node →
     message counter + arrow → receiver node), presence strip, actions
     "Inspect Initiator" / "Inspect Recipient".
  7. Pagination Bar `.cm-pagination-bar` — `#cmPageInfo` ("Showing **1**
     to **10** of **N** links"), page-size select `#cmPageSizeSelect`
     (10/25/50/100, default 10), controls `#cmPaginationControls` (Prev/
     Next + numbered buttons, smart ellipsis when > 7 pages, `goToPage()`
     smooth-scrolls). No-matches card `#cmNoMatchesPrompt` (dashed border,
     "No Matching Connections Found").
  8. Profile Intelligence Modal `#profileModal` (`.cm-profile-modal`,
     `modal-lg`, white, 26 px radius): header with radar dot +
     `#modalUserName`; body `#profileModalBody` (spinner "Fetching profile
     credentials…"); footer "Live verified telemetry from institutional
     database registry". Content built by JS from the user-detail API:
     avatar, name/email, role badge, online badge, last login, Department,
     Batch/Graduation, Current Company/Institution, Technical Skills &
     Domain (`.cm-pill-tag` badges), 3 stat boxes — Connections / Followers
     / Messages.
- **Actions:** Sync Radar (fake 600 ms refresh — spins `#syncIcon`, updates
  `#feedSyncTimestamp`, re-runs client filter; no server reload), Export CSV
  (`exportConnectionsToCSV()` — client-side Blob, columns Link ID,
  Initiator, Initiator Role, Recipient, Recipient Role, Status, Sent At,
  Messages; filename `connection_telemetry_<date>.csv`; only visible rows),
  role GET form, profile inspect modal, pagination/sort/filter (all
  client-side over server-rendered rows).
- **Live features — Socket.IO (the only admin page with it):** CDN
  `https://cdn.socket.io/4.5.4/socket.io.min.js` in `<head>`; IIFE
  `initMonitorSocket()` connects `io({transports:['websocket','polling']})`
  and listens for **`admin_connection_activity`**; on `data.event ===
  'new_request'` increments `#kpiCountPending` + toast "🔔 New Connection
  Request: {sender} → {receiver}"; `'accepted'` increments
  `#kpiCountAccepted` + "✅ Connection Accepted: {sender} ↔ {receiver}";
  `'rejected'` increments `#kpiCountRejected` + "❌ Request Declined: …";
  every event also increments `#kpiCountAll`. Toasts via
  `showFeedbackToast(msg, color)` (fixed bottom-right `#cmToast`, dark
  `#0f172a`, coloured left border, 3,200 ms). **No Chart.js, no polling
  interval.** Server side: `app.py:4012/4071/4123` emits
  `admin_connection_activity` from the connection-request accept/reject
  handlers, plus `connection_request_received` /
  `connection_status_update` to users.
- **Related route — user detail API:** `GET
  /admin/connection-monitor/user/<int:user_id>` (`app.py:1915`,
  `admin_connection_monitor_user`). Admin-only (403 `{'error':
  'Unauthorized'}`). SQL joins `users` + student/alumni/faculty profiles
  (COALESCE department, skills, passing year/semester, company) +
  `user_activity` (`last_login`, `online_status` default `'offline'`);
  404 if missing; merges `get_user_statistics()` and `messages_exchanged`
  (COUNT `private_messages` where user is sender or receiver); returns
  `{'user': payload}`.
- **Flagged quirks:** (1) template reads
  `row.sender_activity.connections_count` / `followers_count`, but
  `get_connection_activity()` sets `sender_activity = {last_login,
  online_status}` only; the counts live in
  `sender_stats.total_connections/total_followers` — so "Social Footprint"
  likely renders 0/blank. (2) Modal JS reads `user.graduation_year` and
  `user.company`, but the API returns `passing_year` and `current_company`
  — those two modal fields likely show "Not specified".

## 6. Messaging Control — Messaging Governance

- **Route:** `GET /admin/messaging-control` — `app.py:1870`,
  `admin_messaging_control`. Admin-only (flash "Unauthorized access" +
  redirect `dashboard_admin`). **Passes no data at all** —
  `render_template('admin/admin_messaging_control.html')` with zero context
  variables; everything is loaded client-side via API.
- **Template:** `templates/admin/admin_messaging_control.html` — **673 lines**.
  Title: `Messaging Governance & Community Group Desk • Executive Control Console`.
- **Hero:** badge `MESSAGING GATEWAY • TELEMETRY & COMMUNITY GOVERNANCE`
  (`admin-live-badge` + `live-pulse-dot`); H1 `Institutional Messaging
  Governance`; subtitle about real-time supervision over community group
  channels, emergency global freeze protocols (kills group & 1-on-1 chats),
  member admissions approval, and public stream redaction. Buttons:
  Command Center → dashboard; Live Community Group (green, WhatsApp icon)
  → `community_group` (new tab); Broadcast Desk → whatsapp-broadcast.
- **Telemetry counters (hero, `.mc-counter` JetBrains Mono, initial `--`/`0`,
  filled by JS):** `#publicMsgCount` "Public / Group — Broadcasted entries"
  (sky `#38bdf8`), `#privateMsgCount` "Direct 1-on-1 — Peer-to-peer
  discussions" (amber `#fbbf24`), `#communityMembersCount` "Community
  Members — Approved group participants" (emerald `#34d399`),
  `#pendingJoinCount` "Pending Join Requests — Awaiting admin verification"
  (rose `#f43f5e`).
- **Layout in order:**
  1. Hero terminal (above).
  2. Dual Moderation Ribbon (`.row g-4`):
     - **Left — Emergency Messaging Lock** (`.admin-card.mc-lock-card#lockCardElement`):
       shield icon, H4 "Emergency Messaging Lock", sub "Universal freeze
       protocol (Group & 1-on-1)"; badge `#lockBadge` (initial "SYNCING…",
       becomes red `CHAT FROZEN (LOCKED)` / green `OPERATIONAL`); explainer
       "When locked, **no student, alumni, or faculty** can send community
       group messages or private 1-on-1 direct messages. Only administrators
       retain communication rights."; info box `#lockedByValue` ("Locked
       By:", default `-`) / `#lockedAtValue` ("Lockdown Timestamp:",
       default "Normal Operations"); input `#lockReason` (placeholder
       "e.g. Scheduled platform maintenance or code of conduct
       review…"); buttons `#lockBtn` "Freeze All Messaging"
       (`lockMessaging()`, red, `fa-lock`) and `#unlockBtn` "Restore
       Operations" (`unlockMessaging()`, green, `fa-lock-open`). Card state
       classes: `.mc-lock-card.is-locked` (2 px red border `#ef4444`,
       gradient to `#fff5f5`) / `.is-active` (2 px emerald border, gradient
       to `#f0fdf4`).
     - **Right — Community Admissions** (`.admin-card`): WhatsApp icon, H4
       "Community Admissions", sub "Verify & approve requests to join
       group"; **Refresh** button (`loadCommunityRequests()`), **Chat**
       link → `community_group` (new tab); filter pills `#tabRequestsBtn`
       "Pending Requests (<span id='tabPendingBadge'>0</span>)" /
       `#tabMembersBtn` "Active Members (<span id='tabMembersBadge'>0</span>)"
       toggling `showCommunityTab('requests'|'members')`; list containers
       `#communityRequestsList` / `#communityMembersList` (both
       `max-height: 280px`, scrollable; members list starts `d-none`);
       request/member cards `.mc-approval-card` (avatar initials
       `avatar-initials-{role}`, name, email, role badge, request date)
       with **Approve** (green) / **Reject** (outline red) buttons, or
       **Remove** (outline red, `fa-user-minus`) for members.
  3. Lower row (`.row g-4`):
     - **Left (8 cols) — Live Discussion Stream & Redaction Desk**: H3
       "Live Discussion Stream & Redaction Desk", sub "Audit recent messages
       in community channels. Delete non-compliant or flagged posts.";
       buttons `#toggleHiddenBtn` "Flagged" (`toggleViewHidden()`,
       `fa-eye-slash` ↔ "Show Active Only") and **Refresh Stream**
       (`loadPublicMessages()`); feed `#messagesList` (`.mc-feed-box`,
       `max-height: 480px`, scrollable); message cards `.mc-feed-item`
       (sender name, timestamp, `[FLAGGED HIDDEN]` red badge when
       `msg.is_hidden`, content `white-space: pre-wrap`, red circular
       delete button → `deleteMessage(id)`).
     - **Right (4 cols) — Sanctioned Users** (`.admin-card`):
       `fa-user-slash` icon, H4 "Sanctioned Users", sub "Privileges
       suspended"; refresh button (`loadSuspendedUsers()`); list
       `#suspendedUsersList` (`max-height: 400px`); cards
       `.mc-approval-card` (2-letter initials, name, role badge) with
       **Restore** button (outline green, `fa-undo`) → `unsuspendUser(id)`.
- **Actions / API calls (all `fetch`, blueprint `messaging` registered in
  `app.py:5317` with `url_prefix='/api'`; handlers in
  `routes/messaging_routes.py`):**
  - `GET /api/admin/messaging/status` → `refreshLockStatus()` — response
    `{is_locked, locked_by, locked_at}`; drives badge, button disabled
    states (`lockBtn` disabled when locked, `unlockBtn` when unlocked),
    card class.
  - `POST /api/admin/messaging/lock` `{reason}` → `lockMessaging()`
    (confirm dialog "CONFIRM GLOBAL MESSAGING FREEZE…", alert "All messaging
    channels have been FROZEN successfully.").
  - `POST /api/admin/messaging/unlock` → `unlockMessaging()` (confirm,
    alert "Messaging system has been restored to OPERATIONAL status.").
  - `GET /api/admin/messaging/statistics` → `refreshStatistics()` — fills
    the 4 hero counters + 2 tab badges from
    `statistics.{total_public_messages, total_private_messages,
    community_members_count, community_pending_count}` (computed in
    `database/messaging_db.py:672 get_messaging_statistics()` from
    `public_messages WHERE deleted_by IS NULL`, `private_messages`,
    `conversations`, `community_group_members` approved/pending).
  - `GET /api/admin/community-group/requests` → `loadCommunityRequests()`;
    `POST /api/admin/community-group/approve` `{user_id}` →
    `approveMember()`; `POST /api/admin/community-group/reject` `{user_id}`
    → `rejectMember()` (confirm); `GET /api/admin/community-group/members`
    → `loadCommunityMembers()`; `POST
    /api/admin/community-group/remove-member` `{user_id}` →
    `removeMember()` (confirm).
  - `GET /api/admin/messaging/public-messages?include_hidden={true|false}&limit=100`
    → `loadPublicMessages()`; `DELETE /api/messages/public/{id}` →
    `deleteMessage()` (confirm "REDACT MESSAGE…", route
    `messaging_routes.py:128 delete_public_msg`, admin-only, soft-delete
    via `delete_public_message()`).
  - `GET /api/admin/messaging/suspended-users` → `loadSuspendedUsers()`;
    `POST /api/admin/messaging/unsuspend` `{user_id}` →
    `unsuspendUser()`. (Suspend endpoint exists server-side — `POST
    /api/admin/messaging/suspend` — but is **not** called from this page.)
  - Local helper `escapeHtml()` used for all injected names/content.
- **Live features:** **polling, not Socket.IO, no Chart.js.** On
  `DOMContentLoaded`: `refreshLockStatus()`, `refreshStatistics()`,
  `loadCommunityRequests()`, `loadPublicMessages()`,
  `loadSuspendedUsers()`; then `setInterval(..., 15000)` re-runs
  `refreshStatistics()` + `refreshLockStatus()` every 15 s. No live
  message-stream socket; refresh is manual (`loadPublicMessages()`) or via
  the 15 s stats poll. JS state vars: `viewingHidden = false`, `isLocked =
  false`, `currentCommunityTab = 'requests'`.

## 7. Jobs — Opportunity Matrix

- **Route:** `GET /admin/jobs` — `admin_jobs()` in `app.py:3196–3248`
  (`@login_required`, non-admin → `403 JSON {error: Unauthorized}`).
  Template: `templates/admin/jobs.html`, **1,591 lines**.
- **Title:** `Opportunity Matrix • Institutional Career & Placement Desk • Alumni Hub`
- **Hero:** badge `OPPORTUNITY MATRIX • RECRUITMENT & CAREER ENGINE`; H1
  `Institutional <holographic>Opportunity Desk</h1>`; subtitle about
  comprehensive governance over campus recruitment drives, corporate
  vacancies, alumni referral pipelines and student placement analytics.
  Top-right: `Command Center` → dashboard; `Post New Vacancy` (gradient
  `#4f46e5→#6366f1`) → `admin_add_job`.
- **Layout in order:**
  1. Hero (above).
  2. **KPI telemetry grid** (`.job-kpi-grid`, 4 clickable cards,
     `onclick="filterByChip(...)"`): Total Listings `#statValTotal`
     (`stats.total` else `jobs|length`); Active & Live `#statValActive`
     (`stats.active`, green); Pending Approval `#statValPending`
     (`stats.pending` else `pending_jobs|length`, amber, spinning
     hourglass if >0); Paused/Closed `#statValInactive` (`stats.inactive`,
     grey). IDs `kpiCardAll/Active/Pending/Inactive`.
  3. **Corporate Approvals Queue** (`#pendingSection`, only `{% if
     pending_jobs %}`, amber gradient `#fffdf8→#fff`) — badge
     `#pendingCountBadge`: `{{ pending_jobs|length }} Awaiting
     Authorization`. Two renderings of the same loop: mobile cards
     `#pendingJobsCardsWrap` (`.d-md-none`) and desktop table
     `#pendingJobsTableWrap`/`#pendingJobTable` (`.d-none.d-md-block`).
     Columns: Job Information & Company | Posted By | Target Role |
     Application Deadline | Verification Action. Shows `job.posted_by_name`,
     `(job.poster_role|upper)` badge (`badge-alumni`/`badge-faculty`),
     `job.deadline or 'Open Ended'`.
  4. **Command Control & Filters Dock** (`.admin-card`): search `#jobSearch`
     (*"Search by title, company, skills, or location…"*, clear button);
     view switcher `#btnViewCards` / `#btnViewTable`
     (`switchJobView('cards'|'table')`); Refresh (`location.reload()`);
     Export CSV (`exportJobsToCSV()`). Quick-filter chips `.job-chip-btn`
     (`data-filter`): All Opportunities, Active Only, Remote Only,
     Technology, Business & Mgmt, Design, Paused. Dropdowns
     `#filterCategorySelect` (All/Technology/Business/Design/Marketing/
     Finance), `#filterModeSelect` (All/Remote/Hybrid/Onsite),
     `#filterStatusSelect` (All/Active/Paused), `#sortJobSelect`
     (newest/oldest/title A–Z/company A–Z). Badge `#totalJobsCountBadge`:
     `{{ jobs|length }} Total Records`.
  5. **Active Employment Directory** (`.admin-card`): dual view — cards
     `#jobsCardsWrap` (`.job-cards-grid`, `minmax(340px,1fr)`) and dense
     table `#jobsTableWrap` (`#jobsTable`, `d-none` by default; mobile
     <768 px forces cards). Card (`.adm-job-card`, `.inactive-card` if
     paused, `.pending-job-card` amber) has: 48 px logo box `.job-logo-box`
     (indigo gradient, company initial or `job.company_logo` img with
     onerror fallback), category badge, status pill
     `#statusBadgeCard{{id}}` (`job-status-active` green /
     `job-status-paused` grey), title, company, meta box (Package/CTC
     `job.salary or job.ctc_range or 'Competitive'`, Location, Type &
     Mode pills `.pill-mode-remote` green / `-hybrid` indigo / `-onsite`
     grey, Deadline), **Portal Visibility toggle** (Bootstrap switch
     `.status-toggle-input`, `data-job-id`), action deck: Quick Inspect
     (`.job-btn-inspect`, sky), Edit Posting (`.job-btn-edit`, indigo →
     `admin_edit_job`), Apply Portal link if `job.apply_link` else Share
     Listing (`copyJobShare()`), Delete (`.job-btn-delete`, red trash;
     POST form to `admin_delete_job` with confirm). Table columns: Job
     Title & Organization | Category | Employment & Mode | Package &
     Location | Openings (+`eligible_branch`) | Visibility (switch) |
     Administrative Controls (Inspect/Edit/Delete icon buttons, 36 px
     circles). Every card/row is `.job-item-node` with `data-*` attributes
     (id/title/company/category/mode/employment/status/salary/location/
     openings/apply/deadline/skills/description/created) — JS extracts them
     into `currentJobsData` for client-side search/filter/sort.
  6. Empty states: `#noJobResults` (*"No Matching Opportunities Found"*,
     Reset button) and, if no jobs at all, *"No Job Postings Yet"* + `Post
     Your First Vacancy`.
  7. **Job Inspect modal** `#jobInspectModal` (`.modal-lg`, dark gradient
     header `#0f172a→#1e293b`, bottom-sheet on phones with drag handle;
     fields `#modalJobLogoWrap/Title/Company/Category/Mode/Status/Salary/
     Location/Employment/Openings/Deadline/Id`, `#modalJobSkills`,
     `#modalJobDescription`, dynamic `#modalJobActions` with Edit + Apply
     Link). Toast container `#admToastContainer` (dark `#0f172a`, 3.2 s).
- **Design:** white cards `#fff`, border `#e2e8f0`, radius 18–24 px, indigo
  `#4f46e5` primary, success `#059669/#10b981`, warning amber, slate text
  `#0f172a/#64748b`; Outfit headings, JetBrains Mono for salary/deadline.
- **Backend data passed:** `render_template('admin/jobs.html', jobs=jobs,
  pending_jobs=pending_jobs, stats=stats)`.
  - `pending_jobs`: `jobs JOIN users ON j.posted_by=u.id WHERE
    approval_status='pending' ORDER BY created_at DESC`, plus
    `posted_by_name`, `poster_role`.
  - `jobs`: same join, `WHERE approval_status != 'pending' OR
    approval_status IS NULL`, `ORDER BY created_at DESC`.
  - `stats`: `{total: COUNT(*) jobs, active: COUNT(is_active=1 AND
    approval_status='approved'), expired: COUNT(deadline < today AND
    approval_status='approved'), pending: COUNT(approval_status='pending'),
    inactive: total − active}`. Note: `stats.expired` is computed but
    **never displayed** in the template.
- **Actions / APIs:**
  - `POST /admin/jobs/approve/<int:job_id>` (`admin_approve_job`,
    `app.py:3250`): sets `approval_status='approved', is_active=1`; emits
    Socket.IO `job_approval_update` `{status:'approved', job_id,
    job_title}` to room `user_{posted_by}`; returns `{success, message}`.
    JS `approveJob(id)` fetches it (confirm first), fades out
    `#pendingRow/#pendingCard{id}`, reloads after 600 ms.
  - `POST /admin/jobs/reject/<int:job_id>` (`admin_reject_job`,
    `app.py:3279`): JSON body `{reason}` (from `prompt()` in
    `rejectJobPrompt(id)`); sets `approval_status='rejected', is_active=0,
    rejection_reason=?`; Socket.IO `job_approval_update`
    `{status:'rejected', …, reason}`; returns `{success}`.
  - `POST /api/admin/jobs/toggle/<int:job_id>` (`admin_toggle_job`,
    `app.py:3329`): flips `is_active`, returns `{success, new_status:
    0|1}`; JS `initStatusToggleSwitches()` syncs card/row/badge and shows
    toast; reverts checkbox on failure.
  - `GET /api/admin/jobs/pending-count` (`app.py:3311`): returns `{count}`
    of pending jobs.
  - `POST /admin/jobs/delete/<int:job_id>` (`admin_delete_job`,
    `app.py:3644`): `DELETE FROM jobs WHERE id=?`, flash `'Job deleted
    successfully!'`, redirect `admin_jobs`. (Form-based, not fetch.)
  - Client-side only: search/filter/sort, view switch,
    `exportJobsToCSV()` — downloads `alumni_hub_jobs_YYYY-MM-DD.csv`
    with columns Listing ID, Job Title, Company, Category, Employment
    Type, Work Mode, Compensation, Location, Openings, Status, Deadline,
    Apply Link.
- **Charts/live:** no charts. Live: visibility toggle API, approve/reject
  fetch + Socket.IO notification to poster, client-side filtering.

## 8. Add Job — Publish New Career Vacancy

- **Route:** `GET, POST /admin/jobs/add` — `admin_add_job()` in
  `app.py:3352–3439` (non-admin → 403 JSON). Template:
  `templates/admin/add_job.html`, **429 lines**.
- **Title:** `Post Opportunity • Career Matrix Admin`
- **Hero:** badge `OPPORTUNITY DEPLOYMENT • VACANCY CREATION MATRIX`; H1
  `Publish New <holographic>Career Vacancy</h1>`; subtitle about deploying
  opportunities across student/alumni dashboards. Back link `Return to Job
  Matrix` → `admin_jobs`. Container `max-width: 1080px`.
- **Layout:** hero + one `<form method="POST" enctype="multipart/form-data">`
  (no `action` = posts to self) with 5 white blocks (`.job-form-block`,
  radius 24 px, `.job-section-title` with 38 px icon):
  1. **Basic Role & Entity Information** (briefcase, blue): `title`*
     (text, *"e.g. Senior Full Stack Engineer"*), `company_name`* (text,
     *"e.g. Google India / Microsoft"*), `company_website` (url),
     `description`* (textarea rows=5), `company_logo` (file, hidden
     `#logoInput`, `accept="image/*"`, dashed dropzone `#uploadZone`,
     *"Supports PNG, JPG, WEBP up to 5MB"*, live preview `#previewBox` via
     FileReader).
  2. **Location & Work Arrangement** (map, info): `location_select`
     (Mumbai/Bangalore/Pune/Delhi NCR/Hyderabad/Remote/Other) + conditional
     `location_manual` text in `#manual_location` (shown only if `Other`);
     `work_mode` (Onsite/Remote/Hybrid); `employment_type` (Full-time/
     Internship/Part-time/Contract).
  3. **Eligibility & Candidate Calibration** (graduation-cap, green):
     `eligible_branch` (All Branches/MCA/BCA/B.Tech (CS/IT)/Other),
     `eligible_batch` (text, *"e.g. 2024, 2025, 2026"*), `qualification`,
     `min_cgpa` (*"e.g. 7.0 (Optional)"*), `experience_required`
     (Fresher/0–1 year/1–3 years/3+ years), `skills_required`*
     (comma-separated), `skills_preferred`.
  4. **Remuneration & Timeline** (money, warning): `salary` (*"e.g. ₹8–12
     LPA or ₹30k/Month"*), `perks`, `deadline`* (date), `joining_date`
     (date), `apply_method` (Link/Email/Portal → `#apply_input_field`;
     hidden if Portal, placeholder swaps Link→URL / Email→email) +
     `apply_link` (text).
  5. **Classification & Intelligence Calibration** (sliders, purple):
     `category` (Technology/Software/Data/Core/Business/Design),
     `target_role`, `openings` (number, `value="1"`, `min="1"`).
  - Footer buttons: `Cancel & Discard` (link → `admin_jobs`) and submit
    `Authorize & Publish Vacancy` (satellite-dish icon).
- **Backend (POST):** reads all above fields plus `ctc_range`,
  `selection[]` (→ `selection_process`, comma-joined) and `skill_level` —
  **none of those three have inputs in this template**, so they arrive as
  `None`/empty. `location = location_manual if location_select=='Other'
  else location_select`. Logo via `save_uploaded_file(..., prefix='logo',
  folder=COMPANY_LOGOS_FOLDER, max_dim=300)`. Validation: missing
  `title`/`company_name` → flash warning + redirect back. `INSERT INTO jobs
  (title, company, company_name, company_website, description, location,
  work_mode, employment_type, eligible_branch, eligible_batch, qualification,
  min_cgpa, experience_required, skills_required, skills_preferred, salary,
  ctc_range, perks, deadline, joining_date, apply_method, apply_link,
  openings, selection_process, category, target_role, skill_level,
  posted_by=current_user.id, company_logo, job_status='Open')` — note
  `company` is set to `company_name`. Flash `'Job added successfully!'`,
  redirect `admin_jobs`. GET passes **no variables**
  (`render_template('admin/add_job.html')`).
- **Charts/live:** none; JS only logo preview + dynamic show/hide of
  manual-location / apply-link fields.

## 9. Edit Job — Modify Vacancy

- **Route:** `GET, POST /admin/jobs/edit/<int:job_id>` — `admin_edit_job()`
  in `app.py:3441–3525` (non-admin → 403 JSON; missing job → flash `'Job
  not found!'` + redirect). Template: `templates/admin/edit_job.html`,
  **420 lines**.
- **Title:** `Edit Opportunity • {{ job.title }} • Admin Career Matrix`
- **Hero:** badge `OPPORTUNITY RECONFIGURATION • RECORD #{{ job.id }}`; H1
  `Modify Vacancy: <holographic>{{ job.title }}</h1>`; subtitle mentions
  `{{ job.company }}`. Back link `Return to Job Matrix`.
- **Layout:** identical structure/CSS to add_job (same 5 `.job-form-block`
  sections, same `max-width: 1080px`, same dropzone
  `#uploadZone`/`#logoInput`/`#previewBox` — but preview shows existing
  `job.company_logo` img if set, text *"Click to replace company logo"*),
  **except**:
  - Every field pre-filled with `value="{{ job.<field> }}"` / `selected`
    conditionals (e.g. `location_select` `Other` selected if `job.location`
    not in the 6 presets; `#manual_location` shown only then;
    `skills_required` falls back `job.skills_required or
    job.required_skills`; `company_name` falls back `job.company_name or
    job.company`).
  - Section 5 renamed **"Classification & Status Control"** and adds two
    extra fields: `skill_level` (Beginner/Intermediate/Advanced) and
    `job_status` (Open/Closed/Expired) — neither exists on the add form.
  - Submit button: `Save Updated Opportunity` (check-circle icon); cancel:
    `Cancel Changes`.
- **Form fields (27):** same 25 as add_job + `skill_level`, `job_status`.
  (Same JS: logo preview + `.dynamic-toggle` logic.)
- **Backend (POST):** same field extraction as add (including `ctc_range`,
  `selection[]` falling back to `job['selection_process']`, `job_status`
  defaulting to `job['job_status']`); new logo replaces old only if upload
  succeeds; `UPDATE jobs SET <all 29 columns incl. company_logo,
  job_status> WHERE id=?`; flash `'Job updated successfully!'`, redirect
  `admin_jobs`. GET passes `job=job` (single `SELECT * FROM jobs WHERE
  id=?` row).
- **Charts/live:** none.

## 10. Admin Events — Events & Meets Console

- **Route:** `GET /admin/events` — `admin_events()` in `app.py:5205–5211`
  (non-admin → flash + redirect home). Template:
  `templates/admin/admin_events.html`, **229 lines**.
- **Title:** `Events & Meets Console • Institutional Activity Desk`
- **Hero:** badge `EVENT HORIZON • REUNIONS, MEETS & WEBINARS`; H1
  `Institutional Events & <holographic>Alumni Meets</h1>`; subtitle about
  scheduling flagship campus assemblies, technical webinars, alumni
  networking dinners, and tracking live attendee RSVPs. Buttons: `Command
  Center` → dashboard; `RSVP Registrations` (warning) → admin_registrations;
  hero CTAs `Schedule New Event` (primary, opens `#createEventModal`) and
  `Manage RSVP Database` (outline → admin_registrations).
- **Layout:** hero → **Upcoming Scheduled Events & Summits** card
  (`.admin-card`) with `Add Event` button (same modal) → table
  `.admin-table` (columns: Event Name & Details | Date & Time |
  Classification | RSVP Capacity | Status | Controls). **Both rows are
  hardcoded HTML, not database-driven — the route passes no data at all**
  (`render_template('admin/admin_events.html')` with no variables):
  1. **Annual Alumni Meet 2026** — *"Flagship Institutional Reunion &
     Mentorship Summit"*, icon `fa-glass-cheers`, violet gradient
     `#7c3aed→#4f46e5`; **10 APR 2026, 10:00 AM IST • Campus Auditorium**;
     badge `badge-alumni` "Reunion Meet"; capacity bar 78% (`390 / 500
     Confirmed`, green); status `badge-verified` "Published".
  2. **Cloud Architecture & DevOps Masterclass** — *"Technical Alumni
     Knowledge Transfer & Placement Prep"*, icon `fa-laptop-code`, blue
     gradient `#0284c7→#0369a1`; **18 MAY 2026, 04:00 PM IST • Online
     Webinar**; badge `badge-student` "Tech Webinar"; capacity 45% (`90 /
     200 Registered`, info blue); status `badge-pending` "Registration
     Open".
  - Each row's Controls: circular View Attendees button (users icon →
    `admin_registrations`) and circular Edit button (sliders icon, **no
    handler**).
- **Modal `#createEventModal`** (`.modal-lg`, blue header): form
  `#createEventForm` with **unnamed inputs (no `name` attributes, no
  action)** — Event Name/Assembly Title* (text), Event Date* (date), Time
  & Timezone* (time), Category (select: Alumni Reunion / Technical Webinar
  / Mentorship Session / Placement Drive), Venue/Link (text), Event Brief
  Description (textarea rows=3). Footer: Cancel + `Save & Publish Event`
  with `onclick="alert('Event scheduled successfully!');
  location.reload();"` — **fake; nothing is saved to the backend**.
- **Backend data passed:** none. **Charts/live:** none (capacity bars are
  static widths 78%/45%).

## 11. Admin Registrations — Alumni Meet RSVP Registrations

- **Route:** `GET /admin/registrations` — `admin_registrations()` in
  `app.py:2756–2814` (non-admin → redirect home). Template:
  `templates/admin/admin_registrations.html`, **234 lines**.
- **Title:** `Alumni Meet Registrations • Attendee Command Console`
- **Hero:** badge `ALUMNI REUNION DESK • ATTENDEE REGISTRATIONS`; H1
  `Institutional Meet <holographic>RSVP Registrations</h1>`; subtitle about
  real-time tracking of confirmed attendees, batch reunions and delegate
  participation. Buttons: `Command Center` → dashboard; `Events Manager`
  (primary) → admin_events. **4 hero stat boxes**
  (`.admin-hero-stat-box`): Students RSVP `{{ stats.students or 0 }}`
  (sky `#38bdf8`, "Active Learners"); Alumni RSVP `{{ stats.alumni or 0 }}`
  (amber `#fbbf24`, "Graduates & Mentors"); Faculty RSVP `{{ stats.faculty
  or 0 }}` (green `#34d399`, "Professors & Guides"); Total Confirmed
  `{{ stats.total or 0 }}` (purple `#c084fc`, "Gross Attendance").
- **Layout:** hero → **Search & Filter bar** (`.admin-card`, GET form to
  `admin_registrations`): search input `name="search"` (`value="{{
  search_query }}"`, placeholder *"Search by name, email, department…"*),
  `name="role_filter"` select (All Classification Roles / student /
  alumni / faculty; auto-submits on change, `current_filter` marks
  selected), Apply button (primary), Export CSV button (green,
  `onclick="exportData()"`) → **Confirmed Reunion Attendee Records** card
  with `{{ registrations|length }} Result(s)` badge → table `.admin-table`
  (columns: Attendee Identity | Role Classification | Department & Ref |
  Registration Date | Inspect Profile). Row: avatar (42 px circle —
  `user_profile_pic` img if `/`, `data:image/` or `http` and ≠
  `default.jpg`, else initial badge `.avatar-initials-{{role}}`),
  `reg.name`, `reg.email` (mono), role pill `badge-{{reg.role}}`
  uppercased, department (or `'General Studies'`), sub-line Roll:
  `reg.enrollment_no` for students else `reg.designation or 'Alumni
  Delegate'`, `reg.registered_at` (mono + clock icon), circular Inspect
  button `.btn-view-details` (`data-user-id="{{ reg.user_id }}"`,
  `data-user-role="{{ reg.role }}"`). Empty state
  (`.admin-empty-state`): *"No Attendee Records Detected"* + `Reset All
  Filters` link.
- **Backend data passed:** `registrations`, `stats`, `current_filter=role_filter`,
  `search_query`.
  - `registrations`: `SELECT r.*, u.profile_pic AS user_profile_pic, u.id
    AS user_account_id FROM registration_log r LEFT JOIN users u ON
    r.email=u.email WHERE 1=1` + optional `AND r.role=?` + optional search
    `LIKE %…%` over `name, email, phone, department, enrollment_no, degree,
    company_name`; `ORDER BY registered_at DESC`. Note: template uses
    `reg.user_id`, but the query selects `user_account_id` (not aliased as
    `user_id`) — the profile link may resolve to empty.
  - `stats`: `{students, alumni, faculty, with_phone, total}` — counts from
    `registration_log` by role / phone not-null / all. `with_phone` is
    computed but **not displayed**.
- **Actions:** GET search/filter; `exportData()` — button shows spinner
  *"Preparing CSV…"*, then after 600 ms navigates to
  `/admin/export/registrations`; JS `.btn-view-details` click routes by
  role: student → `/student/profile/{id}`, alumni → `/alumni/profile/{id}`,
  faculty → `/faculty/profile/{id}`, admin → `/admin/profile/{id}`, else
  `/profile/{id}`.
- **Export route** `GET /admin/export/registrations` —
  `admin_export_registrations()` in `app.py:2816–2876` (non-admin → 403
  JSON): `SELECT * FROM registration_log ORDER BY registered_at DESC`; CSV
  columns: `Record ID, Full Name, Email Address, Primary Phone, System
  Classification, Core Department, Academic Degree, Temporal Stamp
  (Registration)`; filename
  `community_matrix_export_YYYYMMDD_HHMMSS.csv`, `Content-Disposition:
  attachment`.
- **Charts/live:** none (stats are server-rendered).

## 12. WhatsApp Broadcast — Broadcast Console

- **Route:** `GET, POST /admin/whatsapp-broadcast` —
  `admin_whatsapp_broadcast()` in `app.py:3527–3587` (non-admin → flash +
  redirect home). Template: `templates/admin/whatsapp_broadcast.html`,
  **1,160 lines**.
- **Title:** `WhatsApp Broadcast Console • Enterprise Outreach Desk`
- **Hero:** badge `WHATSAPP OUTREACH DESK • HIGH-DELIVERY BROADCAST SUITE`;
  H1 `Institutional <holographic>WhatsApp Broadcast</h1>`; subtitle about
  automated multi-role communication gateway — dispatch announcements,
  placement drives and reunion alerts directly to verified recipients with
  custom exclusion filtering and live smartphone preview. Three glass pills:
  `Direct Device Delivery` (WhatsApp green), `Non-Destructive Batch
  Exclusion` (shield), `Rate-Limited Sequential Dispatch` (bolt).
  `Command Center` link → dashboard. CSS vars: `--wp-green #25d366`,
  `--wp-green-dark #128c7e`, `--wp-green-deep #075e54`, `--wp-bubble
  #d9fdd3`, `--wp-bg-chat #efeae2`.
- **Layout in order:**
  1. Hero.
  2. **Campaign Parameters & Composer** card (`.admin-card`): header with
     `#charBadge` (`0 Characters`) + mobile-only `Preview Phone` button
     `#toggleMobilePreviewBtn`. **Quick Message Templates** (`.quick-chip`,
     `onclick="applyTemplate('…')"`): 🎓 Grand Alumni Reunion 2026
     (`reunion`), 💼 Placement Drive Alert (`placement`), 📢 Campus Notice
     & Exam Update (`notice`), 🎉 Festive & New Year Greetings (`festival`)
     — full preset texts live in JS `templates` object (reunion dated Sat
     14 Nov 2026, 10 AM, Campus Amphitheatre; placement links to the jobs
     page; notice links to announcements).
  3. Form `#broadcastForm` (`method="POST"`, self): left column
     (`.col-lg-7`): `role` select `#role` (`all` 👥 Public Community /
     `student` 🎓 / `alumni` 💼 / `faculty` 🏛️, `selected_role` preserved);
     formatting toolbar (`.format-chip`: `*Bold*`, `_Italic_`, `~Strike~`
     via `insertFormat()`, emoji inserters 📢🎓💼📅📍🔗 via `insertEmoji()`);
     `message` textarea `#message` rows=6 (required, `{{ message }}`,
     placeholder mentions `*bold*, _italic_`); buttons: `Preview
     Recipients` (`type=submit name="action" value="generate"`, outline)
     and `Launch Dispatch` (`name="action" value="auto_send"`, green,
     paper-plane). Right column (`#phonePreviewColumn`, `.col-lg-5`):
     **live phone mockup** (`.wp-mockup-wrapper`, dark `#1e293b` frame
     radius 36 px, header `Alumni Hub Official / Institutional Broadcast
     Bot` in `--wp-green-deep`, chat bubble `.wp-chat-bubble`
     `#mockupBubble` with `#mockupText` synced live from textarea +
     `#mockupTime` set to current time + blue double-tick
     `fa-check-double` `#53bdeb`).
  4. **Filtered Broadcast Pipeline** card `#recipientsCard` (only `{% if
     users %}`): hidden `#autoStartFlag` (`'true' if auto_start else
     'false'` — if true, auto-clicks Start after 1200 ms). Header: `{{
     users|length }} Active` badge `#activeBadgeCount`, `0 Excluded` badge
     `#excludedBadgeCount` (hidden until >0), note *"Total N contact nodes
     retrieved…"*. Controls: `#startAutoBroadcast` (green, Play),
     `#stopAutoBroadcast` (red Pause, `d-none` initially), `#restoreAllBtn`
     (`Restore All (<span id="restoreCountNum">)`). **Progress dashboard**
     `#progressContainer` (`d-none` initially): `#progressStatus`,
     `#progressPercent`, striped animated `#progressBar`, counters
     `#sentCount` (DELIVERED), `#pendingCount` (QUEUED, init
     `users|length`), `#excludedStatCount`, `#failCount`. Filter/search bar:
     `#recipientSearch` (oninput `filterRecipients()`), role tabs
     `.filter-tab-btn` All / Students / Alumni / Faculty / Excluded,
     `#noResultsState` empty state. **Desktop table** `#userTable`
     (columns: master checkbox `#selectAllCheckbox` checked / Recipient
     Name / Contact Phone / Role / Dispatch Status / Manual Actions) and
     **mobile cards** `#mobileCardsContainer` (`.recipient-card-mobile`,
     shown <768 px). Each recipient row `#row-{{loop.index0}}` / card
     `#mcard-{{loop.index0}}` carries `data-index/name/phone/role/message/
     excluded="false"`; avatar 38 px (profile_pic or initial badge), `Node
     #{{loop.index}}`, phone (mono + copy button `copyPhone()`), role pill
     `badge-{{role}}`, status badge `.status-badge` (initial *"Queued"*),
     per-recipient actions: direct WhatsApp link `user.whatsapp_url`
     (green circle, `target=_blank`), Exclude (`.exclude-btn`,
     `excludeRecipient(i)`), Restore (`.restore-btn`, hidden,
     `restoreRecipient(i)`). Undo toast `#undoToast` (`.wb-toast`,
     bottom-center, `UNDO` button `undoLastExclude()`, 4 s).
- **Backend data passed:** `users`, `selected_role`, `message`,
  `auto_start`. On POST: `action = form['action']` (`generate` default;
  `auto_send` → `auto_start=True`); if `message` empty → flash warning and
  no query; else `SELECT name, role, phone, profile_pic FROM users WHERE
  is_verified=1 AND role != 'admin'` (+ `AND role=?` if not `all`); phone
  cleaned to digits, 10-digit → prefix `91`, else last-10 + `91`;
  `whatsapp_url = f"https://wa.me/{clean_phone}?text={quote(message)}"`;
  each user dict `{name, role, phone, profile_pic, whatsapp_url}`. No users
  → flash `No verified users found for role: …`. GET renders with empty
  `users`.
- **Send API** `POST /admin/whatsapp-send-api` — `admin_whatsapp_send_api()`
  in `app.py:3589–3642` (non-admin → 403 JSON): JSON `{phone, message}`;
  validates ≥10 digits, normalizes to `+91…` (≥12 chars), then
  `pywhatkit.sendwhatmsg_instantly(phone_no, message, wait_time=15,
  tab_close=True, close_time=3)` (lazy import; opens a browser tab on the
  server). Returns `{success: True, message: 'Message sequence initiated'}`
  or `{success: False, error}` (400/500).
- **Live dispatch (JS):** Start collects checked, non-excluded rows into
  `dispatchQueue`, confirms count, then `processNextRecipient()`
  sequentially: per-recipient status → *"Transmitting…"* (warning) → POST
  `/admin/whatsapp-send-api` → *"Delivered"* (green) or *"Failed"* (red);
  progress bar/percent + counters update; **3,500 ms delay between
  recipients** (`setTimeout(processNextRecipient, 3500)`); Stop pauses
  (`isRunning=false`, clears timer); completion swaps Start to `Restart
  Broadcast`. Live composer sync: character counter + phone mockup update
  on every input.
- **Charts:** none. Live features: phone mockup, sequential rate-limited
  dispatcher with progress/counters, exclusion engine (non-destructive,
  session-only), role/search filtering.

## 13. Reports — Incident Tickets & Support Tickets

- **Route:** `GET /admin/reports` — `admin_reports()` in `app.py:4996–5071`
  (non-admin → flash + redirect home). Template:
  `templates/admin/reports.html`, **1,095 lines**.
- **Title:** `Incident Tickets & System Reports • Admin Compliance Console`
- **Hero:** badge `TICKET DESK • REAL-TIME INCIDENT RESOLUTION`; H1 `System
  Incident & <holographic>Support Tickets</h1>`; subtitle about real-time
  queue of community issue reports, authentication disputes, mentorship
  tickets and contact inquiries. Right: `#liveSyncStatus` badge *"Live Sync
  Active"* + `Command Center` link. Pills: `Live Ingestion Engine` (red
  tint), `Audit Compliance Active` (green tint), `Sync Now` button
  `#btnManualSync` (spinner `#syncSpinner`).
- **Layout in order:**
  1. Hero.
  2. **4 stat cards** (`.admin-metrics-row`, `.report-stat-card`, top accent
     bar `--card-accent`): Pending Action `#statPending` (`{{
     pending_count }}`, red `#ef4444`, `fa-exclamation-triangle`); In
     Investigation `#statProgress` (`{{ in_progress_count }}`, amber
     `#f59e0b`, spinning `fa-spinner`); Resolved Issues `#statResolved` (`{{
     resolved_count }}`, green `#10b981`, `fa-check-double`); Total
     Submissions `#statTotal` (`{{ total_count }}`, blue `#0284c7`,
     `fa-ticket-alt`). Numbers 2.1 rem Outfit.
  3. **Toolbar** (`.report-toolbar-card`): status tabs `#statusFilterTabs`
     (`.status-tab-btn`, `data-status`): All Tickets `#tabCountAll`
     (`total_count`), Pending, In Progress, Resolved (active tab = blue
     gradient `#0284c7→#2563eb`); search `#ticketSearchInput` (placeholder
     *"Search ticket #, name, email…"*); category select
     `#categoryFilterSelect` (All Categories / Bug Report / Account Access
     / Contact Inquiry / Mentorship / Job Posting / General Feedback);
     Export button `#btnExportCsv`.
  4. **Active Incident Queue** card: `#showingCount` (*"N tickets
     visible"*); table `#ticketsTable` (columns: Ticket ID | Reporter |
     Category | Subject & Details | Priority | Submitted On | Status |
     Intervene). Row `#row-{{t.id}}` with `data-ticket-id/status/category/
     search` (ticket_num + reporter_name + reporter_email + subject +
     description): Ticket ID badge `.tkt-num-badge` (mono, click
     `copyTicketNum()`); reporter name + role pill
     `badge-{{reporter_role|lower}}` + mailto envelope; category pill
     (mono, blue); subject + description (truncated 280 px ellipsis);
     priority `.badge-priority-high` (red, fire icon; High/Urgent) /
     `-med` (amber) / `-low` (grey); `created_at[:16]` mono; status
     `.badge-tkt-pending` (red, spinning clock) / `.badge-tkt-progress`
     (amber, spinner) / `.badge-tkt-resolved` (green); Intervene buttons
     (34 px circles): View (eye, `openTicketModalById(id)`), 1-Click
     Resolve (green check, only if not Resolved, `quickResolveTicket(id)`),
     Delete (red trash, `deleteTicket(id)`). Empty state `#emptyTableRow`:
     *"Incident Queue Clear"* + Refresh Queue button; `#noSearchResults`
     (hidden) with `Reset Filters` (`resetFilters()`).
  5. **Ticket Detail modal** `#ticketDetailModal` (`.modal-lg`,
     `.modal-content-luxury` radius 28 px, dark gradient header
     `#0b1329→#1e293b`): `#modalTicketNum`, `#modalSubject`, metadata row
     (`#modalReporterName/Role/Email` — email link
     `mailto:…?subject=Re: [ticket] subject`, `#modalCategory`,
     `#modalPriority`), full description `#modalDescription` (pre-wrap),
     **Administrative Intervention** box: `#modalStatusSelect` (Pending 🔴
     / In Progress 🟡 / Resolved 🟢 / Closed ⚪), `#modalAuditTrail`
     (*"Not resolved yet"* or *"Resolved by X on Y"*),
     `#modalAdminNotes` textarea; footer Close + `#btnSaveTicketModal`
     (Save Changes).
- **Backend data passed:** `tickets`, `total_count`, `pending_count`,
  `in_progress_count`, `resolved_count`.
  - Route ensures `support_tickets` table exists (`CREATE TABLE IF NOT
    EXISTS` with columns id, ticket_num UNIQUE, reporter_id, reporter_name,
    reporter_email, reporter_role default `'Guest'`, category, subject,
    description, priority default `'Medium'`, status default `'Pending'`,
    admin_notes, resolved_by, resolved_at, created_at, updated_at), then
    **deletes demo/test rows on every load** (`ticket_num IN
    ('TKT-1024','TKT-1023','TKT-3BCDC9') OR email/name LIKE '%test%' OR
    email LIKE '%example.com%'`), then selects all tickets ordered by
    status (Pending→1, In Progress→2, Resolved→3, else 4), `id DESC`.
    Counts computed in Python (`sum(1 for t …)`); note `resolved_count`
    counts only status `'Resolved'`, not `'Closed'`.
- **Live APIs (all admin-only):**
  - `GET /api/admin/reports/live` (`app.py:5073`): same query, returns
    `{success, total_count, pending_count, in_progress_count,
    resolved_count, tickets}`. JS polls it **every 12 s**
    (`setInterval(fetchLiveTickets, 12000)`) + on Sync Now; if ticket JSON
    changed, `renderFullTable()` re-renders tbody and flashes
    `#liveSyncStatus` (`"+N New Report Received!"` / `"Queue
    Synchronized"`).
  - `POST /api/admin/reports/<int:ticket_id>/status` (`app.py:5113`):
    JSON/form `{status, admin_notes}`; valid statuses Pending/In
    Progress/Resolved/Closed (else 400); Resolved/Closed sets
    `resolved_by=current_user.name`, `resolved_at=now`, else clears both;
    `admin_notes` updated only if non-empty. JS `updateTicketStatus()`
    does optimistic UI first, then POSTs.
  - `POST /api/admin/reports/<int:ticket_id>/delete` (`app.py:5150`):
    `DELETE FROM support_tickets`, returns `{success, ticket_id}`.
  - Client-side: status/category/search filtering
    (`filterAndRenderRows()`), `exportToCsv()` →
    `AlumniHub_Incident_Report_YYYY-MM-DD.csv` with columns Ticket ID,
    Reporter Name, Reporter Email, Role, Category, Priority, Status,
    Created At, Resolved By, Resolved At, Description.
- **Charts:** none. Live features: 12-second polling live sync, optimistic
  status updates, quick-resolve, live counters/tabs.

## 14. Admin Profile — View

- **Route:** `GET /admin/profile/<int:user_id>` — `app.py:1468`,
  `admin_profile()` (1470). `@login_required`, GET only.
- **Template:** `templates/admin/profile_admin.html` — **176 lines**.
  Title: `Administrator Profile • Platform Root Authority`.
- **Auth:** `if current_user.role != 'admin': flash('Access denied!',
  'danger'); redirect(home)`. **No `abort(403)` anywhere in the `/admin/*`
  routes.** Any logged-in admin may view any admin's profile — no
  self-only check.
- **Backend data:** single query `SELECT * FROM users WHERE id = ?`. If
  missing or `user['role'] != 'admin'`: `flash('Admin not found!',
  'danger')`, redirect home. On exception: `flash('Error loading profile!',
  'danger')`, redirect home. Only context passed: `user=user` (a
  `sqlite3.Row`, full `users` row). No stats/service calls.
- **Hero:** live badge `ROOT AUTHORITY • SUPER ADMINISTRATOR PROFILE`
  (`admin-live-badge` + `live-pulse-dot`). Top-right buttons: `Command
  Center` → dashboard (`fa-th-large`, `btn-outline-light`); `Edit
  Credentials` → `edit_admin_profile` (`fa-user-edit`, `btn-primary`). H1:
  `<span class="hero-title-prefix">Institutional</span> <span
  class="text-holographic-adm">Administrator Profile</span>`. Subtitle:
  "Primary system administrator identity node with full ecosystem
  governance, role permissions, and database manipulation authority."
  Ambient orbs `admin-ambient-ball admin-ball-1/2/3`.
- **Layout:** `row g-4`: left `col-lg-4` identity card, right `col-lg-8`
  info card, both `admin-card` (`h-100`).
  - **Left card:** 140×140 avatar: `<img>` only if `profile_pic` starts
    with `/`, `data:image/` or `http` and `!= 'default.jpg'`, else
    initial-letter fallback — first letter of `user['name']` upper-cased
    (default `'A'`), `background: linear-gradient(135deg, #0284c7 0%,
    #7c3aed 100%)`, `font-size: 3.2rem`, Outfit; `onerror` swaps to the
    fallback div. Green online dot `bg-success`, 16×16, `title="System
    Online"`. Name `h3`; handle `@{{ user['email'].split('@')[0] }}`
    (fallback `'admin'`); badge `bg-danger bg-opacity-10 text-danger`
    with `fa-crown` (amber): `SUPER ADMINISTRATOR`. Info box: `Ecosystem
    Role: Super Administrator` / `Permission Scope: All Nodes (Full
    Access)`. Buttons: `Edit Admin Profile` (primary, `fa-user-edit` →
    edit_admin_profile) and `Change Password` (outline, `fa-key` →
    `change_password`, route `app.py:2566`).
  - **Right card:** header `fa-id-card`: `Account Credentials & Contact
    Metadata`. 4 tiles (`bg-light border rounded-4`): Full Registered
    Name; System Root Handle (email local-part, monospace); Primary
    Administrative Email (`text-truncate`); Telephone Contact (or `Not
    Provided`). Header `fa-th-large`: `Operational Shortcuts` — 4 tiles:
    User Directory → `admin_view_users(role='all')` (`fa-users`); System
    Analytics → `admin_analytics` (`fa-chart-line`); Support Tickets →
    endpoint `reports`, `GET /reports` (`app.py:4986`), **not**
    `/admin/reports`; Admin Dashboard → `dashboard_admin`
    (`fa-tachometer-alt`).
- **Forms:** none — view-only, links only.

## 15. Admin Profile — Edit

- **Route:** `GET, POST /admin/profile/<int:user_id>/edit` — `app.py:2383`,
  `edit_admin_profile()` (2385). `@login_required`.
- **Template:** `templates/admin/edit_admin_profile.html` — **363 lines**.
  Title: `Edit Administrator Profile • Platform Root Authority`.
- **Auth (double check, redundant):** 1) `if current_user.id != user_id and
  current_user.role != 'admin': flash('You cannot edit this profile!',
  'danger'); redirect(home)`; 2) `if current_user.role != 'admin':
  flash('Only admins can edit admin profiles!','danger'); redirect(home)`.
  Net effect: **only admins, and any admin can edit any admin** (no
  self-only restriction).
- **Backend — GET:** `SELECT * FROM users WHERE id = ?`; if missing /
  non-admin: `flash('Admin not found!','danger')`, redirect home; else
  `render_template('admin/edit_admin_profile.html', user=user)`.
- **Backend — POST:** `name/email/phone = request.form.get(...).strip()`.
  If any empty: re-fetch user, `flash('Name, Email, and Phone are
  required!','warning')`, re-render edit template (no redirect). Photo:
  `if 'profile_pic' in request.files: save_uploaded_file(request.files['profile_pic'],
  prefix='admin', user_id=user_id)` — helper is `utils/helpers.py:59`
  (imported `app.py:31`), not defined in `app.py`. Update: `UPDATE users
  SET name=?, email=?, phone=?, profile_pic=? WHERE id=?` if a pic was
  saved, else without `profile_pic`; `conn.commit()`; `flash('Admin profile
  updated successfully!','success')`; redirect `url_for('admin_profile',
  user_id=user_id)`. Exception: `conn.rollback()`, `flash(f'Error updating
  profile: {str(e)}','danger')`, redirect `admin_profile`. **No
  email-uniqueness or phone-format check server-side** (only HTML
  `type="email"`/`type="tel"` + `required`).
- **Hero:** same wrapper/CSS/fonts as view, container `max-width: 860px`.
  Badge: `CREDENTIAL UPDATE • ROOT ADMINISTRATOR CONSOLE`. Button: `Return
  to Profile` → `admin_profile` (`fa-arrow-left`). H1: `Modify Admin` +
  holographic `Credentials`. Subtitle: "Update verified system
  administrative metadata, contact telephone, and identity avatar
  credentials."
- **Avatar stage (inline `<style>`, ~lines 10–108):** `luxury-avatar-stage`
  150×150, centred; `luxury-avatar-glow` (gradient `#0284c7 → #7c3aed →
  #38bdf8`, blur 12 px, `avatarPulseGlow` 4 s infinite alternate);
  `luxury-avatar-ring` (4 px gradient padding, hover scales glow/img);
  `luxury-avatar-inner` bg `#0b1329`; hover overlay
  `luxury-avatar-overlay` (`rgba(11,19,41,0.65)`, `fa-camera`, `Update
  Photo`); camera badge `luxury-avatar-badge` 44 px, gradient, white 3 px
  border, hover `scale(1.12) rotate(10deg)`. Jinja: custom photo shown only
  if `profile_pic` starts with `data:image/` | `http` | `/`, is not
  `default.jpg`, and is not one hard-coded excluded upload filename. If
  true: `<img id="photoPreview">`; else inline SVG `#defaultAvatarSvg`
  (viewBox `0 0 160 160`, gradients `admRadGrad` `#1e293b→#0b1329`,
  `admAccGrad` `#38bdf8→#0284c7→#7c3aed`, silhouette + dashed orbit ring +
  star/shield emblem). Hidden input `<input type="file" id="profile_pic"
  name="profile_pic" class="d-none" accept="image/*"
  onchange="previewPhoto(this)">`; clicking ring/badge/`Select Photo`
  triggers it. Badges: `ROOT ADMINISTRATOR` (`fa-shield-alt`);
  `#uploadStatusBadge` `NEW PHOTO SELECTED` (initially `d-none`).
  Buttons: `Select Photo` (`btn-outline-primary`); `#resetPhotoBtn`
  `Reset` (initially `d-none`); hint: "JPG, PNG, WEBP (Max 16MB).
  Automatically optimized for cloud delivery."
- **Form:** `<form method="POST" enctype="multipart/form-data">`, no
  explicit `action` (posts to same URL). Fields (all `required`, class
  `admin-input`, labels `admin-form-label`): `name` (text, `Full Name*`,
  placeholder "Enter full legal name"); `email` (email, `Administrative
  Email Address*`); `phone` (tel, `Contact Telephone Number*`, placeholder
  `e.g. 7348619567`). Security box: `fa-shield-check`, "Serverless Cloud
  Synchronization Active — Updates are secured, validated, and synchronized
  permanently across the platform." Actions (right-aligned): `Cancel` →
  admin_profile (outline, `fa-times`); `Change Password` →
  change_password (outline, `border-color: #38bdf8; color: #0284c7`);
  submit `Save Profile Changes` (primary shadow, `fa-save`).
- **Inline JS:** `previewPhoto(input)`: rejects `file.size >
  16*1024*1024` with `alert('Selected image exceeds 16MB limit…')`;
  `FileReader` → `photoPreview.src`, swaps `d-none/d-block` on img/SVG,
  shows `#uploadStatusBadge` + `#resetPhotoBtn`. `handleAvatarError(img)`:
  hides img, restores SVG. `resetToDefaultAvatar()`: clears input/preview,
  restores SVG, hides badge/reset button.

---

## 16. services/admin_service.py — all 6 functions

Module docstring (lines 1–11) is **stale**: it lists only `get_role_counts`,
`get_yearly_stats`, `get_admin_job_stats`. Imports: `logging`, `datetime`,
`get_db_connection` from `db_utils`. `app.py:45` imports only 3 of the 6:
`from services.admin_service import get_all_connections,
get_connection_activity, get_user_statistics`. `get_role_counts`,
`get_yearly_stats`, `get_admin_job_stats` are **defined but never
imported/used by `app.py`** — `dashboard_admin` (`app.py:1741`) and
`admin_analytics` re-implement the same counts inline.

| # | Function (line) | Signature / SQL & logic | Return |
|---|---|---|---|
| 1 | `get_user_statistics` (L20) | `def get_user_statistics(conn, user_id: int) -> dict`. One query: `SELECT COUNT(*) AS connection_count FROM connections WHERE user_id_1 = ? OR user_id_2 = ?` (both params `user_id`). Docstring: no followers table; followers/following derived from accepted (actually all) bidirectional connections. | `{"total_connections": n, "total_followers": n, "total_following": n}` — all three keys are the **same** count. |
| 2 | `get_all_connections` (L45) | `def get_all_connections(conn, role_filter: str = "all", search: str = "") -> list`. Normalises `role_filter` lower/strip, `search` strip, `like_term = f"%{search}%"`. One big query: `connection_requests cr` JOIN `users su` (sender) + `users ru` (receiver); LEFT JOIN `student_profile`/`alumni_profile`/`faculty_profile` for sender and receiver (role-gated joins). Columns: `cr.id, sender_id, receiver_id, status, created_at AS request_sent_at, accepted_at AS request_accepted_at`, plus per-side `name, email, role`, `department` via `COALESCE(sp/alumni/faculty.department, users.branch, 'N/A')`, `skills` via `COALESCE(sp.skills, users.skills, '')`, `current_domain`, `passing_year` via `COALESCE(sp.semester, ap.pass_year, users.passing_year)`, `company` via `COALESCE(ap.company_name, users.company, '')`. WHERE: `(?='all' OR su.role=? OR ru.role=?)` and `(search='' OR su/ru.name/email LIKE ?)`. `ORDER BY cr.created_at DESC`. | `list[dict]` — `[dict(r) for r in rows]`. |
| 3 | `get_connection_activity` (L124) | `def get_connection_activity(conn, role_filter="all", search="") -> list`. Calls `get_all_connections(...)`; returns `[]` if empty. **N+1: 5 extra queries per record** — `get_user_statistics` for sender and receiver; `SELECT last_login, online_status FROM user_activity WHERE user_id=?` for sender and receiver; `SELECT COUNT(*) AS message_count FROM private_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)`, wrapped in `try/except` (missing table → 0). | Same list, each row enriched in place with `sender_stats`, `receiver_stats` (dicts from #1), `sender_activity`/`receiver_activity` (`{"last_login": …\|None, "online_status": …\|"offline"}`), `messages_exchanged: int`. |
| 4 | `get_role_counts` (L190) | `def get_role_counts(conn) -> dict`. One query: `SELECT role, COUNT(*) as cnt FROM users GROUP BY role`; seeds `{'student':0,'alumni':0,'faculty':0,'admin':0,'total':0}`, fills known roles, `total` sums all rows (including any unknown role). | `{'student':int,'alumni':int,'faculty':int,'admin':int,'total':int}`. |
| 5 | `get_yearly_stats` (L212) | `def get_yearly_stats(conn, num_years: int = 5) -> dict`. `years = [str(y) for y in range(current_year-num_years+1, current_year+1)]`. Query 1: `SELECT strftime('%Y', created_at) as reg_year, role, COUNT(*) FROM users WHERE strftime('%Y',created_at) >= ? GROUP BY reg_year, role`. Query 2 (events): same pattern on `alumni_meet_registration`. Builds `year_map` (student/alumni/faculty only — admin excluded) and `event_map`. | `{'years':[…], 'students':[…], 'alumni':[…], 'faculty':[…], 'events':[…]}` — parallel lists, one entry per year. |
| 6 | `get_admin_job_stats` (L268) | `def get_admin_job_stats(conn) -> dict`. Query 1: `SELECT COUNT(*) as total, SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active, SUM(CASE WHEN is_active=0 THEN 1 ELSE 0 END) as closed FROM jobs`. Query 2: `SELECT COUNT(*) as cnt FROM job_applications`. `or 0` guards on `None`. | `{'total':int,'active':int,'closed':int,'applications':int}`. |

## 17. templates/base.html — admin navigation

### Brand / toggler (L820–846)
- Brand `<a class="navbar-brand brand-premium admin-brand-wrap">` (admin
  only; `faculty-brand-wrap` for faculty). `href`: `dashboard_admin` for
  admin, `dashboard_faculty` for faculty, `/` otherwise; `title`: `Alumni
  Hub Admin Console`. Logo `static/images/icons/app-logo.png` + `<span
  class="admin-pulse-beacon" title="Security Active">` (admin only).
- Brand tag (L831–832): `<span class="admin-brand-tag" title="Enterprise
  Admin Portal"><i class="fas fa-shield-alt"></i> ADMIN</span>`.
- Toggler: `navbar-toggler custom-toggler admin-custom-toggler` (admin only).

### Desktop nav — admin branch (`{% elif current_user.role == 'admin' %}`, L1091–1265), in order
1. **Dashboard** — `id="navAdminDashboard"`, `nav-admin-btn`, active when
   `request.endpoint == 'dashboard_admin'`; `url_for('dashboard_admin')`;
   icon `fa-gauge-high text-primary`.
2. **Messages** — `id="navAdminMessages"`, active when endpoint is `messages`
   or path starts `/messages`; hardcoded `href="/messages"`; icon
   `fa-comments text-info`.
3. **Directory** dropdown — `id="usersDropdown"`, `nav-admin-btn
   dropdown-toggle`, icon `fa-users-gear text-success`; active when
   `'admin_view_users'` or `'admin_approve'` in endpoint. Menu
   (`nav-admin-dropdown-menu`): intro `User Governance / Members, Roles &
   Security` (`fa-users-gear`); **All Members** →
   `admin_view_users(role='all')` (`fa-list-check`, "Full user database");
   divider; **Students Roster** → `role='student'` (`fa-user-graduate`);
   **Alumni Directory** → `role='alumni'` (`fa-user-tie`); **Faculty
   Directory** → `role='faculty'` (`fa-chalkboard-user`); divider;
   **Pending Approvals** → `admin_approve_requests` (`fa-user-clock`,
   `nav-admin-item-urgent`, red text + `ACTION` badge `bg-danger-subtle`).
4. **System Control** dropdown — `id="systemDropdown"`, icon
   `fa-shield-halved text-warning`; active when endpoint contains `jobs`,
   `whatsapp`, `messaging_control`, `connection_monitor`, `analytics`,
   `registrations`, `reports` or `stats`. Menu (`nav-system-menu
   nav-admin-dropdown-menu`), intro `Enterprise Control Hub / Governance,
   Comms & Infrastructure` (`fa-shield-alt`):
   - Heading `CAREER & TALENT`: **Jobs Matrix** → `admin_jobs`
     (`fa-briefcase`); **Job Approvals Queue** → `admin_jobs#pending`
     (`fa-clipboard-check`).
   - Heading `COMMUNICATIONS & BROADCAST`: **Community Group** →
     `url_for('community_group')` (`fa-users`, inline WhatsApp-green
     `#25d366`); **WhatsApp Broadcast** → `admin_whatsapp_broadcast`
     (`fa-brands fa-whatsapp`); **Messaging Control** →
     `admin_messaging_control` (`fa-comments`); **Campus Announcements** →
     hardcoded `/announcements` (`fa-bullhorn`).
   - Heading `INFRASTRUCTURE & AUDIT`: **Connection Monitor** →
     `admin_connection_monitor` (`fa-network-wired`); **Platform Analytics**
     → `admin_analytics` (`fa-chart-line`); **Registration Logs** →
     `admin_registrations` (`fa-clipboard-list`); **Event RSVPs** →
     hardcoded `/admin/events` (`fa-calendar-check`); **Incident Reports**
     → hardcoded `/admin/reports` (`fa-triangle-exclamation`); **System
     Statistics** → hardcoded `/admin/stats` (`fa-chart-pie`).
5. PWA button (L1266–1275): for `role in ['admin','faculty']`, hidden
   `btn-admin-utility-icon d-none`, `id="pwaNavInstallBtnAuth"`.

### User pill (L1278–1340)
- `<li class="nav-item dropdown user-dropdown admin-user-dropdown">`;
  toggle `<a class="nav-link user-pill admin-user-pill dropdown-toggle"
  id="navbarDropdown">`.
- Avatar `<div class="user-avatar admin-user-avatar-ring">`:
  `current_user.profile_pic` if `/`/`data:image/`/`http` and `!=
  'default.jpg'` (with `onerror` fallback to initials via `| initials`
  filter), else initials span. Name `<span class="user-name d-none
  d-sm-inline">`; admin-only `<span class="admin-user-pill-tag ms-1"><i
  class="fas fa-shield-alt"></i> ADMIN</span>`.
- Dropdown menu: header `Signed in as` + name; **My Profile** → `/profile`
  (`fa-user`); **Messages** → `/messages` (`fa-comment-alt`);
  **Settings** — role-dependent: admin →
  `url_for('edit_admin_profile', user_id=current_user.id)` (`fa-cog`);
  student → `settings`; alumni → `edit_alumni_profile`; faculty →
  `edit_faculty_profile`; **Change Password** → `/change_password`
  (`fa-lock`); divider; **Logout** → `/logout` (`text-danger`,
  `fa-sign-out-alt`).

### Mobile drawer (L1341–1960)
- Overlay `<div class="mobile-menu-overlay admin-drawer-theme"
  id="mobileMenuOverlay" aria-hidden="true">` (admin;
  `faculty-drawer-theme` for faculty). Topbar: logo
  `static/images/icons/app-logo.png`, `ALUMNI HUB`, role tag `<span
  class="drawer-role-tag role-tag-admin"><i class="fas fa-shield-alt
  me-1"></i> ADMIN</span>` (L1352), close button `#closeMobileMenu`.
- **SUPER ADMIN card** (L1363–1410, `admin-mobile-card`, `--delay: 0.08s`):
  header `admin-mobile-status-pill` (`admin-status-pulse` + `ADMIN
  CONSOLE`) + `admin-role-badge` `SUPER ADMIN`. User row:
  `admin-mobile-avatar-box` — pic (`admin-mobile-img`, `onerror` →
  initials) or `admin-mobile-initials` (`| initials`), plus
  `admin-avatar-badge-icon` (`fa-shield-halved`, "Super Admin");
  `admin-mobile-name` (name, white bold) + `admin-mobile-email` (email or
  fallback `System Administrator`). **4 quick tiles**
  (`admin-mobile-quick-grid`, all `admin-tile-btn … adm-drawer-link`):
  Dashboard → `dashboard_admin` (`tile-indigo`, `fa-gauge-high`);
  Approvals → `admin_approve_requests` (`tile-rose`, `fa-user-check`);
  WhatsApp → `admin_whatsapp_broadcast` (`tile-emerald`, `fa-brands
  fa-whatsapp`); Messages → `/messages` (`tile-sky`, `fa-comments`).
- **Admin drawer groups** (L1693–1892, `{% elif current_user.role ==
  'admin' %}`; L1493–1692 is the non-admin/faculty link lists):
  1. `Member Governance` (`fa-users-gear`): **All Members Directory** →
     `admin_view_users(role='all')`; **Pending Approvals Queue** →
     `admin_approve_requests` (`adm-row-urgent`, `ACTION` badge
     `adm-badge-urgent`); roster pills `adm-roster-pills`: Students →
     `role='student'` (`pill-student`, `fa-user-graduate`), Alumni →
     `role='alumni'` (`pill-alumni`, `fa-user-tie`), Faculty →
     `role='faculty'` (`pill-faculty`, `fa-chalkboard-user`).
  2. `Communications & Broadcast` (`fa-tower-broadcast`): Campus Community
     Group → `community_group`; WhatsApp Broadcast →
     `admin_whatsapp_broadcast`; Messaging Control →
     `admin_messaging_control`; Campus Announcements → `/announcements`;
     Direct Messages Inbox → `/messages` ("One-on-one administrator
     dialogues").
  3. `Operations, Audit & Security` (`fa-shield-halved`): Jobs &
     Internships Matrix → `admin_jobs`; Connection Monitor →
     `admin_connection_monitor`; Platform Analytics → `admin_analytics`;
     Registration Logs → `admin_registrations`; Event RSVPs →
     `/admin/events`; Incident Reports → `/admin/reports`; System
     Statistics → `/admin/stats`.
  4. `Admin Configuration` (`fa-sliders`): **Administrator Settings** →
     `edit_admin_profile(user_id=current_user.id)` (`fa-user-gear`);
     **Change Password** → `/change_password` (`fa-key`, "Console
     credentials & 2FA"); **View Public Portal** → `/` (`fa-globe`);
     **Sign Out** → `/logout` (`adm-row-danger`, `fa-power-off`,
     "Terminate admin session safely").
- Drawer footer (L1944–1952): admin gets only centred text `<i class="fas
  fa-shield-halved text-warning"></i> ENCRYPTED ADMIN SESSION • v2.4` —
  **no Logout button** here (non-admin roles get a full-width Logout
  button). PWA card `#pwaMobileDrawerCard` (`d-none`) follows for all roles.
- Admin-only JS (L2463–2482): polls `fetch('/api/admin/jobs/pending-count')`
  on load and every 60 s, writing into
  `document.getElementById('pendingJobsBadge')` — **no element with id
  `pendingJobsBadge` exists in `base.html`** (only this JS reference), so
  the badge update is a no-op in the base template.

### Design tokens (base.html)
- **Indigo (primary):** `base.html:796` `color: var(--primary-color,
  #4f46e5)`; `role-tag-admin` (L200–204, inline `<style>`): `background:
  rgba(99, 102, 241, 0.25); color: #a5b4fc; border: 1px solid rgba(99, 102,
  241, 0.45)` (indigo `#6366f1` family). Tile `tile-indigo` on the
  Dashboard mobile tile; `bullet-indigo` on Event RSVPs / System Statistics
  rows.
- **ADMIN badge / shield:** `admin-brand-tag`
  (`static/css/navbar-professional.css:1902`): `background: #0f172a`
  (obsidian slate), `color: #fbbf24` (amber gold), `border: 1px solid
  rgba(251,191,36,0.4)`, `font-size: 0.64rem`, `font-weight: 800`,
  `letter-spacing: 0.08em`; icons `fa-shield-alt` (brand tag, user pill
  tag, drawer role tag, System intro) and `fa-shield-halved` (System
  Control toggle, mobile avatar badge, drawer footer, Operations group
  head).
- **`admin-pulse-beacon`** (`navbar-professional.css:1878`): 10×10 dot,
  `background: #10b981`, `border: 2px solid #0f172a`, `box-shadow: 0 0 10px
  #10b981`, `animation: adminBeaconPulse 2s infinite` (scale 1→1.35,
  opacity 1→0.65), positioned `top:-2px; right:-2px` on the logo.
- **Drawer theme** (`navbar-professional.css:2587`):
  `.mobile-menu-overlay.admin-drawer-theme { background: linear-gradient(180deg,
  #070b14 0%, #0a0f1d 45%, #0c1222 100%); backdrop-filter: blur(28px);
  padding: 68px 12px 35px; }`; close button hover turns red
  (`rgba(239,68,68,0.25)`).
- **Profile-page palette** (`admin-luxury.css`, classes
  `admin-page-wrapper`, `admin-hero-card`, `text-holographic-adm` L223,
  `admin-btn-pill` L476, `admin-form-label` L422, `admin-input` L431):
  gradient `#0284c7 → #7c3aed → #38bdf8`; `theme-color` meta `#0284c7`
  (`base.html:24`).

---

## 18. Viva traps — known quirks and honest gaps (do not present as features)

1. **`/admin/stats` is fully hardcoded** — route passes no data; 1,250 /
   850 / 350 / 50 and both charts are static literals.
2. **`/admin/events` is a mock** — route passes no data; both event rows
   and the create-event modal are hardcoded/fake (`alert()` + reload,
   inputs have no `name` attributes, nothing is saved).
3. **"Live" is mostly branding.** Dashboard/Analytics/Stats are
   server-rendered on load. Only genuinely live client-side elements:
   dashboard clock + particle canvas + client-side directory engine;
   Connection Monitor Socket.IO feed; Messaging Control 15 s polling;
   Reports 12 s polling. Analytics period pills are cosmetic.
4. **Dead / unused backend values:** `stats.expired` (jobs),
   `stats.with_phone` (registrations), `pending_connections`
   (analytics), `events_data` (dashboard) are computed but never rendered;
   `get_role_counts` / `get_yearly_stats` / `get_admin_job_stats` exist
   but are unused — dashboard/analytics duplicate their logic inline.
   Reports `resolved_count` excludes `Closed` tickets.
5. **Field mismatches (likely rendering bugs):** Connection Monitor
   "Social Footprint" reads `sender_activity.connections_count` /
   `followers_count`, but `get_connection_activity()` only sets
   `last_login`/`online_status` there (counts live in
   `sender_stats.total_connections/total_followers`) — likely renders 0.
   Its profile modal reads `user.graduation_year` / `user.company`, but
   the API returns `passing_year` / `current_company` — likely "Not
   specified". Registrations template reads `reg.user_id`, but the query
   aliases it as `user_account_id`.
6. **Add vs Edit job mismatch:** add form lacks `skill_level`,
   `ctc_range`, `selection[]` inputs the route reads (they save as
   null/empty); edit form adds `skill_level` + `job_status`
   (Open/Closed/Expired). `job_status` is set to `'Open'` on add.
7. **State-changing GET:** `verify_user` approves/blocks via GET with no
   CSRF token; "block" actually hard-deletes the user. Its error branch
   references endpoint `admin_dashboard` (L2707), which does not exist
   (endpoint is `dashboard_admin`) — that path would raise a `BuildError`.
8. **Reports route side effect:** every page load permanently deletes
   tickets matching test/demo criteria (specific ticket numbers, `%test%`,
   `%example.com%`).
9. **WhatsApp send depends on pywhatkit** opening a real browser tab on
   the server (`sendwhatmsg_instantly`, `wait_time=15`); the broadcast
   "send" is a sequential 3.5 s/client-side loop, not a server queue.
10. **`base.html` admin JS references `#pendingJobsBadge`, which has no
    matching element in `base.html`** — the 60 s pending-count poll is a
    no-op there. `get_user_statistics` returns the same count for
    `total_connections`, `total_followers` and `total_following` (no
    separate followers table). `get_connection_activity` is N+1: 5 extra
    queries per record.
11. **Auth pattern:** no `abort(403)` in admin routes — enforcement is
    flash + redirect home, flash + redirect dashboard, or JSON 403.
    `edit_admin_profile` has a redundant double role check; any admin can
    view/edit any admin (no self-only restriction). Edit profile has no
    server-side email-uniqueness or phone-format check.

---

## Files read (for the record)

- `templates/admin/dashboard_admin.html` — 2,988 lines
- `templates/admin/admin_view_users.html` — 1,841 lines
- `templates/admin/connection_monitor.html` — 1,813 lines
- `templates/admin/jobs.html` — 1,591 lines
- `templates/admin/whatsapp_broadcast.html` — 1,160 lines
- `templates/admin/reports.html` — 1,095 lines
- `templates/admin/admin_analytics.html` — 1,060 lines
- `templates/admin/admin_messaging_control.html` — 673 lines
- `templates/admin/add_job.html` — 429 lines
- `templates/admin/edit_job.html` — 420 lines
- `templates/admin/edit_admin_profile.html` — 363 lines
- `templates/admin/admin_registrations.html` — 234 lines
- `templates/admin/admin_events.html` — 229 lines
- `templates/admin/admin_stats.html` — 206 lines
- `templates/admin/profile_admin.html` — 176 lines
- `services/admin_service.py` — 293 lines
- `templates/base.html` — 3,155 lines (admin nav / user pill / mobile drawer sections)
- `app.py` — 5,373 lines (all `/admin/*` and adjacent `/api/admin/*` routes read; full file not re-read line-by-line)

**Total admin template lines: 14,278.** With `admin_service.py` (293) and
the admin-relevant parts of `base.html`/`app.py`, the admin area covered
here is ~17,700+ lines of source read for this reference.
