# Alumni Hub — Alumni Area Reference (Redesign)

> Redesign of the Alumni role pages to admin-level quality. Source:
> `/home/hatch/workspace/alumni-hub-checkout` (GitHub main, commit `41e4ba9`
> before this work). **Local work only — nothing was pushed to GitHub.**
>
> Project: **Alumni Hub v1.0** (MCA Major Project) — Flask 2.3.2 + SQLite (WAL) +
> Flask-SocketIO + Scikit-Learn. Lead developer / backend: Rajender Mohan Verma.
> Live: https://alumni-hub-psi.vercel.app/ · Repo: https://github.com/RajenderMohanVerma/alumni-hub
>
> Companion file: `docs/admin-reference.md` — the admin design system this
> redesign is based on. Read that first for the admin pages, routes and the
> viva traps (§18 there).

## 0. What this redesign is — and is not

**Scope:** all 14 alumni templates (`templates/alumni/*.html`), 6,401 → 6,374
lines. No other file was changed: `app.py`, routes, services, models,
database code, `templates/base.html`, `templates/admin/*` and every other
role's templates are untouched. No new global CSS files were created and no
new backend dependencies were added.

**Goal:** make the Alumni role look and feel like the Admin role — same
dark-navy hero + glassmorphism system, same fonts and icon set — with the
Alumni amber theme as the accent, professional and clean, fully mobile
friendly, with subtle animation. All content, text, buttons, links, forms
and backend data are preserved exactly.

**Design tokens (shared across all 14 pages)**

| Token | Value | Notes |
|---|---|---|
| Alumni primary | `#f59e0b` / `#d97706` | Amber; replaces admin indigo `#4f46e5` |
| Amber gradient text | `#fde68a → #fbbf24 → #f59e0b → #d97706` | Page titles, replaces admin holographic `#38bdf8 → #818cf8 → #c084fc` |
| Hero gradient | `linear-gradient(135deg, #0b1329 0%, #172554 48%, #0f172a 100%)` | Same dark navy as admin |
| Fonts | Outfit / Plus Jakarta Sans / JetBrains Mono | Google Fonts, same as admin |
| Icons | Font Awesome | Same as admin |
| Shared CSS | `static/css/admin-luxury.css?v=2.4` | Loaded by every page, same as admin |
| Shell | `.admin-page-wrapper` → 3 ambient orbs → `.admin-container` → dark hero card | Same structure as admin pages |
| Cards | White, 18–28px radii, soft shadows | Hover lift `translateY(-5px)` |
| Glass | `rgba(255,255,255,0.05–0.08)` panels, `backdrop-filter: blur(10–16px)` | Hero chips, stat panels |
| Danger / success | `#ef4444` rose / `#10b981` emerald | Same as admin |

**Mobile rules (all pages):** layouts work at 360px — Bootstrap grids stack
to one column, no horizontal overflow (`overflow-x: clip/hidden` on the
wrapper), touch targets ≥44px (forms/buttons 44–48px), tables become stacked
cards, hero titles use `clamp()`. The `base.html` mobile drawer was not
touched and keeps working.

**Animation rules (all pages):** subtle reveal-on-scroll via
`IntersectionObserver` (opacity + small rise, staggered), hover lift on
cards/tiles, animated counters only where numbers already exist on the page,
pulsing live/badge dots. No heavy animation. Every page respects
`@media (prefers-reduced-motion: reduce)` — animations/transitions disabled
and revealed state forced.

**Features rule:** new features were added ONLY where they use data/routes
already passed to that template. No invented endpoints, no fake or hardcoded
data presented as live, no new backend dependencies.

## 1. Files changed

| File | Before | After | Routes that render it |
|---|---|---|---|
| `templates/alumni/dashboard.html` | 847 | 972 | `GET /alumni/dashboard` |
| `templates/alumni/edit_profile.html` | 1,682 | 1,037 | `/alumni/profile/<id>/edit` (GET, POST) |
| `templates/alumni/events.html` | 1,450 | 541 | `GET /alumni/events` |
| `templates/alumni/jobs.html` | 165 | 351 | `GET /alumni/jobs` |
| `templates/alumni/meet_register.html` | 264 | 374 | `/alumni/meet/register` |
| `templates/alumni/meet_view.html` | 144 | 255 | `/alumni/meet/view` |
| `templates/alumni/mentorship.html` | 184 | 315 | `GET /alumni/mentorship` |
| `templates/alumni/network.html` | 181 | 348 | `GET /alumni/network` |
| `templates/alumni/notifications.html` | 105 | 278 | `GET /alumni/notifications` |
| `templates/alumni/post_job.html` | 204 | 344 | `/alumni/post-job` (GET, POST) |
| `templates/alumni/profile.html` | 758 | 670 | `GET /alumni/profile/<id>` |
| `templates/alumni/settings.html` | 192 | 381 | `GET /alumni/settings` |
| `templates/alumni/spotlight.html` | 119 | 217 | `GET /alumni/spotlight` |
| `templates/alumni/upgrade.html` | 106 | 291 | (student → alumni verification form) |
| **Total** | **6,401** | **6,374** | |

Line counts fell on the biggest files because the old pages carried 1,000+
lines of heavy inline CSS/effects (mesh balls, floating particles, 3D tilt,
magnetic buttons, shine/holographic animations) that were replaced by the
shared `admin-luxury.css` + one tight page-local stylesheet. Content was not
cut — see §3.

Alumni routes in `app.py` (unchanged): `/alumni/dashboard`,
`/alumni/profile/<id>`, `/alumni/profile/<id>/edit`, `/alumni/network`,
`/alumni/messages`, `/alumni/mentorship`, `/alumni/post-job`, `/alumni/jobs`,
`/alumni/spotlight`, `/alumni/events`, `/alumni/notifications`,
`/alumni/settings`, `/alumni/meet/register`, `/alumni/meet/view`.

## 2. Per-page notes

### 2.1 dashboard.html — 847 → 972
- **Look:** admin shell, dark-navy hero, "ALUMNI HUB • LIVE" badge with
  pulsing amber dot, time-of-day greeting pill, "Welcome back,
  `{{ current_user.name }}`!", amber-gradient Post a Job button + glass My
  Network button, glass Profile Strength panel (same ids), floating avatar
  with amber ring + "Alumni" tag.
- **Sections:** 3 stat cards with top accent strips (Active Connections 0,
  Pending Requests `{{ pending_count }}`, Success Mentorships 5+);
  connection-request cards (amber ring avatars, amber role badges, amber
  Accept / soft-red Decline); dark-navy-with-amber "Guiding Star" mentorship
  banner; Quick Actions sidebar as bordered tiles with chevrons; "Students
  You May Know" recommendation cards; Mega Alumni Reunion 2025 spotlight
  (same image, date, venue, buttons).
- **Added:** animated counters reading already-rendered numbers via
  `data-count`/`data-suffix`; `{% block title %}` ("Alumni Dashboard •
  Alumni Hub").
- **Mobile:** hero centres, buttons full-width ≤576px, stat cards stack,
  request-card actions stretch full-width, avatar scales via
  `min(200px, 62vw)`, spotlight image `min-height: 220px`.
- **Preserved:** `post_job`, `alumni_network`, `edit_alumni_profile` ×2,
  `alumni_meet_register` ×2, `change_password`, `logout`,
  `alumni_meet_view`, `pending_count`/`pending_requests` loop,
  `recommendations` loop (`rec.source/score/reason/branch/skills/id/role`),
  completeness JS with the full `alumni` dict, `handleConnection` (POST
  `/api/connection-request/<action>/<senderId>`), `connectUser`,
  `showToast`, Socket.IO `job_approval_update` listener. All copy verbatim,
  including hardcoded "0", "5+", "January 15, 2025", "University Grand Hall".
- **Known tiny change:** the old greeting badge wrapper id
  `timeGreetingBadge` was dropped — nothing in JS or CSS referenced it (the
  JS uses `dynamicGreeting`, which is preserved and still wired). The only
  other occurrence of that id in the repo is in
  `templates/student/dashboard.html`, which was not touched.

### 2.2 profile.html — 758 → 670
- **Look:** dark-navy hero with amber "ALUMNI ELITE" badge, amber-gradient
  name, "Batch of `{{ profile['pass_year'] }}` |
  `{{ profile['department'] }}`", glass batch chip, preserved animated wave
  divider. Identity card: avatar with conic amber ring + green online dot,
  "Professional Alumni" amber tag, Year/Exp mini-stats, amber Company /
  emerald Role strips, amber Enhance Profile button (own profile) or green
  pulsing Send Request + WhatsApp Bridge / Professional Mail / Gmail Compose
  / LinkedIn buttons (other profiles). Bio card with amber top border,
  Academic Roots (amber icon) / Industry Pulse (emerald icon) cards, amber
  experience progress bar, amber-left-border achievement rows with medal
  rings.
- **Added:** animated counters on Year/Exp mini-stats (already-rendered
  numbers); `{% block title %}` (`{{ user['name'] }} • Alumni Profile`).
- **Mobile:** hero centres, buttons full-width ≤576px, avatar scales,
  `overflow-x: clip`.
- **Preserved:** all `user[...]`/`profile[...]` fields, `user.name |
  initials` avatar fallback (verbatim `onerror`),
  `achievements.split('|')` loop, experience-bar width expression,
  `edit_alumni_profile` / `whatsapp_bridge` / `compose_email` + Gmail link,
  `sendExtremeConnection` / `showExtremeToast`, VanillaTilt init,
  IntersectionObserver. Also fixed a stray extra `</div>` the original had
  before its `<style>` block.

### 2.3 edit_profile.html — 1,682 → 1,037 (profile editing — most critical)
- **Look:** admin shell, dark-navy hero, amber-gradient "Edit Your
  **Profile**" title, JetBrains Mono badge "ALUMNI PROFILE · EDIT MODE",
  amber section chips (Photo / Personal / Career / Achievements). Form
  sections are white cards (24px radii, hover lift, amber border on hover)
  with numbered step chips and amber icon tiles: **01 Profile Photo, 02
  Personal Information, 03 Professional Details, 04 Achievements & Social
  Links**. Same headings, subtitles, guidelines, tips, placeholders and
  button text. Inputs are light (`#f8fafc`, `#e2e8f0` borders) with amber
  focus ring + animated amber underline; labels now have matching `for=`
  attributes.
- **Sidebar (unchanged in purpose):** Live Preview card (dark-navy banner
  with amber rule, amber initial-letter avatar, same stats/bio) + Quick Tips
  (same 3 tips). "View Full Profile" was a dead `<button>`; it is now a real
  link to the existing `alumni_profile` route.
- **Added (existing data only):** profile-completeness indicator — hero glass
  stat box (%, amber progress bar, "N of 10 fields complete") + sidebar
  checklist (photo, name, phone, company, job title, location, experience,
  bio, LinkedIn, achievements), computed live in JS purely from the 10 fields
  already on the page. Mobile sticky save bar (`d-xl-none`, inside the form):
  Cancel + Save, sticky to the viewport bottom.
- **Small JS fixes:** `handlePhotoUpload` now actually shows the uploaded
  preview (the old code set `style.display='block'` but left Bootstrap's
  `d-none` class on, so first-time uploads stayed invisible) and syncs the
  preview-card avatar/initial; `removePhoto` also resets the preview avatar
  to the initial-letter state; double-submit guard (disables submit buttons,
  "Saving…" — only after native validation passes, on the form `submit`
  event). Photo overlay shows only when no photo is present; upload circle
  and drag-drop zone are keyboard-accessible (Enter/Space).
- **Mobile:** `col-md-6` sections stack to one column, photo upload grid
  collapses, hero title `clamp()`, card padding shrinks ≤767px, header wraps
  ≤480px, checklist 2-col → 1-col, all inputs/buttons ≥48px, sticky save bar
  full-width. No horizontal overflow; long names/bios use `word-break:
  break-word` in the preview.
- **Preserved — verified field by field:** `<form id="editForm"
  method="POST" enctype="multipart/form-data">`, no action (same URL),
  submit "Save Changes" + Cancel link. All 10 `name=` attributes identical
  before/after (sorted-list diff): `profile_pic`, `name`, `phone`,
  `company_name`, `designation`, `work_location`, `experience_years`, `bio`,
  `linkedin_url`, `achievements`. Avatar upload: same input
  `name="profile_pic"`, `accept="image/*"`,
  `onchange="handlePhotoUpload(this)"`; same 5MB + image-type validation,
  FileReader preview, drag-and-drop, `removePhoto()`,
  `{% set has_custom_pic ... %}` logic, `uploadPreview` `onerror` handler,
  `svgPlaceholder` (`url_for('static',
  filename='images/camera_pic.svg')`), progress-ring SVG. All
  `user[...]`/`profile[...]` values, `required` flags, `min="0"`,
  placeholders, preview avatar `{% if %}/{% else %}` branches (including
  `{{ (user['name']|trim)[0]|upper if user['name'] else 'A' }}`) intact. JS
  functions kept: `updatePreview()` (now also updates avatar initial +
  completeness), `handlePhotoUpload(input)`, `removePhoto()`, drag-and-drop,
  focus handlers, reveal observer. (Duplicate ids `previewImg`/
  `previewInitial` exist in the mutually exclusive `{% if %}/{% else %}`
  branches — exactly as in the original.)

### 2.4 events.html — 1,450 → 541
- **Look:** dark-navy hero with dot texture, badge "CONNECT & GROW",
  amber-gradient "Events" title, same subtitle, 4 glass stat cards (25 Events
  This Year / 650 Participants / 7 Upcoming / 98% Success Rate) with animated
  counters. Old heavy effects (mesh balls, particles, 3D tilt, magnetic
  buttons, shine/holographic animations) removed, replaced by reveal-on-scroll
  + hover lift + counters.
- **Preserved — all 8 event cards verbatim:** Itrang'26 (Live Now, 27–28 FEB,
  Main Campus, disabled Live Event button + Join Itrang →
  `https://itrangadmin.vercel.app/`, `/static/images/itrang.jpeg` header),
  Sparda'26 (Completed, 28–29 JAN, disabled Event Closed), AI in 2026 webinar
  (15 MAR, Register → `/register`), Resume Building Masterclass (22 MAR,
  RSVP), Annual Alumni Meet 2026 (10 APR, Get Tickets), Tech Founders Meetup
  (18 APR, Join Now), Spring Career Fair 2026 (25 APR, Register), Alumni
  Hackathon 2026 (05 MAY, Sign Up) — titles, dates, times, descriptions,
  locations, seat counts, badges, button labels/disabled states intact.
  Filter tabs (All/Webinars/Workshops/Social/Networking) with the same
  `data-filter`/`data-category` client-side filtering. CTA "Don't Miss Out!"
  with Join Alumni Hub (`/register`) and Get Notifications (`#`) preserved.
  Note: this file had **zero** Jinja variables in the original (confirmed by
  grep) — all content is hardcoded, and it stays that way.
