# Design — Alumni Hub

> Visual and UX design system as implemented across `templates/` and `static/`.
> Brand: **ALUMNI HUB** — *"Building Connections, Creating Opportunities."*

---

## 1. Design Philosophy

| Principle | Meaning | Where It Shows |
| --- | --- | --- |
| **Premium, not plain** | Layered gradients, glass surfaces, motion — a "product" feel rather than an academic demo | Glassmorphism cards, mesh backgrounds, blob animations |
| **Content first, decoration second** | Every animation supports hierarchy or feedback | Counters, hover lifts, badge reveals |
| **Role-aware chrome** | Navigation, hero and dashboard density change per role | `base.html:228-530` |
| **Mobile is a first-class target** | Every layout collapses cleanly | Bootstrap grid + custom media queries |
| **Ambient, not attention-seeking** | Backgrounds move slowly; the content stays still | 60-particle canvas at 0.6 opacity |

---

## 2. Design Tokens

Canonical source: **`static/css/theme.css` `:root`**.

### 2.1 Colour

| Token | Value | Use |
| --- | --- | --- |
| `--primary` | `#1e3a8a` | Deep navy — headings, primary surfaces |
| `--secondary` | `#0ea5e9` | Sky blue — links, accents, info |
| `--accent` | `#f59e0b` | Amber — highlights, CTAs, warnings |
| `--success` | `#10b981` | Emerald — positive state, accept actions |
| `--danger` | `#ef4444` | Red — errors, destructive actions |
| `--light` | `#f8fafc` | Page background tint |
| `--dark` | `#0f172a` | Body text, dark surfaces |
| `--text-dark` / `--text-light` | `#1e293b` / `#64748b` | Text hierarchy |

### 2.2 Gradients

| Token | Value | Use |
| --- | --- | --- |
| `--primary-gradient-*` | `#1e3a8a → #0ea5e9` | Primary buttons, card headers, hero fills, text gradient |
| `--secondary-gradient-*` | `#f59e0b → #ef4444` | Accent/CTA buttons |

### 2.3 Extended Accents
`--accent-green #10b981` · `--accent-green-light #6ee7b7` · `--accent-blue #0ea5e9` · `--accent-cyan #06b6d4` · `--accent-lime #84cc16` · `--accent-teal #14b8a6` · `--warning #f59e0b` · `--info #0ea5e9`

### 2.4 Neutral
`--light-border #e2e8f0` · `--muted #64748b`

### 2.5 Typography

| Token | Value |
| --- | --- |
| Display / headings | **Outfit** (300–800) |
| Body / UI | **Plus Jakarta Sans** (300–800) |
| Monospace accent | **JetBrains Mono** (admin dashboard, OTPs) |
| `--font-weight-bold / semi / normal` | 700 / 600 / 400 |
| Body line-height | 1.6 |

Loaded in `base.html:36-38` and re-declared per-page where a template is standalone.

### 2.6 Spacing Scale
`--spacing-xs .25rem` · `--spacing-sm .5rem` · `--spacing-md 1rem` · `--spacing-lg 1.5rem` · `--spacing-xl 2rem` · `--spacing-2xl 3rem`
Mobile override: `--spacing-2xl → 1.5rem` at ≤768 px.

### 2.7 Radii
`--radius-sm 8px` · `--radius-md 12px` · `--radius-lg 15px` · `--radius-xl 20px`
Cards drop to `--radius-md` on mobile.

### 2.8 Shadows
| Token | Value | Use |
| --- | --- | --- |
| `--shadow-sm` | `0 2px 8px rgba(0,0,0,.08)` | Resting cards |
| `--shadow-md` | `0 5px 15px rgba(0,0,0,.10)` | Raised cards, panels |
| `--shadow-lg` | `0 10px 30px rgba(0,0,0,.15)` | Modals, hero cards |
| `--shadow-xl` | `0 15px 40px rgba(0,0,0,.20)` | Hover state, premium panels |

### 2.9 Motion
`--transition-fast .2s ease` · `--transition-normal .3s ease` · `--transition-slow .5s ease`

### 2.10 Token Governance — Current Problem

