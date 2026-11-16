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
  Home / About at the top of the drawer are unchanged.
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