- **Added (existing DOM data only):** "Showing X of 8 events" count line + a
  "No events in this category yet" empty state, both driven by the filter JS
  over already-loaded cards.
- **Bug fixed:** the old script looked for a non-existent
  `[data-target="6"]` counter; the Upcoming counter is now computed from the
  actual DOM cards (total minus `.event-completed` = 7) before animating. The
  25/650/98 hero stats are pre-existing hardcoded presentation figures — kept
  unchanged, not presented as live backend data.

### 2.5 jobs.html — 165 → 351
- **Look:** dark-navy hero, "ALUMNI CAREER OPPORTUNITIES" badge,
  amber-gradient title, Post a Job Opening button (`url_for('post_job')`).
- **Preserved:** search input (`jobSearchInput`), type select
  (`jobTypeFilter`), Filter/Reset buttons — same IDs and options
  (Full-Time/Internship/Contract/Remote). Every job row: `{% for job in jobs
  %}` loop, company avatar with `company_logo` img fallback to first letter
  of company, `job.title`, employment-type badge (`or 'Full-Time'`),
  company/location (`or 'Remote'`)/salary (`or 'Competitive'`), conditional
  deadline (`{% if job.deadline %}` → "Closes: …"), Apply link with the exact
  `://` / `mailto:` conditional, `target="_blank"`. Empty state ("No Active
  Openings Found" + Post an Opening) preserved.
- **Added (existing `jobs` data only):** hero summary chips — Total /
  Full-Time / Internships — computed in Jinja with a `namespace` counter loop
  over `jobs`; quick type chips (All/Full-Time/Internship/Contract/Remote)
  driving the existing client-side filter; a live "Showing X of N
  opportunities" label and a "No openings match your filters" state with Clear
  Filters, shown only when filtering hides all loaded rows.

### 2.6 post_job.html — 204 → 344
- **Look:** dark-navy hero ("RECRUITER & ALUMNI PORTAL", Back to Jobs →
  `url_for('list_jobs')`). Form card with amber top accent and icon-headed
  sections (Role & Company / Work Mode & Eligibility / Compensation &
  Application / Requirements & Description).
- **Preserved — form exactly:** `method="POST"`,
  `enctype="multipart/form-data"`, `id="jobPostForm"`, all 13 fields with
  identical names, types, options, placeholders and `required` flags:
  `title`, `company`, `category` (Technology/Finance/Design/Marketing/Other),
  `employment_type` (Full-Time/Internship/Contract/Part-time), `work_mode`
  (Remote/Onsite/Hybrid), `eligible_branch`, `experience_required`
  (Freshers/0-1/1-3/3+ Years), `location`, `salary`, `deadline` (date),
  `apply_link` (required), `skills`, `description` (textarea, 4 rows).
  Submit button "Publish Job Opportunity" unchanged. Live preview card
  preserved with the same `updatePreview()` JS (same input IDs `in_*` /
  preview IDs `prev_*`, same default values), now amber-styled and sticky on
  large screens, plus a small note that postings are reviewed before going
  live (matches the admin approve/reject job flow).

### 2.7 network.html — 181 → 348
- **Look:** admin shell, dark-navy hero, Messages button
  (`url_for('messages')` kept); search/filter card (all 4 controls + Filter
  button preserved, batch/city selects given `value` attributes); stats grid
  (480+ / 210 / 180+ / 32, text unchanged) with count-up animation on scroll.
- **Preserved:** 8 member cards — the `{% set alumni_members %}` list is
  identical apart from indentation, all `{{ member.* }}` fields,
  `{{ member.accent }}` class, Connect/View Profile alerts and pagination.
  Avatars now amber-gradient circles.
- **Added (existing data only):** client-side directory filter (search text +
  batch year + city, live on input/change) over the already-loaded cards,
  with a "Showing N alumni" count and a no-results empty state.

### 2.8 mentorship.html — 184 → 315
- **Look:** admin shell, dark-navy hero, Offer Mentorship alert button;
  search/filter card preserved; all 3 mentor cards verbatim (names, roles,
  batches, bios, skill chips, availability badges, Connect alerts). Avatars
  keep their original per-mentor gradients; skill chips restyled amber.
- **Added (existing data only):** client-side filter (keyword search over
  card text + domain select mapped to each card's skills) with "Showing N
  mentors" count and empty state.

### 2.9 spotlight.html — 119 → 217
- **Look:** centred dark-navy hero (same heading/subtitle); featured Anjali
  Gupta story and all 3 story cards preserved exactly (images, Unsplash URLs,
  alt text, badges, copy, Read Story alerts). Cards get image zoom-on-hover
  and lift. No new features — nothing new to derive from.

### 2.10 meet_register.html — 264 → 374
- **Look:** form restyled as numbered step sections (1 Personal, 2 Academic,
  3 Professional/Higher Studies, 4 Giving Back) with amber step chips, amber
  focus rings and checked radio/checkbox colours, 46–48px touch targets.
- **Preserved — form untouched in behaviour:** `method="POST"`,
  `id="alumniMeetForm"`, no action (as before); every field
  name/id/value/option/`required`/`min`/`max`/`checked` preserved, including
  `current_user.name`, `current_user.phone or ''`, `current_user.email`
  pre-fills, `onchange="toggleSections()"` /
  `onchange="toggleContributions()"`, and both toggle functions verbatim;
  Cancel still `url_for('dashboard_alumni')`. Added a `{% block title %}`
  (new, no content removed).

### 2.11 meet_view.html — 144 → 255
- **Look:** hero with Edit Registration (`url_for('alumni_meet_register')`)
  and Dashboard (`url_for('dashboard_alumni')`) buttons; confirmed-status
  banner; detail rows stack to one column on mobile, email gets `text-break`.
- **Preserved:** all `{{ registration[...] }}` fields including the
  `{% if registration['company_name'] %}` conditional professional section
  and the attending badge.
- **Added:** client-side "Print Pass" button (`window.print()`) with a print
  stylesheet that hides nav chrome/orbs; also a `{% block title %}`.

### 2.12 notifications.html — 105 → 278
- **Look:** admin shell (`.admin-page-wrapper` + 3 ambient orbs +
  `.admin-container`, `admin-luxury.css?v=2.4` loaded inside the content block
  exactly as admin pages do). Dark-navy hero with amber pulsing "Alumni
  Updates" badge and amber-gradient title. White 20px-radius cards, hover
  lift.
- **Layout:** hero holds Refresh + Mark All Read; below, 8-col feed (empty
  state "All Caught Up!" with amber bell-slash chip + "Post a Job Opening"
  amber-gradient button) beside a 4-col Preferences card with 4 toggle rows
  (amber switches, hover border highlight).
- **Mobile:** hero stacks, buttons wrap, `clamp()` hero title, rows stack;
  all buttons min-height 44px.
- **Features added:** none — the template receives no notification list from
  the backend, so there was no existing data to build an unread-count summary
  from; inventing one would have been fake data.
- **Preserved:** `url_for('list_jobs')`, Refresh `location.reload()`, Mark All
  Read button, all 4 toggles (`emailNotif`, `eventNotif`, `messageNotif`,
  `jobNotif`, all checked), all labels/subtexts, Save Preferences
  `alert('Alumni notification preferences updated!')`, all header copy.

### 2.13 settings.html — 192 → 381
- **Look:** same admin shell/hero treatment; amber-gradient "Alumni
  Settings" title; amber pulsing "Account & Experience" badge. Amber-gradient
  active pill in the settings nav (other pills hover amber-subtle); amber
  focus rings on inputs/selects; amber toggle switches; section icon chips
  (amber/green/purple per tab).
- **Layout:** unchanged structure — 3-col pill nav + 9-col content card, all
  4 tabs (Profile Info / Security / Notifications / Privacy) with identical
  headings, subtexts, and forms.
- **Mobile:** below 992px the vertical pill nav becomes a horizontal
  scrollable strip (no wrap, hidden scrollbar, 44px targets) so it never
  overflows at 360px; form fields stack via existing Bootstrap grid; buttons
  min-height 44px.
- **Features added:** none (no new backend data available).
- **Preserved:** title block, all tab button ids
  (`v-pills-profile-tab`, `-account-tab`, `-notifications-tab`,
  `-privacy-tab`) with `data-bs-toggle="pill"`/`data-bs-target`/roles, all 3
  forms with identical `onsubmit` alert handlers (`Profile information
  saved!` / `Password updated successfully!` / `Privacy settings saved!`),
  `{{ current_user.name }}` and `{{ current_user.email }}` (disabled), bio
  textarea text, all 3 password inputs, toggles `emailNotifAlumni`/
  `msgNotifAlumni` (checked), `showEmailAlumni` (checked)/`showPhoneAlumni`
  (unchecked), visibility `<select>` with all 3 options ("Community…"
  selected), `alert('Preferences saved successfully!')` button.

### 2.14 upgrade.html — 106 → 291
- **Look:** same admin shell; centred dark-navy hero with amber-gradient
  "Verified Alumni Status" title and pulsing "Graduation Milestone" badge.
  Single white 24px-radius card holding the form; inner sections as subtle
  panels with amber hover borders; numbered amber step chips (1/2) on the two
  form sections; amber-gradient submit button (48px), amber-hover cancel
  button.
- **Layout:** same form order — Verified Academic Record → Professional &
  Career Details → Alumni Privileges (green panel, unchanged) →
  submit/cancel.
- **Mobile:** buttons stack full-width (`flex-column flex-sm-row`),
  `clamp()` title, grids stack; 44–48px touch targets.
- **Features added:** one purely presentational 3-step strip in the hero
  ("1 · Verify Record / 2 · Career Details / 3 · Alumni Privileges") — it
  only labels the three sections already in the form; no new data, pricing,
  plans, or payment flow invented.
- **Preserved:** title block, `method="POST"` + `needs-validation` form, all
  four disabled record fields (`{{ profile['enrollment_no'] }}`,
  `{{ profile['department'] }}`, `{{ profile['degree'] }}`,
  `{{ profile['cgpa'] or 'N/A' }}`), all three inputs with exact
  `id`/`name`/`min`/`max`/`required`/placeholders (`pass_year`,
  `company_name`, `designation`), info note, all 4 privilege items, submit
  "Complete Alumni Verification", cancel link
  `url_for('dashboard_student')`.

## 3. What was preserved (verification)

- **Jinja/template syntax:** `python3 scripts/validate_templates.py` →
  **Total errors: 0** (all templates in the repo, including all 14 alumni
  pages, `[OK]`). Note: the validator needs Jinja2 installed; if
  `ModuleNotFoundError: No module named 'jinja2'` appears, install it
  user-local (`pip install --user jinja2`) and re-run — no repo files are
  affected by that.
- **Token set-diff (coordinator check):** for each of the 14 files, the
  multiset of `{{ ... }}` expressions, `{% ... %}` blocks, `url_for(...)`
  calls, `name="..."` attributes and `id="..."` attributes in the new file
  was compared against `HEAD`. Result: **nothing lost in 13 of 14 files**
  (only additions). The single exception is dashboard.html, where the dead
  wrapper id `timeGreetingBadge` was dropped — verified unreferenced by any
  JS/CSS (see §2.1).
- **Spot checks (coordinator):** all 8 events.html titles + Itrang URL/image
  present; edit_profile `name=` list identical before/after (sorted diff);
  all 13 post_job field names present; dashboard `pending_count`,
  `handleConnection`, `job_approval_update`, `completenessPercent`,
  `recommendations` present; meet_register `name=` list identical.
- **Scope check:** `git status` / `git diff --stat` show ONLY the 14
  `templates/alumni/*.html` files modified (4,659 insertions, 4,698
  deletions) plus this file, `docs/alumni-reference.md`. `app.py`,
  `templates/base.html`, `templates/admin/*`, services, models and all other
  templates are untouched. Nothing was pushed to GitHub.

## 4. How to test each page (after deploy / locally with Flask)

Prerequisite: run the app locally (`python app.py` or the project's normal
start command) and log in as an Alumni user. Check each page at desktop width
and at 360px (DevTools device toolbar). Things to verify per page:

| Page | URL | Check |
|---|---|---|
| Dashboard | `/alumni/dashboard` | Greeting + name, Profile Strength bar animates, pending count matches, Accept/Decline on a request works, Post a Job / My Network links work, no horizontal scroll at 360px |
| Profile (own) | `/alumni/profile/<own id>` | Avatar, batch/department, bio, achievements list, Enhance Profile button goes to edit page |
| Profile (other) | `/alumni/profile/<other id>` | Send Request / WhatsApp / Mail buttons present, no edit button |
| Edit Profile | `/alumni/profile/<id>/edit` | **Most important:** upload a photo — preview must appear (old bug fixed, §2.3); change a field, Save — value must persist after reload; completeness % updates as fields fill; sticky save bar appears on mobile; Cancel returns to profile |
| Events | `/alumni/events` | All 8 event cards, Itrang Join link opens `itrangadmin.vercel.app`, filter tabs filter the cards, "Showing X of 8" updates |
| Jobs | `/alumni/jobs` | Job rows from the DB render, search + type filter work, Apply link opens `://` or `mailto:` correctly, Post a Job Opening button works |
| Post a Job | `/alumni/post-job` | Fill all 13 fields, live preview updates, submit → job goes to admin approval (pending), then appears in Jobs only after admin approves |
| Network | `/alumni/network` | 8 member cards, search/batch/city filter narrows them, "Showing N alumni" updates, Messages button works |
| Mentorship | `/alumni/mentorship` | 3 mentor cards, keyword/domain filter works, Connect alerts work |
| Spotlight | `/alumni/spotlight` | Featured story + 3 story cards, images load, Read Story alerts work |
| Meet Register | `/alumni/meet/register` | Pre-filled name/phone/email, step sections toggle correctly (Professional vs Higher Studies, Giving Back), submit saves, Cancel → dashboard |
| Meet View | `/alumni/meet/view` | Registration details render, Edit Registration + Dashboard buttons work, Print Pass opens print dialog |
| Notifications | `/alumni/notifications` | Empty state shows, all 4 preference toggles flip, Save Preferences shows the alert, Refresh reloads |
| Settings | `/alumni/settings` | All 4 tabs switch, pill nav scrolls horizontally on mobile, the 3 forms show their alerts on submit, disabled name/email show current user |
| Upgrade | `/alumni/upgrade` | Disabled record fields show the student's data, pass_year/company/designation validate (year range), submit completes verification, Cancel → student dashboard |

**Global checks on every page:** no horizontal scrollbar at 360px; buttons
≥44px; hero and cards reveal on scroll; with "Reduce motion" enabled in the
OS/browser, animations are off and content is fully visible; no console
errors; the base.html mobile drawer opens and all nav links work.

## 5. Known limitations / viva notes

- **Events page stats are presentation figures, not live data** (25 Events /
  650 Participants / 98% Success Rate were already hardcoded before this
  redesign; the Upcoming count is now computed from the rendered cards). Do
  not claim them as live backend metrics in the viva — same caution as the
  admin `/admin/stats` and `/admin/events` traps in `docs/admin-reference.md`
  §18.
- **Notifications page has no backend list yet** — the feed shows the
  "All Caught Up!" empty state by design; the preferences toggles are
  client-side alerts, not saved settings (same as before the redesign).
- **Network / Mentorship member data is template-side** (`{% set
  alumni_members %}` / hardcoded mentor cards) — the new client-side filters
  only search what is already rendered; they are not a backend search.
- **Settings forms use `onsubmit` alerts** (pre-existing behaviour) — they do
  not actually save to the backend. If asked in the viva, say so honestly;
  wiring them to real endpoints is a Phase 6 item.
- **No backend was changed**, so every route, permission check and data flow
  behaves exactly as before. The redesign is presentation-only.

## 6. Alumni navbar / header redesign (2026-11-16, local — not pushed)

Desktop navbar + mobile drawer for the Alumni role rebuilt to the Admin
standard, in the shared shell `templates/base.html` (3,155 lines) and
`static/css/navbar-professional.css`. No alumni page template, route,
service or backend file was touched.

### 6.1 Files changed

| File | Change |
|---|---|
| `templates/base.html` | Alumni desktop nav, brand, toggler, user pill, mobile drawer (see below) |
| `static/css/navbar-professional.css` | +258 lines appended at end — alumni desktop CSS only |
| `docs/alumni-reference.md` | This section (§6) |

### 6.2 Desktop navbar (alumni)

- Pill buttons now use new `.nav-alumni-btn` (mirrors `.nav-admin-btn`):
  amber-tinted pill `#fffbeb` / border `#fde68a`, hover amber `#fef3c7`,
  active = amber gradient `#f59e0b → #d97706` with white text. Same
  1200–1400px / 992–1199px responsive sizing rules as the admin buttons.
- **Connect** dropdown (was plain text items): intro header
  "Connect & Mentor — Network, Guidance & Stories" + rich rows (icon tile +
  title + subtitle + chevron) for Alumni & Students, Mentorship Hub,
  Alumni Spotlight. **Career** dropdown (renamed from "Opportunities",
  same links): intro "Career & Events — Jobs, Referrals & Reunions" +
  Browse Jobs, Post Job / Referral, Alumni Events. Dropdown menus reuse
  the admin `.nav-admin-dropdown-menu` structure with alumni-scoped
  amber overrides (`.nav-alumni-dropdown-menu`, `.nav-alumni-menu-item`).
- Active states added where they were missing: Connect toggle is active
  on `alumni_network` / `alumni_mentorship` / `alumni_spotlight`, Career
  toggle on `alumni_jobs` / `alumni_post_job` / `alumni_events`,
  Messages on `messages` (same check as admin), Notifications on
  `alumni_notifications`. Dashboard active check unchanged.
- All 9 desktop links and hrefs unchanged:
  `/alumni/dashboard`, `/messages`, `/alumni/network`, `/alumni/mentorship`,
  `/alumni/spotlight`, `/alumni/jobs`, `/alumni/post-job`, `/alumni/events`,
  `/alumni/notifications`. Dropdown ids `alumniConnectDropdown` /
  `opportunitiesDropdown` unchanged.
- **Brand:** new `.alumni-brand-wrap` — brand now links to
  `/alumni/dashboard` for alumni (was `/`), with an amber ALUMNI tag
  (`fa-user-tie`) and an amber pulse beacon, mirroring
  `.admin-brand-wrap` / `.admin-brand-tag` / `.admin-pulse-beacon`.
  Admin and faculty brand branches are byte-identical.
- **Hamburger toggler:** new `.alumni-custom-toggler` (amber border/hover),
  mirroring `.admin-custom-toggler`. Same button, same
  `id="navbarToggler"`, `aria-controls="mobileMenuOverlay"`,
  `aria-expanded` handling — no JS change.
- **User pill:** new `.alumni-user-pill` (white pill, amber `#d97706`
  border, amber avatar ring) + ALUMNI role tag next to the name, mirroring
  `.admin-user-pill` / `.admin-user-pill-tag`. The pill dropdown menu
  itself is unchanged (My Profile, Messages, Settings, Change Password,
  Logout).

### 6.3 Mobile drawer (alumni)

- Overlay now gets `.alumni-drawer-theme` (dark amber-navy gradient,
  amber topbar / close button / group boxes), mirroring
  `.faculty-drawer-theme`. Topbar shows the amber ALUMNI role tag
  (`.role-tag-alumni`).
- New **alumni mobile profile card** (`.alumni-mobile-card`, amber
  gradient) replacing the generic grey card for alumni: "ALUMNI PORTAL"
  status pill with pulse, "ALUMNI MEMBER" badge, avatar with `fa-user-tie`
  badge, name + email, and 4 quick tiles — Dashboard, Network, Post Job,
  Messages — all existing routes, all with `adm-drawer-link` so the
  drawer auto-closes on tap (same JS hook as admin/faculty).
- The old flat list of 9 plain `mobile-nav-link` rows is replaced by 4
  grouped sections using the admin `.adm-drawer-group` /
  `.adm-drawer-group-box` / `.adm-drawer-row` pattern (icon bullet + title
  + subtitle + chevron, amber accents):
  - **Alumni Home** — Dashboard, Messages
  - **Connect & Mentor** — Alumni Network, Mentorship Hub, Alumni
    Spotlight, Community Group
  - **Career & Events** — Browse Jobs, Post Job / Referral, Alumni Events
  - **Account** — Notifications, My Profile
    (`url_for('alumni_profile')`), Settings
    (`url_for('alumni_settings')`), Sign Out (`/logout`, danger row)
- Every pre-existing mobile alumni link is preserved (all 9 nav links +
  Community Group + Profile from the old quick actions). Only additions
  are links to routes that already exist: My Profile, Settings, Logout.
  Home / About / Events at the top of the drawer were initially left as
  white cards — see §6.7, which rebuilt them as dark Explore rows.
- No JS was changed: open/close uses the existing `#navbarToggler` /
  `#mobileMenuOverlay` / `#closeMobileMenu` handlers, Escape key, and the
  `.mobile-nav-link, .adm-drawer-link` auto-close listener.

### 6.4 Mobile & accessibility

- Rows are min 48px tall, quick tiles min 64px; drawer stacks to one
  column at 360px with no horizontal overflow; subtitles truncate with
  ellipsis (same as admin rows).
- `aria-expanded` / `aria-label` / `aria-controls` untouched; focus
  behaviour unchanged (Escape closes and refocuses the toggler).
- Pulse/beacon animations are disabled under
  `prefers-reduced-motion: reduce`.

### 6.5 What was preserved (verification)

- `python3 scripts/validate_templates.py` → **Total errors: 0**.
- Jinja2 parse of `base.html` OK; full render test with mocked
  `current_user`/`request`/`url_for` for alumni (`dashboard_alumni`,
  `alumni_network`) and admin (`dashboard_admin`) — all alumni navbar
  and drawer elements render, dashboard active state works, brand href
  is `/dashboard_alumni`, and neither role's render leaks the other's
  drawer/card/theme classes in markup.
- `git diff --stat`: only `templates/base.html` and
  `static/css/navbar-professional.css` changed. The CSS diff is purely
  appended lines at the end of the file; the `base.html` diff hunks are
  confined to the alumni style block, brand, toggler, alumni desktop nav,
  user pill, drawer overlay/topbar, alumni mobile card and alumni mobile
  links. The only shared line touched is the brand anchor (admin/faculty
  branches inside it are byte-identical). No `+/-` diff line references
  any admin/faculty/student endpoint (`dashboard_admin`,
  `dashboard_faculty`, `dashboard_student`, `admin_view_users`, …).
- Removed dead CSS: the old `.nav-alumni-link` compact styles (no longer
  used anywhere — verified by repo-wide grep).
- **Note:** no notification count badge was added — there is no existing
  unread-count variable for alumni, and no count was invented.

### 6.6 How to test (after deploy / locally with Flask)

- Log in as an alumni user on desktop: brand links to
  `/alumni/dashboard`, ALUMNI tag + amber beacon visible, pill nav with
  amber active state, Connect/Career dropdowns open on hover (desktop)
  and click, with intro headers and chevron rows.
- At 360px: hamburger opens the amber drawer — profile card, 4 tiles,
  4 grouped sections; tap any row and the drawer closes; Escape closes
  it; no horizontal scrollbar.
- Log in as admin and faculty: navbar, brand, drawer and pills must look
  exactly as before (no alumni classes in their markup).

### 6.7 Alumni drawer white-card fix (2026-11-16, local — not pushed)

Bug seen on a real phone screenshot (21:24 IST): below the amber profile
card and 4 quick tiles, the alumni drawer showed two big **white** cards
— Home and About — plus a white Events card at the bottom, clashing with
the dark amber drawer. Cause: three places in `templates/base.html`
rendered the old white `.mobile-nav-link` cards for every non-admin /
non-faculty user, i.e. alumni included.

What was white, and what it is now (all in `templates/base.html` only):

- **Home (`/`) + About (`/about`)** — were white cards at the top of
  the drawer (gated by `role not in ['admin', 'faculty']`). The gate now
  also excludes `alumni`; the same two links render as dark rows in a
  new **Explore** group at the bottom of the drawer. Same hrefs, same
  `.adm-drawer-link` auto-close.
- **Events (`/events`)** — was a white card after the groups (gated by
  `role != 'admin'`). The gate now excludes alumni too; the link renders
  as a dark **Campus Events** row inside Explore ("All campus events &
  reunions"). Student and logged-out users still see the original white
  cards — their markup is untouched.
- **Dead alumni quick actions** — the `{% else %}` standard
  `.mobile-profile-card` still contained an alumni branch with grey
  `.action-btn` links. It was unreachable for alumni (alumni hits its
  own profile-card branch first), so only that dead alumni branch was
  removed; the student/faculty branches are untouched.
- **Duplicate Logout button** — the generic `btn-outline-danger` Logout
  button below the groups duplicated the Sign Out row already in the
  Account group. For alumni it is replaced by an amber session footer
  ("VERIFIED ALUMNI PORTAL • JIMS ROHINI"), mirroring the admin/faculty
  footer lines. Student keeps the Logout button.
- **Quick-tile icons** — the Network and Post Job tiles showed muddy
  dark squares behind their glyphs. Cause: global `.tile-sky` /
  `.tile-emerald .tile-icon` rules in
  `static/css/navbar-professional.css` paint a tinted 32px box behind
  any `.tile-icon` (Dashboard amber and Messages violet had no such
  rule, so they looked clean). Fixed with an alumni-scoped override
  (`.alumni-mobile-quick-grid .alumni-tile-btn .tile-icon` —
  transparent background, no box) in the inline alumni CSS. The Network
  tile glyph was also swapped `fa-network-wired` → `fa-users` (clean
  single glyph at small size); the grouped Alumni Network row keeps
  `fa-network-wired`.
- Audited the rest of the alumni drawer (topbar, profile card, tiles,
  all groups, PWA banner — already has an alumni dark override, session
  footer): no other white/light element renders for alumni.

Final drawer order: profile card → 4 quick tiles → Alumni Home →
Connect & Mentor → Career & Events → Account → **Explore** (Home,
About, Campus Events) → amber session footer.

Verification: `python3 scripts/validate_templates.py` → **Total errors:
0**. Jinja render test with mocked alumni/student/faculty/admin/
anonymous users (`/tmp/test_alumni_drawer.py`): rendered alumni drawer
contains **zero** `mobile-nav-link` and **zero** `action-btn`; Home /
About / Campus Events render as `adm-drawer-row` inside Explore; all 16
pre-existing alumni hrefs still present; student, faculty, admin and
anonymous drawer output is **byte-identical to HEAD**. No push — local
only.

### 6.8 Navbar ALUMNI badge removed (2026-11-16, local — not pushed)

Rajender's phone screenshot (21:41 IST) showed the amber **ALUMNI** role
tag next to ALUMNI HUB in the top navbar overflowing on mobile — white
text cut off behind the hamburger button. Fix: removed the
`<span class="alumni-brand-tag">…ALUMNI</span>` element from the navbar
brand in `templates/base.html` (2 lines deleted). The navbar now shows
only the logo + **ALUMNI HUB** name, as requested. The admin ADMIN tag is
untouched. The ALUMNI tags inside the mobile drawer (topbar role tag,
profile card ALUMNI MEMBER badge) were NOT removed — only the navbar one
was circled. Verification: `python3 scripts/validate_templates.py` →
**Total errors: 0**; `alumni-brand-tag` no longer occurs in `base.html`.
No push — local only.

## 7. Fixed-navbar overlap + dark-hero contrast fix (2026-11-16, local — not pushed)

Two live bugs from Rajender's phone screenshots (21:19 IST).

### 7.1 Root causes

- **Bug 1 — content hidden behind the fixed navbar.** `#mainNavbar` is
  `fixed-top`. Admin pages clear it with `.admin-page-wrapper`
  `padding-top` from `static/css/admin-luxury.css`
  (`--adm-top-spacing-desktop 145px / tablet 125px / mobile 98px /
  small 92px`). But 5 alumni pages never had that padding:
  `dashboard.html` + `profile.html` (`.alumni-page-wrapper`, inline CSS
  with no `padding-top`) and `events.html`, `jobs.html`, `post_job.html`
  (`.alumni-page`, only a `py-4` container). Their heroes started at the
  top of the page, so the navbar clipped the hero card / the
  "RECRUITER & ALUMNI PORTAL" pill / the title.
- **Bug 2 — dark-on-dark hero titles.** `static/css/theme-system.css`
  (loaded in `base.html`) sets `h1..h6 { color: var(--text-primary)
  !important; }` — dark navy — which beats every plain `color: #fff`
  rule in the alumni templates. Only the amber gradient spans survived
  (they use `background-clip: text` + `-webkit-text-fill-color:
  transparent`), so "Welcome back," / "Post a Job" rendered dark on the
  dark-navy hero while the amber part stayed readable. Admin heroes were
  already protected by the "bulletproof" block in `admin-luxury.css`
  (`.admin-hero-card h1 { color: #fff !important }`); alumni heroes
  using `.alu-hero-card` / `.alumni-hero` were not.

### 7.2 The shared fix (one place, alumni-scoped)

Appended to `static/css/navbar-professional.css` (loaded in `base.html`
on every page; grep confirms no non-alumni template uses these classes):

- **Clearance** — `.alumni-page-wrapper, .alumni-page` get exactly the
  admin values: `padding-top: 145px` desktop, `125px` ≤991.98px, `98px`
  ≤768px, `92px` ≤575.98px. Navbar is ~80px desktop / ~64–70px mobile,
  so these leave the same breathing room admin has. The 9 pages already
  on `.admin-page-wrapper` needed nothing. (Note: `meet_view.html` has a
  `padding-top: 0 !important` on `.admin-page-wrapper`, but it is inside
  `@media print` only — print-only, left alone.)
- **Contrast** — `.alu-hero-card h1/h2/h3/.alu-hero-title` and
  `.alumni-hero h1/h2/h3/.alumni-hero-title` get `color: #fff !important`
  + `-webkit-text-fill-color: #fff !important`, mirroring admin's
  bulletproof block. Gradient spans keep their transparent fill (a direct
  rule on the span beats the inherited value from the `h1`), exactly as
  admin's `.hero-title-gradient` does.

### 7.3 Per-page audit

| Page | Wrapper (clipped?) | Hero title | Change |
|---|---|---|---|
| dashboard.html | `.alumni-page-wrapper` — covered by shared fix | `.alu-hero-title` covered; **one extra spot**: "Be a Guiding Star" mentorship banner (`.alu-mentor-banner`, dark gradient) — its `h3` was forced dark by theme-system, its `<p class="lead opacity-75">` forced `#334155` | Scoped CSS in the template only: `.alu-mentor-banner h3/p { color:#fff !important }` (p keeps `opacity-75`, so it renders dimmed as intended) |
| profile.html | `.alumni-page-wrapper` — covered | Covered | None — `.alu-profile-content { margin-top:-90px }` only overlaps the hero's own wave padding, not the navbar |
| edit_profile.html | `.admin-page-wrapper` — already had admin padding | `.admin-hero-card` bulletproof + shared fix | None |
| events.html | `.alumni-page` — covered | `.alumni-hero h1` covered | None — `.alumni-lift { margin-top:-5.5rem }` only overlaps the hero's own bottom padding |
| jobs.html | `.alumni-page` — covered | Covered | None |
| post_job.html | `.alumni-page` — covered | Covered ("Post a Job" now white, "or Internship" amber) | None |
| network.html, mentorship.html, notifications.html, settings.html, spotlight.html, upgrade.html, meet_register.html, meet_view.html | `.admin-page-wrapper` — already had admin padding | All `h1`s inside `.admin-hero-card` — bulletproof white | None — systematic grep found every dark-colour instance on these pages lives on white/light cards, never inside a dark container |

Mobile 360px polish (static review, both groups): no real defects — no
fixed widths >360px, no long unbroken strings, hero buttons go full-width
≤576px, settings nav is a contained horizontal scroll strip, upgrade
pills wrap. No mobile changes made.

### 7.4 Verification

- `python3 scripts/validate_templates.py` → **Total errors: 0**.
- Jinja render tests with mocked alumni users: all 14 pages render;
  dashboard/post_job/profile (18/18 checks) and mentorship/
  notifications/upgrade/network/settings/spotlight/meet_register/
  meet_view all PASS — hero titles present, wrappers as expected, form
  fields and `url_for` routes intact.
- `git diff --stat`: only `static/css/navbar-professional.css` (+55,
  shared fix) and `templates/alumni/dashboard.html` (+15, banner fix).
  70 insertions, 0 deletions. No content, text, Jinja, `url_for`, form
  field or route changed. No push — local only.

## 8. Network page redesign (2026-11-16, local — not pushed)

### 8.1 Which file is actually live — important finding

Rajender's screenshot (21:51 IST) shows the **live** Network page as a
plain light page ("Student & Alumni Networks", INSTITUTIONAL DIRECTORY
pill, stats 1 / 4 / 1 / 1, "All Campus Network" / "My Connections Only
(1)" pills, Messages Hub). That is **not** `templates/alumni/network.html`
— that file was already redesigned (dark hero, amber cards, client-side
filter over 8 hardcoded demo members) and is never rendered for this URL:
`alumni_network()` (`app.py` ~2072) does `return redirect(url_for('network'))`,
and `network()` (`app.py` ~4577) renders **`templates/student/network.html`**
with real database rows. So the redesign was done on the file that actually
serves the page: `templates/student/network.html` (817 lines).
`templates/alumni/network.html` was left untouched. The page is shared by
student / alumni / faculty / admin (all hit the same `network()` route),
so the redesign stays role-neutral in copy ("Student & Alumni Networks")
and keeps the per-role card colours (student sky, alumni amber, faculty
emerald) and the faculty-only Faculty Dashboard button.

### 8.2 What changed

- **Hero:** plain light header replaced by a dark-navy `.admin-hero-card
  .alumni-hero` (amber border via the shared `navbar-professional.css`
  contrast fix, so the title renders white): amber INSTITUTIONAL
  DIRECTORY badge with live dot, white title "Student & *Alumni
  Networks*" (amber gradient on "Alumni Networks"), subtitle, Messages
  Hub as an outline-light pill, Faculty Dashboard as an amber button
  (faculty only, unchanged condition). Google Fonts + `admin-luxury.css`
  links added at the top of the block, same as the other alumni pages.
- **Stat cards:** same 4 server-rendered counts (`alumni_count`,
  `students_count`, `faculty_count`, `connections_count`) and the same
  links, now with animated counters (`data-target` = the server number;
  the rendered number stays as the no-JS fallback), reveal-on-scroll,
  amber hover border, and role-tinted icon chips kept.
- **Filter bar:** same GET form, same field names (`search`, `role`,
  `department`, `location`, hidden `scope`), same `onchange` submits,
  same reset button condition. Restyled: search input with icon and
  amber focus, amber selects, amber Filter button, amber active states
  on the scope switcher and quick-filter pills, amber active pagination.
  "Showing X of Y verified members" kept verbatim.
- **Directory cards:** markup unchanged (role cover, avatar/initials,
  department + degree chips, skills/designation info box, Profile /
  Connect / Message / Pending / You actions, `connectUser()` JS verbatim).
  Added `reveal` to the card columns for the scroll animation.
- **New utility definitions:** the page used Tailwind-style colour
  classes (`text-slate-900`, `bg-amber-subtle`, `text-amber-700`, …)
  that do not exist anywhere in the repo CSS — previously they silently
  did nothing (hence the plain/blue look: KPI numbers inherited the
  anchor blue). They are now defined in the page's own `<style>` block
  (page-scoped only), so the tints and amber accents actually render.
- **Clearance:** the wrapper's inline `padding-top: 100px !important`
  is untouched — the screenshot already showed correct navbar clearance;
  the page does not use `.alumni-page-wrapper`, so the shared §7 fix
  does not apply here and was not regressed.
- **Mobile:** hero buttons go full-width ≤576px, scope switcher stretches
  full width with centred links, KPI grid stays 2 columns, member grid is
  a single column below 768px, pagination wraps. `prefers-reduced-motion`
  disables reveal and counters.

### 8.3 What was preserved / verification

- `python3 scripts/validate_templates.py` → **Total errors: 0**.
- Token set-diff vs HEAD: all 46 `{{ }}` / 46 `{% %}` / 21 `url_for()` /
  5 `name=` / 1 `id=` / `connectUser` from the old file still present;
  only additions are the `admin-luxury.css` `url_for` and the counter
  `tick` helper. `app.py` untouched; no route, count or endpoint invented.
- Jinja render test with mocked data (alumni user, 2 members, counts
  1/4/1/1): 20/20 checks pass — hero, KPIs, both scope links, search,
  member cards, Profile/Message/Connect actions, `connectUser()`,
  counters, reveal, result counter, wrapper clearance, no Jinja
  leftovers; empty state renders for `users=[]` with the connections
  scope. No push — local only.

---

## 9. Public (logged-out) mobile drawer redesign (2026-11-17, local — not pushed)

### 9.1 The bug (Rajender's phone screenshot, 2026-11-17 12:12 IST)

The logged-out mobile drawer was still the old light design while the
alumni/admin drawers are dark and professional. Two visible problems:

- **Brand title half-invisible:** the drawer topbar is white, but
  `.drawer-brand-title` is white (`!important`, inline `<style>` in
  `base.html` line ~173) — so "ALUMNI" vanished on white and only the
  green "HUB" (`brand-highlight`) showed.
- **Five white cards:** Home, About, Services, Events, Contact rendered
  as big white `.mobile-nav-link` cards (the old public style), clashing
  with the dark drawer used everywhere else.

### 9.2 What changed

Same fix as the alumni white-card fix (§6.7), mirrored for the public
branch — dark navy, sky-blue accent (`#38bdf8`) for the public identity
instead of alumni amber:

- **`templates/base.html`**
  - Overlay gets a new theme class only when logged out:
    `{% elif not current_user.is_authenticated %} public-drawer-theme`.
    Admin / faculty / alumni / student overlays are unchanged.
  - The five public links are now one **Explore** group of dark
    `.adm-drawer-row` rows (the same global group classes the alumni
    drawer uses): Home, About, Services, Events, Contact — each with a
    coloured icon tile, title + subtitle, and chevron. The old white
    cards are gone, including the duplicate Services/Events/Contact
    cards in the `{% else %}` branch (removed, with a note left behind).
  - The shared Home/About block still serves students: logged-out users
    get the new group, students keep their two original white links
    verbatim (moved into an `{% elif %}`).
  - **Sign In / Register** restyled as a professional pair — Sign In is
    now an outline-light button, Register a blue-gradient primary CTA
    (routes `/login` and `/register` unchanged, inline styles moved into
    CSS classes `public-auth-signin` / `public-auth-register`). A small
    "ALUMNI HUB • JIMS ROHINI" footer caption was added under the
    buttons, mirroring the alumni session footer.
  - `navbar-professional.css` cache-buster bumped `?v=4.0` → `?v=4.1` so
    phones actually load the new CSS.
- **`static/css/navbar-professional.css`** — new `public-drawer-theme`
  section (~235 lines) at the end of the file: dark-navy overlay
  gradient, dark topbar (so the white ALUMNI title + green HUB finally
  read), sky-blue group-box/row/chevron tints, auth-button styles, a
  themed PWA banner, and a ≤360px media query. Rules are
  `#mobileMenuOverlay.public-drawer-theme`-scoped with `!important`
  where they must beat the bullet-proof inline `<style>` in `base.html`
  (same pattern as the faculty/alumni theme blocks).
- **Topbar fix, explained:** the topbar stays sticky white in the base
  rule, but under `public-drawer-theme` it becomes dark navy
  (`rgba(11, 30, 58, 0.95)`) — so the existing white brand title and
  green HUB highlight are readable with no change to the brand markup
  or the logo.

### 9.3 What was preserved / verification

- `python3 scripts/validate_templates.py` → **Total errors: 0**;
  `base.html` parses cleanly under Jinja2 as well.
- CSS brace check: 708 open / 708 close, balanced.
- Render test (`/tmp/public_drawer_render_test.py`, mocked
  `current_user`/`request`/`url_for`): **21/21 checks pass** — public
  render: overlay carries only `public-drawer-theme`, all 5 Explore
  rows are dark `adm-drawer-row` links, zero white `mobile-nav-link`
  cards, `/login` + `/register` intact, no Jinja leftovers; student
  render: no theme class, original Home/About white links and
  Dashboard/Messages/Jobs intact; alumni render: `alumni-drawer-theme`
  kept, its own Explore group intact.
- **360px audit (static):** no fixed width above the viewport in the
  new CSS (only a 480px `max-width` on the fluid content column and
  100% widths); rows/buttons are 52px tap targets (50px at ≤360px);
  row subtitles use the global ellipsis rule, so nothing overflows or
  clips.
- Desktop navbar untouched; alumni, admin, faculty and student drawer
  branches untouched (verified by `git diff` — only the 5 public hunks
  in `base.html`). No push — local only, pending Rajender's approval
  together with the unpushed Network-page changes.

## 10. Student header / navbar + mobile drawer redesign (2026-11-17, local — not pushed)

Mirrors the alumni navbar redesign (§6) and the later drawer fixes (§6.7,
§9): same structure, same grouped dropdowns / drawer groups, same
animation language — sky-blue accent (`#0ea5e9` / `#38bdf8`) for the
student identity instead of alumni amber, so students stay visually
distinct from alumni / admin / faculty / public.

### 10.1 What the student nav was before

- **Desktop:** plain white pill links (Dashboard, Messages,
  Notifications) + two bare dropdowns (Connect: Alumni Directory,
  Mentorship Hub; Opportunities: Jobs & Internships, Campus Events) with
  plain text items, no active states on Messages/Notifications/dropdowns,
  no role tag, brand linked to `/` (public home) for students.
- **Mobile drawer:** the generic grey `.mobile-profile-card` with grey
  `.action-btn` quick actions, plus **seven white `.mobile-nav-link`
  cards** (Dashboard, Messages, Alumni Directory, Mentorship Hub, Jobs &
  Internships, Campus Events, Notifications), two more white Home/About
  cards at the top and a white Events card at the bottom — the same
  white-card problem fixed for alumni (§6.7) and public (§9). No theme
  class on the overlay.

### 10.2 Desktop navbar (student only)

- **Brand:** new `.student-brand-wrap` — brand now links to
  `/student/dashboard` for students (was `/`), with a sky STUDENT tag
  (`.student-brand-tag`, `fa-user-graduate`) and a sky pulse beacon
  (`.student-pulse-beacon`, `studentBeaconPulse` keyframes), mirroring
  `.alumni-brand-wrap` / `.alumni-brand-tag` / `.alumni-pulse-beacon`.
  The tag is hidden below 768px in CSS — the alumni ALUMNI tag was
  removed for exactly this mobile overflow (§6.8); the tag still shows
  in the drawer topbar and the user pill.
- **Pill buttons:** new `.nav-student-btn` (mirrors `.nav-alumni-btn`):
  sky-tinted pill `#f0f9ff` / border `#bae6fd`, hover `#e0f2fe`,
  active = sky gradient `#0ea5e9 → #0284c7` with white text. Same
  1200–1400px / 992–1199px responsive sizing rules as the alumni buttons.
- **Connect dropdown** (rich rows, ids `studentConnectDropdown`): intro
  header "Connect & Learn — Network, Mentors & Community" + Alumni
  Directory, Mentorship Hub, Community Group (`/community-group` —
  already a student link in the old drawer quick actions). **Career
  dropdown** (renamed from "Opportunities", same links + one addition,
  id `studentCareerDropdown`): intro "Career & Events — Jobs,
  Internships & Campus Life" + Jobs & Internships, Campus Events,
  Upgrade to Alumni (`/upgrade` — already in the user-pill menu).
  Dropdown menus reuse the admin `.nav-admin-dropdown-menu` structure
  with student-scoped sky overrides (`.nav-student-dropdown-menu`,
  `.nav-student-menu-item`), including the desktop hover-open rule.
- **Active states added:** Connect toggle is active on `network` /
  `mentorship` / `/community-group`, Career toggle on `list_jobs` /
  `events` / `upgrade`, Messages on `messages` (same check as alumni),
  Notifications on `notifications`. Dashboard active check unchanged.
- **Hamburger toggler:** new `.student-custom-toggler` (sky
  border/hover), mirroring `.alumni-custom-toggler`. Same button, same
  `id="navbarToggler"` — no JS change.
- **User pill:** new `.student-user-pill` (white pill, `#0284c7`
  border, sky avatar ring) + STUDENT role tag next to the name,
  mirroring `.alumni-user-pill` / `.alumni-user-pill-tag`. The pill
  dropdown menu itself is unchanged (My Profile, Messages, Upgrade to
  Pro, Settings, Change Password, Logout).
- All pre-existing student desktop links and hrefs unchanged:
  `/student/dashboard`, `/messages`, `/network`, `/mentorship`,
  `/jobs`, `/events`, `/notifications`.

### 10.3 Mobile drawer (student only)

- Overlay now gets `.student-drawer-theme` (dark sky-navy gradient,
  dark topbar / close button / group boxes), mirroring
  `.alumni-drawer-theme` / `.public-drawer-theme`. Topbar shows the sky
  STUDENT role tag (`.role-tag-student`).
- New **student mobile profile card** (`.student-mobile-card`, sky
  gradient) replacing the generic grey card for students: "STUDENT
  PORTAL" status pill with pulse, "ENROLLED STUDENT" badge, avatar with
  `fa-user-graduate` badge, name + email, and 4 quick tiles — Dashboard,
  Network, Mentorship, Messages — all existing routes, all with
  `adm-drawer-link` so the drawer auto-closes on tap. The generic
  `.mobile-profile-card` is kept verbatim as the fallback `{% else %}`
  branch for any unknown role. Tile icons use the same bare-glyph
  override as the alumni fix (§6.7) so the global `.tile-sky` /
  `.tile-emerald` tinted boxes do not show as muddy squares.
- The 7 white rows are replaced by 5 grouped sections using the admin
  `.adm-drawer-group` / `.adm-drawer-group-box` / `.adm-drawer-row`
  pattern (icon bullet + title + subtitle + chevron, sky accents):
  - **Student Home** — Dashboard, Messages
  - **Connect & Learn** — Alumni Directory, Mentorship Hub, Community
    Group
  - **Career & Events** — Jobs & Internships, Campus Events, Upgrade
    to Alumni
  - **Account** — Notifications, My Profile (`/profile`), Settings
    (`url_for('settings')`), Change Password (`/change_password`),
    Sign Out (`/logout`, danger row)
  - **Explore** — Home, About, Services, Contact
- The shared white Home/About cards and the trailing white Events card
  are gated out for students (same gate-widening as §6.7/§9); Home /
  About / Services / Contact now render as dark rows in Explore, and
  Events lives once in Career & Events (no duplicate — unlike alumni,
  where Explore's Campus Events and Career & Events' Alumni Events are
  different URLs; for students both are `/events`).
- The duplicate generic Logout button below the groups is replaced by
  a sky session footer ("VERIFIED STUDENT PORTAL • JIMS ROHINI"),
  mirroring the alumni footer. Sign Out already exists as a row in the
  Account group.
- No JS was changed: open/close uses the existing `#navbarToggler` /
  `#mobileMenuOverlay` / `#closeMobileMenu` handlers, Escape key, and
  the `.mobile-nav-link, .adm-drawer-link` auto-close listener.

### 10.4 Animations

Same animation language as alumni/admin, all CSS-only (no new JS
libraries, no new JS at all):

- Logo pulse beacon (`.student-pulse-beacon`, 2s) + status pulse on
  the profile card (`.student-status-pulse`, `studentPulse` ring).
- Dropdown open snap (shared `.nav-admin-dropdown-menu` animation) +
  hover-open on desktop ≥992px; hover lift on pill buttons, dropdown
  rows, drawer rows/tiles (translateY −1/−2px, chevron slides).
- **Staggered reveal on drawer open:** the card rises first, then the
  5 groups one by one (`studentRiseIn` keyframes, 0.05s / 0.10s /
  0.16s / 0.22s / 0.28s / 0.34s). Keyed off
  `#mobileMenuOverlay.student-drawer-theme.active` — the JS only
  toggles `.active` on the overlay, so page-load animations would
  already be finished by the time the drawer opens; without `.active`
  there is no animation, so the drawer is fully visible if JS never
  runs.
- No animated counters were added in the nav/drawer — there is no stat
  rendered inside the navbar or drawer to count from.
- `prefers-reduced-motion: reduce` disables the beacons, pulses, the
  staggered reveal (opacity/transform forced to final state) and all
  hover lifts.

### 10.5 Mobile & accessibility

- Rows are min 52px tall (50px at ≤360px), quick tiles min 64px;
  drawer stacks to one column at 360px with no horizontal overflow
  (no fixed width above the viewport in the new CSS — only the 480px
  `max-width` on the fluid content column, same as public); subtitles
  truncate with ellipsis (same as admin rows).
- **Top clearance — no new rules needed:** unlike the alumni §7 fix,
  student pages already clear the fixed navbar via
  `static/css/theme-system.css` (`--nav-header-offset-desktop` 135px /
  mobile 100px on `.student-hero-section` and the generic
  `.main-wrapper > div:first-child` rule, which covers
  `.jobs-page-wrapper`, `.profile-wrapper`, `.settings-wrapper`;
  mentorship/notifications carry inline `margin-top: 80px`, network
  `padding-top: 100px`). Verified statically; nothing was added.
- `aria-expanded` / `aria-label` / `aria-controls` untouched; focus
  behaviour unchanged (Escape closes and refocuses the toggler).

### 10.6 What was preserved / verification

- `python3 scripts/validate_templates.py` → **Total errors: 0**.
- CSS brace check: 822 open / 822 close, balanced.
- Render test (`/tmp/student_nav_render_test.py`, mocked
  `current_user`/`request`/`url_for`): **58/58 checks pass** — student
  render: overlay carries only `student-drawer-theme`, zero
  `class="mobile-nav-link"` and zero `class="action-btn"`, profile card
  + 4 tiles + 5 groups, all 17 student hrefs present, brand href is
  `/student/dashboard`, cache-buster `?v=4.2`; alumni render keeps
  `alumni-drawer-theme` + its 5 groups, admin keeps `admin-drawer-theme`,
  faculty keeps `faculty-drawer-theme`, anonymous keeps
  `public-drawer-theme` + its 5 Explore rows — and none of the four
  renders contains any student class or `/student/dashboard` link.
- Token set-diff vs HEAD (`base.html`): no `url_for()` / `name=` lost;
  only the brand-href `{{ }}` expression changed (student branch added
  inside it, admin/faculty/alumni branches byte-identical) and the two
  widened gate `{% %}` conditions; 5 new `id=` values added
  (`navStudentDashboard`, `navStudentMessages`,
  `studentConnectDropdown`, `studentCareerDropdown`,
  `navStudentNotifications`), none lost. All 16 gained `href=` values
  are the new group rows / dropdown rows (duplicates of existing
  destinations) plus the `?v=4.2` bump.
- `git diff --stat`: only `templates/base.html` (+325/−49) and
  `static/css/navbar-professional.css` (+714, purely appended at end)
  changed, plus this file. The only `+/-` diff lines mentioning other
  roles' endpoints are the shared brand-anchor line (admin/faculty/
  alumni branches inside it are byte-identical). No page template,
  route, service or backend file was touched. No push — local only.

### 10.7 Deliberately left out (would need new backend data)

- **Unread-messages badge on the Messages pill/tile/row:** no unread
  count is available to `base.html` — `get_unread_message_count()` is
  only passed to the messaging template itself
  (`routes/messaging_routes.py`), and there is no global context
  processor injecting it into the navbar. Adding a badge would need a
  new context processor in `app.py` (backend change) — left out, do
  not invent a count.
- **Profile-completeness ring on the drawer card:** the student
  dashboard computes completeness in its own template/JS; that value
  is not passed to `base.html`. Left out for the same reason.
- **Live counts on tiles/groups** (e.g. pending requests, new jobs):
  no such variables exist in the navbar context; nothing was
  hardcoded.
- **STUDENT tag in the top navbar on phones:** deliberately hidden
  below 768px in CSS — the alumni ALUMNI tag was removed for exactly
  this overflow (§6.8). The tag still shows on desktop navbar, in the
  drawer topbar and in the user pill.

---

## 11. Student pages redesign (2026-11-17, local — not pushed)

Redesign of all 8 remaining student pages to the same admin-level
standard as the alumni 14-page redesign (§0–§2), in the student Sky
theme established by the student header redesign (§10). Done in
parallel by 4 workers, one per file group, then verified centrally.
**Local work only — nothing was pushed to GitHub.**

### 11.1 Scope — what was (and was not) redesigned

| File | Before | After | Route that renders it |
|---|---|---|---|
| `templates/student/dashboard.html` | 2,801 | 1,835 | `GET /student/dashboard` |
| `templates/student/profile.html` | 827 | 800 | `GET /student/profile/<id>` |
| `templates/student/edit_profile.html` | 821 | 966 | `/student/profile/<id>/edit` (GET, POST) |
| `templates/student/jobs.html` | 421 | 519 | `GET /student/jobs` (list_jobs) |
| `templates/student/mentorship.html` | 185 | 353 | `GET /student/mentorship` |
| `templates/student/notifications.html` | 105 | 250 | `GET /student/notifications` |
| `templates/student/settings.html` | 716 | 702 | `GET /student/settings` |
| `templates/student/upgrade.html` | 240 | 392 | `GET /upgrade` (student role) |
| **Total** | **6,116** | **5,817** | |

`templates/student/network.html` was **not** touched — it was already
redesigned in §8 (commit d67a542). Nothing else was changed: `app.py`,
`templates/base.html`, `templates/alumni/*`, `templates/admin/*`,
`templates/faculty/*`, `templates/common/*`, `templates/auth/*` are
untouched (verified: `git status` shows only the 8 files above;
4,092 insertions / 4,399 deletions). Dashboard line count fell
because ~1,000 lines of heavy inline CSS/effects (mesh balls, blobs,
particles, 3D tilt, holographic borders, neon glow, skeleton loaders)
were replaced by shared `admin-luxury.css` + one tight page-local
stylesheet — content was not cut.

### 11.2 Design system (student Sky)

Same tokens as §0, with Sky replacing amber:

| Token | Value |
|---|---|
| Student primary | `#0ea5e9` / `#38bdf8` (Sky) |
| Sky gradient text | `#bae6fd → #7dd3fc → #38bdf8 → #0ea5e9` (page titles) |
| Hero gradient | `linear-gradient(135deg, #0b1329 0%, #172554 48%, #0f172a 100%)` (same dark navy as admin/alumni) |
| Fonts | Outfit / Plus Jakarta Sans / JetBrains Mono |
| Shared CSS | `static/css/admin-luxury.css?v=2.4` (loaded by every page) |
| Shell | `.admin-page-wrapper` → 3 ambient orbs → `.admin-container` → dark hero card |
| Cards | White, 18–28px radii, soft shadows, hover lift `translateY(-5px)` |
| Glass | `rgba(255,255,255,0.05–0.08)` panels, `backdrop-filter: blur(10–16px)` |
| Danger / success | `#ef4444` rose / `#10b981` emerald |

Hero titles are forced white `!important` in each page's own
`<style>` block — the §7 navbar-overlap contrast fix in
`navbar-professional.css` is alumni-scoped, so each student page
re-asserts it. Each page carries one page-scoped `<style>` block (the
§8 pattern); no new global CSS files were created.

**Mobile rules (all pages):** layouts work at 360px — Bootstrap
grids stack to one column, no horizontal overflow, touch targets
≥44px (forms/buttons 44–48px), hero titles use `clamp()`, hero
buttons full-width ≤576px. Navbar clearance comes from the shared
shell / `theme-system.css` offsets (145px desktop / 98px mobile) —
verified statically per page, no hero is clipped.

**Animation rules (all pages):** subtle reveal-on-scroll via
`IntersectionObserver` (opacity + small rise, staggered), hover lift
on cards, animated counters only where numbers already exist on the
page (`data-target` = the server number; the rendered number stays as
the no-JS fallback), pulsing live/badge dots. Every page respects
`@media (prefers-reduced-motion: reduce)`.

**Features rule:** new extras were added ONLY where they use
data/routes already passed to that template. No invented endpoints,
no fake or hardcoded data presented as live.

### 11.3 Per-page notes

#### 11.3.1 dashboard.html — 2,801 → 1,835
- Shell + sky hero: live sky badge with pulsing dot, white greeting
  pill (`#dynamicGreeting` / `#timeGreetingBadge` kept), `Hello,
  <name>!` with sky gradient text and the preserved typing effect,
  Career Board (sky gradient) + Network (glass) buttons, glass
  profile-completeness panel (ids/logic untouched), avatar block
  verbatim with sky tag.
- Stats: same 4 cards (Alumni / Mentors / Semester / GPA), sky icon
  gradients, hover lift. Numbers now render server-side as text
  (e.g. `{{ alumni | length }}`) as the no-JS fallback, with
  `data-target` still driving the preserved `animateValue` counter.
- All sections preserved: Network Insights charts, Recommended for
  You, category pills (sky active state), pending requests,
  filter/search, 3-tab directory, mentorship banner (dark, white
  `!important` h2/p guard like alumni's), Quick Actions, FAB, both
  detail modals (student modal header recolored sky; alumni modal
  kept green).
- VanillaTilt 3D tilt removed (script tag + `VanillaTilt.init`);
  `initAdvancedAnimations` keeps only the button glow (card hover is
  CSS); `staggerCardAnimations` uses the new `stuRise` keyframes. All
  16 JS function definitions preserved by name, including both
  duplicate `connectUser` definitions.

#### 11.3.2 profile.html — 827 → 800
- Dark-navy hero with sky pulsing "STUDENT PROFILE" badge, user's
  name as the hero title with sky gradient text, enrollment no. |
  department subtitle, glass "Semester X" chip, animated wave
  divider, content overlapping −90px.
- Identity card: avatar with conic sky ring + green online dot (same
  `{% if %}` avatar/`initials` fallback and verbatim `onerror`),
  "Student" sky tag, Semester/CGPA mini-stats (Semester has an
  animated counter; CGPA rendered as-is since it is a decimal),
  enrollment/department badges, WhatsApp / Professional Mail / Gmail
  Compose buttons, own-profile → Edit Profile + Change Password,
  other-profile → Send Connection Request.
- Academic Information (Department/Degree + CGPA + animated semester
  progress bar from `data-semester`), Skills & Achievements
  (comma-split skill chips, pipe-split achievement rows, both
  original empty states kept).
- The old typing effect was dropped (it rewrote the gradient title
  char-by-char) and the heavy mesh/tilt/magnetic effects removed;
  `sendConnectionRequest` / `showToast` and the
  `/api/connection-request/send` flow are verbatim.

#### 11.3.3 edit_profile.html — 821 → 966 (profile editing — most critical)
- `admin-page-wrapper` + 3 sky orbs + `admin-container` +
  `admin-hero-card` (student-hero variant), JetBrains Mono "STUDENT
  PROFILE · EDIT MODE" badge, "Edit Your **Profile**" sky-gradient
  title, original subtitle kept, Photo/Personal/Academic/Portfolio
  chips, hero Profile Completeness stat box.
- Four numbered white cards: **01 Profile Photo, 02 Personal
  Information, 03 Academic Information, 04 Expertise & Portfolio**
  with sky icon tiles, light inputs (`#f8fafc`, sky focus ring +
  animated underline), explicit `for=` labels.
- Sidebar: 8-item completeness checklist (photo, name, phone,
  semester, CGPA, skills, achievements, resume link — computed live
  in JS from fields already on the page), Live Preview card (avatar,
  name, department, enrollment, semester, CGPA, skills, "View Full
  Profile" link), Quick Tips, mobile sticky save bar (`d-xl-none`,
  inside the form).
- Drag-and-drop zone wired to the same `previewPhoto` handler;
  double-submit guard (disables submit buttons, "Saving…" only after
  native validation passes).
- **Form intact (verified):** `<form id="editForm" method="POST"
  enctype="multipart/form-data">` unchanged; all 8 field names
  identical (`profile_pic`, `name`, `phone`, `semester`, `cgpa`,
  `skills`, `achievements`, `resume_link`); photo input
  `accept="image/*"` + `onchange="previewPhoto(this)"` +
  `onerror="handleStudentAvatarError(this)"` preserved; default-avatar
  SVG (incl. `studRadGrad`/`studAccGrad` ids) kept verbatim except
  the border recolored sky; semester `<select>` loop and ordinal
  (`st/nd/rd/th`) Jinja copied verbatim; `previewPhoto`,
  `handleStudentAvatarError`, `showToast` all present (previewPhoto
  now also syncs the preview-card avatar + completeness). Email /
  enrollment no. / department stay disabled with no `name=` (never
  submitted), exactly as before. No `removePhoto` button (alumni edit
  has one): the student's original photo flow has no remove path and
  the route never clears `profile_pic`.

#### 11.3.4 jobs.html — 421 → 519
- Sky shell/hero with pulsing live badge, gradient title, glass stat
  chips (total openings / recommended / internships, computed from
  passed data via namespace — no new backend data), restyled filter
  card + quick type chips, recommended grid and list rows as white
  sky-accent cards with hover lift, "no filter results" empty state
  with Clear Filters, animated counter on total openings,
  reveal-on-scroll.

#### 11.3.5 mentorship.html — 185 → 353
- Sky shell/hero; all 3 mentor cards preserved verbatim (names,
  bios, skills, badges, `alert()` texts) in white lift cards with sky
  CTAs; hero shortcut added to Explore Jobs.
- **The previously dead search/filter now works:** `mentorSearchInput`
  + the two selects (given ids) wired to a new `applyMentorFilter()`
  over `data-search`/`data-dept`/`data-industry` attributes, with a
  live "Showing N mentors" count and a no-results empty state.

#### 11.3.6 notifications.html — 105 → 250
- Sky shell/hero with pulsing badge; "All Caught Up!" card and all 4
  preference toggles (`emailNotif`, `eventNotif`, `messageNotif`,
  `jobNotif`) preserved, sky switch styling, hover-lift preference
  rows, reveal animations.

#### 11.3.7 settings.html — 716 → 702
- Sky shell/hero, "Manage Your **Settings**" sky-gradient title, sky
  badge with pulsing live dot ("Account Settings"); hero buttons
  Dashboard + Edit Profile.
- White 20px-radius cards with hover lift; each tab gets an icon-chip
  section header + subtext; sky-gradient `.btn-sky` buttons, sky
  focus rings, sky toggle switches; notification/privacy toggles
  rebuilt as `.pref-row` cards (same ids, labels, checked states).
- Floating-label inputs replaced with top-label inputs (alumni
  pattern) — same `id`/`name`/`value`/`required`/`disabled` on every
  field; password-strength bar, 2FA block, visibility `<select>` (all
  3 options, "Community (Visible to alumni only)" selected) all
  preserved verbatim. All 9 toggle checked-states identical to the
  original.
- Sidebar mini-profile card using only `current_user` (initials via
  the existing `initials` filter, name, email, STUDENT badge); glass
  quick-links strip in the hero (My Profile, Network, Messages,
  Notifications, Mentorship — all verified existing endpoints).
- Nav pills become a horizontal scrollable strip below 992px (same as
  alumni); quick-links strip scrolls horizontally ≤576px.
- Route check: `/settings` (app.py ~4829) passes **no variables** —
  the template only ever used `current_user.name` /
  `current_user.email`, both preserved.

#### 11.3.8 upgrade.html — 240 → 392
- Sky shell/hero (centered, like alumni upgrade); all 3 plans (₹0 /
  ₹499 / ₹899), feature lists, comparison table, and `alert()`
  buttons preserved; Pro plan highlighted with sky border + MOST
  POPULAR badge, hover lift, staggered reveal, hero shortcut chips
  to Jobs / Mentors / Network.
- **Note:** the student `upgrade.html` is a **pricing page** rendered
  by `/upgrade` (app.py ~3783) with no variables and no form fields —
  it is not the form page the alumni `upgrade.html` is. No link to
  the upgrade-to-alumni route was added (see §11.6).

### 11.4 Extras added (existing data/routes only)

- **Dashboard:** 4-tile Quick Shortcuts row — Network
  (`search_network`), Career Board (`list_jobs`), Messages
  (`messages`), My Profile (`student_profile`); `{% else %}` empty
  states for the alumni / student / faculty grids and recommendations.
  **Bug fix:** alumni cards were classed `alum-card` while
  `performSearch()` queries `.alumni-card`, so global search silently
  did nothing on the Alumni tab. Renamed to `alumni-card`; search now
  works on all three tabs.
- **Profile:** Resume / LinkedIn button when
  `profile['resume_link']` exists; Quick Links row to
  `dashboard_student`, `network`, `mentorship`, `messages`.
- **Edit profile:** completeness checklist, Live Preview card, Quick
  Tips, mobile sticky save bar, drag-and-drop photo zone, double-
  submit guard.
- **Jobs:** glass stat chips from passed data, quick type chips, "no
  filter results" empty state with Clear Filters.
- **Mentorship:** working client-side search/filter (was dead),
  "Showing N mentors" count, no-results empty state, Explore Jobs
  shortcut.
- **Settings:** hero Dashboard + Edit Profile buttons, glass
  quick-links strip, sidebar mini-profile card.
- **Upgrade:** Pro plan highlight + MOST POPULAR badge, hero shortcut
  chips to Jobs / Mentors / Network.

### 11.5 What was preserved (verification)

- `python3 scripts/validate_templates.py` → **Total errors: 0**
  (re-run centrally after all 4 workers finished; mid-work validator
  runs showed transient errors in files still being edited).
- Token set-diff vs HEAD, whitespace-normalized, for all 8 files:
  every `{{ }}`, `{% %}`, `url_for()`, `name=`, `id=` and JS function
  name from the old files is present in the new files — **0 missing
  in every category, on every file** (a naive whitespace-sensitive
  diff briefly flagged 4 re-indented multi-line expressions; all
  confirmed present after normalization).
- Edit-profile form: all 8 field names, photo preview flow, submit
  behaviour verified intact (§11.3.3). Settings: all 30 `id=`s, all 5
  `name=`s, all 9 toggle states identical. Dashboard: all 16 JS
  function definitions, 13 `onclick`s, 20 `getElementById`s present.
- Jinja render smoke tests: dashboard (populated + all-empty states),
  settings (StrictUndefined mock `current_user`), jobs/mentorship/
  notifications/upgrade (dummy data) — all render clean.
- `app.py` untouched; no route, count or endpoint invented.

### 11.6 Pre-existing issues found (NOT fixed — out of scope, viva-relevant)

These were found during the redesign, left exactly as they were.
Do not present them as working features in the viva.

1. **`/student/upgrade-to-alumni` is broken (would 500) — FIXED, see §11.8.**
   `upgrade_to_alumni()` (app.py ~3714) renders
   `templates/upgrade_to_alumni.html`, which **did not exist** in the
   repo (verified: `ls` fails; only root `templates/upgrade.html`
   exists). The student pricing page (`student/upgrade.html`) has no
   working path to it, and no link to it was added. Needs a template
   or a route fix in a separate task.
2. **Dashboard "Upgrade to Alumni" button is dead — FIXED, see §11.8.** It targets
   `#upgradeModal`, but no element with that id exists anywhere in
   the repo. Preserved unchanged.
3. **`connectFromModal()` is undefined** in dashboard.html (student
   modal Connect button calls it). Preserved unchanged — FIXED, see §11.8.
4. **Hardcoded (non-live) numbers preserved on the dashboard:**
   mentorship banner "500+ Active Mentors" / "1.2k Success Stories",
   and Chart.js data (alumni growth `[12, 19, 3, 5, 2, 3]`;
   TCS/Infosys/Wipro/Google/Microsoft `30/20/15/10/25`). Do not
   present these as live in the viva.
5. **Dashboard `s['skills']` always shows "No skills listed":** the
   route's query does not select `skills` for student cards.
   Pre-existing; the template was not changed to fake it.
6. **Mentorship mentor cards are hardcoded** in the template (3
   mentors); the search now filters them client-side, but a real
   mentor directory needs a backend query.
7. **Upgrade Pro/Master buttons are `alert()` placeholders** in the
   original; a real checkout needs a payment flow.

### 11.7 Deliberately left out (would need new backend data)

- Unread-messages badge / live notification counts (notifications
  template receives no notification list — static "All Caught Up!"
  state only; messaging count is not passed to these templates).
- Profile-completeness ring on profile/shortcut tiles; live counts
  on dashboard shortcut tiles (no such variables exist in these
  templates' contexts; nothing hardcoded).
- Real chart data aggregated from the alumni table (pass-year/company
  counts) and real mentor counts for the dashboard banner — would
  need route/query changes.
- Showing the student's phone number on the public profile — the
  field exists on `user` but the old page never displayed it, so it
  was not newly exposed.
- 2FA enable, theme selector, and settings persistence remain exactly
  as before (client-side toast only, as in the original) — wiring
  them to real endpoints would need new backend work.

### 11.8 Upgrade-to-alumni 500 fix (2026-11-17, local — not pushed)

Fixes §11.6 items 1–3. The route was verified broken because the
template it renders did not exist; items 4–7 above are still open.

- **New file `templates/upgrade_to_alumni.html`** (root `templates/`,
  not `templates/student/` — the route renders the bare name).
  Student Sky design system from §11.2 (dark-navy hero, white cards,
  `admin-luxury.css?v=2.4`, reveal-on-scroll, 360px mobile-friendly).
  Shows the student's existing profile read-only
  (`profile['enrollment_no']`, `profile['department']`,
  `profile['degree']` — bracket syntax, as in the other student
  pages) plus a "What Changes" card. The form posts to the same URL
  (`action="{{ url_for('upgrade_to_alumni') }}"`, POST) with exactly
  the fields the route reads — `pass_year` (number input, required),
  `company_name` (optional), `designation` (optional) — no extra
  fields added. Render-tested with a mocked profile + student user:
  14/14 checks pass (form method/action, all three field names,
  `pass_year` required, profile values rendered, no Jinja leftovers).
- **Dashboard "Upgrade to Alumni" button (2a):** the dead
  `data-bs-target="#upgradeModal"` button is now an anchor to
  `url_for('upgrade_to_alumni')`, same classes/label — one-line
  change, dashboard otherwise untouched.
- **`connectFromModal()` (2b):** defined. The static onclick fired
  only while the student modal was still loading (the button is
  rewired to `connectUser()` after the `/api/student` fetch
  succeeds). Fix: a `modalStudentId` variable set in
  `viewStudentModal()` and a `connectFromModal()` that calls
  `connectUser(modalStudentId, 'student')` if set. The alumni modal
  was untouched (its button is an anchor, no undefined function).
- **Other missing templates (full scan):** every `render_template`
  target in `app.py` + `routes/*.py` (83 literal + multi-line
  targets) was checked against files on disk — **no other missing
  template exists**. The upgrade template was the only one.

## 12. Student FAB fix + footer restore + feature re-polish (2026-11-17, local — not pushed)

Rajender reported three things on the student pages after the §11
push: the floating **+** button did nothing, the footer looked
"thoda kharab" on student pages, and the recently added features
needed to look better than before. All three are fixed here, local
only — nothing pushed.

### 12.1 The + button — what it was, what it does now

**The bug (verified in code):** the Floating Action Button on
`templates/student/dashboard.html` was a fixed 60px sky-gradient
circle at bottom-right with three sub-buttons (Search → `#globalSearch`,
Messages → `messages`, Profile → `student_profile`) stacked above it
at fixed offsets 90/150/210px. The main **+** had **no click
handler at all**, and the three sub-buttons were **always visible** —
so the + did nothing and a permanent cluster of four floating circles
sat on the page. It pre-dated the §11 redesign (present at HEAD
5617a98) but was never wired up.

**Now (`dashboard.html` only — no other student page has a FAB):**
- Tap **+** → the three actions open with labels (Search / Messages /
  Profile), staggered 0.05s apart; the **+ rotates 135° into ×**.
- Tap **+** again, tap **anywhere outside**, or press **Escape** →
  the menu closes. Tapping an action also closes it, then follows
  the same destination as before (all three URLs unchanged).
- The actions are **hidden by default** (`opacity: 0`, `visibility:
  hidden`, `pointer-events: none`, `aria-hidden="true"`); only the
  single + circle shows until opened.
- On phones ≤576px the FAB is compact (52px main, 44px actions,
  16px from the corner) so it never crowds the screen.
- `prefers-reduced-motion` disables the rotate/stagger transitions.
- Render-tested: 12/12 checks pass (toggle button, hidden-by-default
  actions, setOpen JS, outside-click + Escape close, all three
  destinations, no leftover `.sub-button`).

### 12.2 The footer — root cause (it was never broken)

**Verified by rendering:** the footer HTML in `base.html`
(`footer.footer-custom#mainFooter`, marquee + grid + bottom bar) is
**byte-identical** between the student and alumni dashboard renders
(18,536 chars), the footer CSS was touched by **0 lines** in both
the header push (d67a542..5617a98) and the pages push
(5617a98..72fb80e), and the bottom spacing is identical too
(`.admin-page-wrapper` `padding-bottom: 4.5rem` on both). There is no
student-specific footer branch. **The footer code was never changed
or spoiled.**

**The real cause:** the always-visible FAB cluster — fixed, `z-index:
1030` — floated on top of the footer whenever Rajender scrolled to
the bottom of the student dashboard, covering footer links/text. The
alumni dashboard has no FAB, which is why its footer looks perfect.
That is the whole difference.

**The fix (no footer redesign, spacing/overlap only):**
- The FAB now **fades out automatically while the footer is on
  screen** (`IntersectionObserver` on `#mainFooter`, class
  `fab-parked`; it also closes the open menu). The footer is never
  covered by the button again.
- The FAB is hidden by default (see §12.1), so only one small circle
  ever floats — never the old four-circle cluster.
- Small spacing restore: on phones the dashboard's
  `.admin-container` bottom padding was `0` (`0.9rem 0.9rem 0`), so
  the last card sat flush; it is now `0.9rem 0.9rem 1.25rem`, giving
  the last card breathing room above the footer. The footer itself
  (marquee, grid, bottom bar) is untouched.

### 12.3 Feature re-polish (visible upgrades, polish only)

No form field, link destination, Jinja variable or JS behaviour was
changed anywhere — CSS/hover/focus/animation polish only, all
`prefers-reduced-motion` respected:

- **Dashboard:** Quick Shortcuts now slide their chevron right and
  scale their icon on hover, with a press (`:active` scale) and a
  sky `focus-visible` ring; stat numbers use tabular figures so
  counters don't jitter while counting.
- **Mentorship:** the "Showing N mentors" line is now a proper sky
  pill (blue-tinted background, border, bold sky count) instead of
  plain muted text; the Apply button gets a press scale and a focus
  ring. Filter logic and empty state untouched.
- **Jobs:** type chips get a press scale and focus ring; stat-chip
  counters use tabular figures.
- **Edit Profile:** checklist rows now transition colour/weight when
  an item flips to done, and the done check icon scales in; the
  drag-and-drop zone icon lifts on hover. Completeness math, preview
  and form untouched.
- **Notifications:** each preference row (`.pref-row`) gets a soft
  sky hover background/border and a focus-within ring; the "All
  Caught Up!" bell chip gently floats with a sky glow.
- **Settings:** the sidebar mini-profile avatar gets a sky ring
  (`0 0 0 3px #e0f2fe`) on top of its existing shadow.
- **Upgrade:** the MOST POPULAR badge gets a soft glow pulse (scoped
  to that badge only, via a new `plan-popular-badge` class); the
  price uses tabular figures.
- **Profile:** the avatar's conic-gradient halo now rotates slowly
  (9s linear, disabled under `prefers-reduced-motion`); skill tags
  lift and deepen on hover.

### 12.4 Verification

- `python3 scripts/validate_templates.py` → **Total errors: 0**.
- CSS braces balanced in all 9 student templates (dashboard 568/568,
  profile 220/220, edit_profile 270/270, jobs 181/181, mentorship
  59/59, notifications 66/66, settings 113/113, upgrade 70/70,
  network untouched 424/424). One self-caught slip during the profile
  polish (a rule closed early, leaving a stray brace) was fixed and
  re-verified before finishing.
- Render tests: student dashboard (12/12 FAB checks, footer still
  byte-identical to alumni) + mentorship, edit-profile, jobs,
  notifications, settings, upgrade, profile — all render clean with
  no unrendered Jinja.
- Token set-diff vs HEAD (whitespace-normalised) across all 8 touched
  files: **0 missing** in every category (`{{ }}`, `{% %}`,
  `url_for()`, `name=`, `id=`).
- `git status` shows only the 8 student templates + this doc;
  `base.html`, `app.py`, alumni/admin/faculty/common/auth templates
  and the footer are untouched.