`theme.css` is **not linked from `base.html`**. Its variables are re-declared inline in several templates, and three competing scoped token blocks exist:

| Scope | Prefix | Location | Palette |
| --- | --- | --- | --- |
| Global (intended) | `--primary`, `--radius-*`, `--shadow-*` | `static/css/theme.css` | navy/sky/amber/emerald |
| Admin dashboard | `--terminal-*`, `--accent-*`, `--glass-*` | `templates/admin/dashboard_admin.html` | indigo/purple/emerald/amber/rose on `#f8fafc`, dark hero `#030712` |
| Connection monitor | `--cm-*` | `templates/admin/connection_monitor.html` | sky/blue, `--cm-ok #16a34a`, `--cm-warn #d97706`, `--cm-danger #dc2626` |

**Recommendation:** link `theme.css` globally, delete the duplicated `:root` blocks, keep only page-specific *scale* tokens (e.g. `--cm-accent`) where genuinely needed.

---

## 3. Layout System

### 3.1 Page Shell — `templates/base.html`

```
<html>
<head>
  SEO block          meta description · keywords · author · robots · canonical
  Open Graph         og:type / url / title / description / image
  Twitter Card       summary_large_image
  Fonts              Google Fonts (Outfit, Plus Jakarta Sans)
  Icons              FontAwesome 6.4
  Framework          Bootstrap 5.3
  Motion             animate.css 4.1.1 + AOS 2.3.1
  Charts             Chart.js
  Custom CSS         style.css → navbar-professional.css → social_pages.css
                     → ui-enhancements.css → animations.css
  Scoped <style>     .map-container · .network-canvas · .nav-alumni-link
</head>
<body class="premium-theme">
  <canvas id="particle-canvas">            ← global ambient particles
  <div class="scroll-progress-container">   ← top scroll progress bar
  <nav id="mainNavbar">                     ← smart-scroll floating navbar
     ├─ Desktop: island pill nav (public) / role dropdowns (auth)
     ├─ User avatar dropdown (initials or photo)
     └─ Mobile overlay menu with profile card + animated links
  <div class="alerts-container">            ← flash messages / toasts
  <button id="scrollToTopBtn">
  <main class="main-wrapper">{% block content %}{% endblock %}</main>
  <footer class="footer-custom">            ← marquee + 4 columns + map + bottom
  <button id="backToTop">
  AOS.init({ duration: 800, once: true, offset: 50 })
  Inline JS: active-link, smart-scroll, mobile menu, magnetic brand
</body>
```

### 3.2 Navigation by Role

| Role | Menu Structure |
| --- | --- |
| **Guest** | Centred island pill nav (Home · About · Services · Events · Contact) + Log In + **Get Started** gradient CTA |
| **Student** | Dashboard · Connect▾ (Network, Messages, Mentorship) · Opportunities▾ (Jobs, Events) · Notifications · Avatar▾ |
| **Alumni** | Dashboard · Connect▾ (Network, Mentorship, Spotlight) · Opportunities▾ (Find Jobs, Post a Job) · Events · Updates▾ (Messages, Notifications) · Avatar▾ |
| **Faculty** | Dashboard · Connect▾ (Network, My Profile) · Manage▾ (Announcements, Reports, Post a Job, View Jobs) · Events · Updates▾ (Messages, Notifications) · Avatar▾ |
| **Admin** | Dashboard · Users▾ (All / Students / Alumni / Faculty / Approve Requests) · System▾ (Jobs Matrix, Job Approvals w/ live badge, WhatsApp Broadcast, Messaging, Connection Monitor, Analytics, Registration Logs) · Avatar▾ |

**Avatar logic** (`base.html:537-542`): uploaded photo if `profile_pic` starts with `/`, else the `initials` filter (`app.py:95`) — first letter of first + last name, or `?` when the name is empty.

**Active-link highlighting:** inline JS compares `location.pathname` against each `.nav-pill-link` / `.mobile-nav-link` `href` and adds `.active` on exact match or prefix match.

**Smart scroll:** scrolling down past 100 px adds `.scrolled-down` (navbar hides); scrolling up adds `.scrolled-up` (navbar returns). Below 50 px both classes are removed.

### 3.3 Mobile Menu
Full-screen overlay (`#mobileMenuOverlay`) with:
- Role-specific **profile card** — avatar initial, name, role badge, quick-action grid (Dashboard, Approve, Users, Profile; admins additionally get Messaging Control, Announcements, Reports)
- Vertical link list with `--delay` staggered entrance (0.2 s → 0.7 s)
- Body scroll lock while open
- Auto-close on link click or backdrop/close-button tap

---

## 4. Page Inventory & Layout

| Page | Template | Layout Signature | Extra CSS |
| --- | --- | --- | --- |
| Home | `common/home.html` | Hero + mesh background, feature grid, stats counters, CTA | `home-premium.css`, `home-enhancements.css` |
| About | `common/about.html` | Story + mission + **team grid** with photos | `about-enhancements.css` |
| Services | `common/services.html` | Service card grid | `services-enhancements.css` |
| Contact | `common/contact.html` | Split form + info panel + map | `contact-enhancements.css` |
| Events | `events.html`, `alumni/events.html`, `faculty/events.html` | Timeline / card list | — |
| Login / Register | `auth/*.html` | Centred glass card, split role-specific forms | — |
| OTP Verify | `auth/verify_otp.html` | Glassmorphic **6-box OTP input**, 120 s countdown bar, auto-backspace, auto-advance focus | inline |
| Student Dashboard | `student/dashboard.html` (2,399 lines — largest page) | Gradient hero w/ typing name + dynamic greeting + completeness bar · alumni/faculty/student directories · recommendation cards · pending requests | `student-dashboard-animations.css` |
| Alumni Dashboard | `alumni/dashboard.html` | Profile completeness + recommendations + pending requests | — |
| Faculty Dashboard | `faculty/dashboard.html` | Profile header + 4 directory tabs (Students, Alumni, Colleagues) | — |
| Admin Dashboard | `admin/dashboard_admin.html` (1,172 lines) | Dark hero `#030712`, role stat cards, **Chart.js** yearly registration line/bar chart, user table | inline scoped tokens |
| Jobs Matrix | `admin/jobs.html` | High-density table, status toggles, pending queue, filters | — |
| Add/Edit Job | `admin/add_job.html`, `edit_job.html` | **11 sections** — basic info, location & mode, type & eligibility, skills, salary, dates, apply & hiring, intel, logo upload | — |
| Connection Monitor | `admin/connection_monitor.html` | Radial-gradient shell, live filter chips, records table, drill-down modal via `admin_connection_activity` Socket.IO events | inline scoped tokens |
| Public Chat | `messaging/dashboard.html` | Message feed + composer + admin lock banner + online users | — |
| Private Chat | `messaging/private_chat.html` | Bubble thread, typing indicator, read receipts, Socket.IO | — |
| Social pages | `social/*.html` (5 pages) | Centred branded panel per platform | `social_pages.css` |

---

## 5. Component Library

### 5.1 Cards
```css
.card {
  border: none;
  border-radius: var(--radius-lg);   /* 15px */
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  overflow: hidden;
}
.card:hover { transform: translateY(-8px); box-shadow: var(--shadow-xl); }
.card-header {
  background: linear-gradient(135deg, #1e3a8a, #0ea5e9);
  color: #fff; padding: 1.5rem;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
```
Extensions: `.glass-card` (blur + translucent), `.shadow-premium`, `.alert-modern`, `.stat-card`, `.nav-pill-link`, `.mobile-nav-link`, `.badge-role`.

### 5.2 Buttons

| Class | Gradient | Hover |
| --- | --- | --- |
| `.btn-primary` | `#1e3a8a → #0ea5e9` | `translateY(-2px)` + glow `0 10px 25px rgba(30,58,138,.4)` |
| `.btn-secondary` | `#f59e0b → #ef4444` | same lift, red glow |
| `.btn-success` | `#10b981 → #6ee7b7` | same lift, green glow |
| `.btn-premium-gradient` | Brand gradient | + `.btn-glow` box-shadow `0 4px 15px rgba(99,102,241,.4)` |
| `.btn-white` | White | Dark text (mobile overlay logout) |
| `.btn-outline-light` | — | Admin mobile quick actions |

Shape vocabulary: `.rounded-pill` for CTAs and nav pills; default `--radius-md` for form/action buttons.

### 5.3 Forms
```css
.form-control, .form-select {
  border-radius: var(--radius-md);        /* 12px */
  border: 2px solid var(--light-border);   /* deliberate 2px */
  padding: .75rem 1rem;
  transition: all var(--transition-normal);
}
.form-control:focus {
  border-color: #1e3a8a;
  box-shadow: 0 0 0 3px rgba(102,126,234,.1);
}
.input-group-text { background: #fff; border: 2px solid var(--light-border); border-left: none; }
```
Split layouts (`col-lg-6` side-by-side) **stack vertically below the `lg` breakpoint**.

### 5.4 Alerts / Toasts
Four severity variants with a 4 px left accent bar:
| Variant | Background | Accent | Text |
| --- | --- | --- | --- |
| `.alert-info` | blue 10% tint | `--info` | `#0c5de4` |
| `.alert-success` | teal/green 10% tint | `#10b981` | `#0a7e6e` |
| `.alert-warning` | amber 10% tint | `--warning` | `#b87e00` |
| `.alert-danger` | red 10% tint | `--danger` | `#b8202e` |

Rendered in `.alerts-container` with Bootstrap dismiss behaviour and a **5-second auto-dismiss**. Flash categories map: `danger → danger`, `success → success`, `warning → warning`, everything else → `info`.

### 5.5 Badges
`.badge { padding: .6rem .8rem; font-size: .85rem; font-weight: 600; border-radius: 8px }`, with gradient variants `.badge-primary`, `.badge-success`. Role badge `.badge-role` used in the mobile profile card. Recommendation cards carry a **score badge** (green for ML, blue for rule-based) plus an **AI badge** for `source == 'ml'`.

### 5.6 Progress Bars
Height 25 px, `--radius-md`, track `#e9ecef`, fill gradient emerald, label centred inside the bar.

### 5.7 Text Utilities
`.text-gradient-primary` · `.text-gradient-secondary` · `.text-gradient-success` (background-clip: text) and `.gradient-bg-primary|secondary|success` for filled surfaces.

### 5.8 Avatars
```css
.user-avatar  → circular; <img> when profile_pic is a real upload,
                otherwise the {{ current_user.name | initials }} span
.mobile-avatar → larger, single initial
```
External fallback for recommendation cards: `https://ui-avatars.com/api/?name=<Name>&background=random`.

---

## 6. Motion Design

### 6.1 Ambient Backgrounds

| Effect | Implementation |
| --- | --- |
| **Particle network** | `static/js/network-animation.js` — 60 particles, links drawn under 150 px, mouse repel within 200 px, `requestAnimationFrame` loop, canvas sized to its parent |
| **Global particle canvas** | `#particle-canvas` in `base.html`, `.particle-canvas` class, opacity 0.6, `pointer-events: none` |
| **Mesh gradient balls** | `.mesh-background` with 4 `.mesh-ball` elements drifting on long keyframes |
| **Blobs** | `.blob.blob-1 / blob-2 / blob-3` — large radial gradients, slow scale + translate |
| **Aurora hero** | Layered `radial-gradient` overlays, animated hue |
| **Animated bg lines** | `.animated-bg-lines` — diagonal moving strokes behind hero content |
| **Sparkles** | `static/js/sparkles.js` — small ambient cursor sparkles |

### 6.2 Entrances
| Effect | Keyframes |
| --- | --- |
| `fadeInLeft` / `fadeInRight` / `fadeInUp` / `fadeInDown` | Slide + fade with `cubic-bezier(.25,.46,.45,.94)`, staggered `animation-delay` (0.3 s → 0.7 s) |
| `slideInLeft/Right`, `slideUp`, `fadeIn` | Defined in `theme.css:247-287` |
| `bounceIn` | Badge / pill entrance |
| `counterPop` | Numeric value change |
| `titleGlow` (3.5 s infinite) | `drop-shadow` pulse on gradient headings |
| `animate-gradient` | Background-position sweep on gradient text |
| AOS | `data-aos="fade-up"` with `data-aos-delay` 100–300 ms on footer columns |

### 6.3 Micro-interactions
| Interaction | Behaviour |
| --- | --- |
| Card hover | `translateY(-8px)` + shadow ramp |
| Button hover | `translateY(-2px)` + coloured glow |
| 3D tilt | Vanilla Tilt 1.7.0 on premium cards |
| Magnetic navbar brand | `mousemove` → brand shifts up to 30% of cursor offset |
| Typing name | `.typing-text` reveals `{{ current_user.name }}` character by character |
| Word reveal | `.split-text-hero` + `.word-reveal` per-word entrance |
| Scroll progress | Top bar width tracks page scroll |
| Back to top | `#backToTop` / `#scrollToTopBtn` — two buttons serve the same intent |

### 6.4 Scroll-Triggered System — `static/js/animations.js`
```js
new IntersectionObserver(entries => { ... }, {
  threshold: 0.1,
  rootMargin: '0px 0px -100px 0px'
})
```
Observed selectors: `.scroll-fade-up`, `.scroll-fade-down`, `.scroll-fade-left`, `.scroll-fade-right`, `.scroll-scale-in`, `.scroll-rotate-in`, `.counter`.

Counters animate `data-target` over 2,000 ms using `requestAnimationFrame` and are **guarded with a `dataset` flag** so scrolling back up does not restart the count.

### 6.5 Performance Rules for Motion
- Animate only `transform` and `opacity` (GPU-composited).
- Keep ambient loops below 60 particles.
- `prefers-reduced-motion` should disable particles and counters — **not yet implemented**; this is an accessibility gap.

---

## 7. OTP Verification Screen — Signature Component

`templates/auth/verify_otp.html` + `templates/verify_otp.html`

```
┌────────────────────────────────────┐
│         (gradient backdrop)        │
│   ┌────────────────────────────┐   │
│   │   Verify Your Email        │   │
│   │   ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐  │   │  6 individual digit boxes
│   │   │ 8││ 2││ 4││ 1││ 9││ 0│  │   │  auto-advance on input
│   │   └──┘└──┘└──┘└──┘└──┘└──┘  │   │  auto-backspace on delete
│   │  ▓▓▓▓▓▓░░░░░░░  1:47 left  │   │  120 s countdown progress bar
│   │   Resend (26s)   Change    │   │
│   │      Verify                │   │
│   └────────────────────────────┘   │
└────────────────────────────────────┘
```
Design goals: one-handed input on mobile, no native number-picker friction, visual urgency via the depleting bar, and a resend that unlocks only after the cooldown.

---

## 8. Dashboard Design Language

### 8.1 Student Dashboard (`templates/student/dashboard.html`)

```
┌─ Gradient hero (#667eea → #764ba2), 120px top padding ───────┐
│  [🕐 Good afternoon]                    (dynamic greeting)   │
│  Hello,  {{ name }}!                    (typing + gradient)   │
│  "Empower your future..."                                  │
│  [🚀 Explore Career Board]  [👥 Network]                     │
│  ┌─ Profile Completeness ────────────┐                      │
│  │                    72%  [progress]│                      │
│  └────────────────────────────────────┘                      │
├──────────────────────────────────────────────────────────────┤
│  Recommended Connections                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │avatar  │ │avatar  │ │avatar  │ │avatar  │ │avatar  │       │
│  │name    │ │name    │ │name    │ │name    │ │name    │       │
│  │role    │ │role    │ │role    │ │role    │ │role    │       │
│  │score   │ │score   │ │score   │ │score   │ │score   │       │
│  │reason  │ │reason  │ │reason  │ │reason  │ │reason  │       │
│  │AI badge│ │        │ │AI badge│ │        │ │        │       │
│  │Connect │ │Connect │ │Connect │ │Connect │ │Connect │       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
├──────────────────────────────────────────────────────────────┤
│  Alumni Directory  ·  Faculty Directory  ·  Students  ·  Pending │
└──────────────────────────────────────────────────────────────┘
```
Background layers: `.mesh-background` (4 balls) + `.hero-bg` (3 blobs + `.animated-bg-lines`). Card entrance staggered by `--delay`.

### 8.2 Admin Dashboard (`templates/admin/dashboard_admin.html`)
Deliberately **different** from the user dashboards — a control-room aesthetic:
- Dark hero `#030712` with `--terminal-*` tokens, `JetBrains Mono` accents
- Indigo/purple/emerald/amber/rose accent set (distinct from the public navy/sky)
- Four role stat cards (Students / Alumni / Faculty / Event registrations)
- **Chart.js** yearly registration chart fed by `chart_data` (`years`, `students`, `alumni`, `faculty`)
- Full user table with role chips and department/batch columns

### 8.3 Connection Monitor (`templates/admin/connection_monitor.html`)
- Fixed radial-gradient background wash (sky top-left, blue top-right)
- Frosted hero panel with `backdrop-filter: blur(7px)`, `cmFadeUp` entrance
- Filter chips: role (`all` / `student` / `alumni`) + text search
- Records table with sender/receiver cards, status pills, online indicator, messages-exchanged count
- **Live updates** — Socket.IO `admin_connection_activity` injects new rows without refresh
- Drill-down modal fetches `/admin/connection-monitor/user/<id>`

---

## 9. Chat UI Design

### 9.1 Public Chat (`templates/messaging/dashboard.html`)
- Full-height scrollable message feed
- `d-flex` bubble rows; own messages right-aligned, others left with avatar
- System banner (`.alert`) appears on `system_locked` / `system_unlocked`
- Typing indicator driven by `user_typing_public` / `user_stopped_typing_public`
- Admin-only delete button per message
- Composer disabled while the global lock is active
- Initial history via `GET /api/messages/public?limit=50&offset=0`

### 9.2 Private Chat (`templates/messaging/private_chat.html`)
- Header: avatar, name, role, phone (revealed only via the WhatsApp bridge)
- Bubble thread with timestamp
- Typing indicator, read-receipt ticks (`message_read` event)
- `IntersectionObserver` marks messages read when scrolled into view
- History via `GET /api/messages/conversation/<id>/messages?limit=50`
- **Access gate:** reaching this page requires an accepted connection (or admin)

---

## 10. Footer Design

```
┌─ Marquee strip (infinite scroll) ────────────────────────────┐
│  ⭐ Join 15000+ Alumni · 🌍 Connect Globally · 💼 Careers …   │
├──────────────────────────────────────────────────────────────┤
│  ALUMNI HUB      Quick Links     Information     Our Location│
│  description     Home            Privacy Policy  ┌──────────┐ │
│  social grid     About           Terms & Cond.   │ map image│ │
│  LinkedIn        Services        FAQ             │ +overlay │ │
│  GitHub          Contact         Report Issue    └──────────┘ │
│                                                    JIMS Rohini│
├──────────────────────────────────────────────────────────────┤
│  © 2026 ALUMNI HUB                            Designed with ♥ │
└──────────────────────────────────────────────────────────────┘
```
The map block uses `.map-container` with a hover overlay ("View on Maps" with `fa-arrow-up-right-from-square`) and scales 1.02× on hover.

---

## 11. Responsive Strategy

| Breakpoint | Behaviour |
| --- | --- |
| **≥1200 px** | Full desktop nav; all dropdown labels visible (`d-xl-inline`) |
| **992–1199 px** | Nav labels collapse to icons only (`nav-alumni-link`, `d-none d-xl-inline`) |
| **768–991 px** | Bootstrap `md` grid; split forms stack |
| **<768 px** | Mobile overlay menu; dashboards become single-column; `--spacing-2xl` shrinks to 1.5rem; cards drop to `--radius-md` |
| **<576 px** | OTP boxes shrink; hero type scales; map height reduces |

Additional per-page media queries: `home-premium.css`, `about-enhancements.css`, `contact-enhancements.css`, `services-enhancements.css`, `social_pages.css`, `ui-enhancements.css`, `student-dashboard-animations.css`.

---

## 12. Accessibility

| Concern | Status |
| --- | --- |
| Semantic landmarks | `<nav>`, `<main>`, `<footer>` present in `base.html` |
| `aria-label` on icon buttons | Present on toggler, close button, back-to-top |
| `aria-expanded` / `aria-controls` on dropdowns | Present |
| `alt` on images | Map, avatars, team photos |
| Colour contrast | Navy/sky on white passes AA; amber-on-white text uses darkened variants (`#b87e00`, `#856404`) |
| Keyboard focus | Bootstrap default focus rings; no global `outline: none` |
| Screen-reader live regions | ❌ **Not implemented** — Socket.IO message arrivals, toasts and count changes are not announced |
| `prefers-reduced-motion` | ❌ **Not implemented** — particles, counters and blob animations run regardless |
| Form error association | ❌ **Not implemented** — flash alerts are visual only, no `aria-describedby` / `aria-invalid` |
| Colour-only status | ⚠️ Status pills carry text, so meaning is not colour-only |

---

## 13. Design Debt & Recommendations

| # | Issue | Impact | Recommendation |
| --- | --- | --- | --- |
| 1 | `theme.css` not linked; tokens duplicated inline in 3+ templates | Design drift, maintenance cost | Link globally, remove inline `:root` blocks |
| 2 | Two back-to-top buttons (`#scrollToTopBtn` and `#backToTop`) | Duplicate UI, ambiguous behaviour | Keep one |
| 3 | ~1,500 lines of near-duplicate templates (root-level vs `student/`/`alumni/`) | Two sources of truth per page | Shared partials with role blocks |
| 4 | `student/dashboard.html` is 2,399 lines | Unmaintainable | Split into `_hero.html`, `_recommendations.html`, `_directory.html` partials |
| 5 | Fonts re-imported in many templates | Redundant network requests | Load once in `base.html` only |
| 6 | Icon CSS/JS loaded from CDN without SRI | Supply-chain risk | Add `integrity` + `crossorigin` |
| 7 | No `prefers-reduced-motion` support | Motion-sensitive users affected | Gate particles, counters, blobs |
| 8 | No ARIA live regions for real-time updates | Screen-reader users miss messages | Add `aria-live="polite"` to chat feed and toasts |
| 9 | Inline `style="..."` attributes throughout templates | Duplicates tokens, defeats theming | Move to CSS classes |
| 10 | Heavy inline gradients in template markup | Hard to restyle | Promote to utility classes |
| 11 | Emoji used as section icons in email HTML | Inconsistent cross-platform rendering | Move to FontAwesome in web UI |
| 12 | Admin palette diverges from public palette | Feels like two products | Harmonise accents onto the token scale |
| 13 | No dark mode | — | `body.nav-dark-mode` class exists with no implementation; either complete or remove |
| 14 | Counter animation has no `aria-live` alternative | Value change is silent for AT | Announce final value in a visually-hidden span |
| 15 | Particle canvas runs even on low-end devices | Battery / CPU cost | Pause via `IntersectionObserver` when off-screen |

---

## 14. Design Checklist for New Pages

1. Extend `base.html`; never write a standalone document.
2. Use `theme.css` tokens for colour, spacing, radius, shadow, transition.
3. Load page CSS as a new file in `static/css/` and link it in `base.html`.
4. Use Bootstrap grid + `g-4` gutters; verify stacking at 768 px.
5. Add `.card` / `.glass-card` — do not hand-roll card styles.
6. Primary CTA → `.btn-premium-gradient .rounded-pill`; secondary → `.btn-outline-secondary`.
7. Status colour must pair with an icon and a text label.
8. Add `data-aos="fade-up"` for entrances; stagger with `data-aos-delay`.
9. Respect the 5-second toast auto-dismiss; do not stack more than 3.
10. Fill in the full SEO meta block; the block is inherited, verify `{% block title %}`.
11. Keep decorative canvases at ≤60 particles and `pointer-events: none`.
12. Test at 360 px, 768 px, 1280 px and 1920 px before merging.