import re

with open('templates/base.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Desktop Navbar for Faculty
desktop_old = """                    <li class="nav-item">
                        <a class="nav-link nav-pill-link nav-faculty-link {% if request.path == '/network' %}active{% endif %}"
                            href="/network" title="Academic Directory">
                            <i class="fas fa-users"></i> <span>Directory</span>
                        </a>
                    </li>"""

desktop_new = """                    <li class="nav-item">
                        <a class="nav-link nav-pill-link nav-faculty-link {% if request.path in ['/network', '/faculty/network', '/directory', '/faculty/directory'] %}active{% endif %}"
                            href="/network" title="Academic Networks">
                            <i class="fas fa-network-wired"></i> <span>Networks</span>
                        </a>
                    </li>"""

if desktop_old in text:
    text = text.replace(desktop_old, desktop_new, 1)
    print("1. Replaced Desktop Navbar for Faculty")
else:
    print("1. Desktop Navbar pattern not found, checking...")

# 2. Mobile Drawer quick tile for Faculty
tile_old = """                    <a href="/network" class="faculty-tile-btn tile-cyan">
                        <div class="tile-icon"><i class="fas fa-users-viewfinder"></i></div>
                        <div class="tile-label">Directory</div>
                    </a>"""

tile_new = """                    <a href="/network" class="faculty-tile-btn tile-cyan">
                        <div class="tile-icon"><i class="fas fa-network-wired"></i></div>
                        <div class="tile-label">Networks</div>
                    </a>"""

if tile_old in text:
    text = text.replace(tile_old, tile_new, 1)
    print("2. Replaced Quick Tile for Faculty")
else:
    print("2. Quick Tile pattern not found, checking...")

# 3. Category 1 Row in Mobile Drawer for Faculty
cat1_old = """                        <a href="/network" class="adm-drawer-row adm-drawer-link">
                            <span class="adm-row-bullet bullet-cyan"><i class="fas fa-users-viewfinder"></i></span>
                            <div class="adm-row-content">
                                <span class="adm-row-title">Academic Directory</span>
                                <span class="adm-row-sub">Students, alumni &amp; peer faculty roster</span>
                            </div>
                            <i class="fas fa-chevron-right adm-row-chevron"></i>
                        </a>"""

cat1_new = """                        <a href="/network" class="adm-drawer-row adm-drawer-link">
                            <span class="adm-row-bullet bullet-cyan"><i class="fas fa-network-wired"></i></span>
                            <div class="adm-row-content">
                                <span class="adm-row-title">Academic Networks</span>
                                <span class="adm-row-sub">Connected students, alumni &amp; peer network</span>
                            </div>
                            <i class="fas fa-chevron-right adm-row-chevron"></i>
                        </a>"""

if cat1_old in text:
    text = text.replace(cat1_old, cat1_new, 1)
    print("3. Replaced Category 1 Row for Faculty")
else:
    print("3. Category 1 pattern not found, checking...")

# 4. Action-btn bars for /network
act_old = '<a href="/network" class="action-btn"><i class="fas fa-users"></i> Directory</a>'
act_new = '<a href="/network" class="action-btn"><i class="fas fa-network-wired"></i> Networks</a>'
if act_old in text:
    text = text.replace(act_old, act_new)
    print("4. Replaced action-btn Directory to Networks")

# 5. Redesign Events in Mobile Drawer
events_old = """                {% if current_user.role != 'admin' %}
                <a href="/events" class="mobile-nav-link" style="--delay: 0.7s"><i class="fas fa-calendar-alt"></i>
                    Events</a>
                {% endif %}"""

events_new = """                {% if current_user.role == 'faculty' %}
                <!-- ===== FACULTY CAMPUS EVENTS SPOTLIGHT CARD (Redesigned) ===== -->
                <div class="faculty-drawer-event-card-wrap" style="--delay: 0.65s">
                    <a href="/events" class="faculty-drawer-event-card">
                        <div class="f-event-card-top">
                            <div class="f-event-card-badge">
                                <i class="fas fa-calendar-days me-1.5 text-purple-glow"></i>
                                <span>CAMPUS EVENTS</span>
                            </div>
                            <span class="f-event-status-pill"><span class="event-live-dot"></span> Active Schedules</span>
                        </div>
                        <div class="f-event-card-body">
                            <div class="f-event-card-title">Academic Meets &amp; Seminars</div>
                            <div class="f-event-card-desc">Conferences, guest lectures, department workshops &amp; alumni reunions</div>
                        </div>
                        <div class="f-event-card-action">
                            <span><i class="fas fa-calendar-check me-1.5" style="color: #6ee7b7 !important;"></i> Explore All Campus Events</span>
                            <i class="fas fa-arrow-right f-event-arrow"></i>
                        </div>
                    </a>
                </div>
                {% elif current_user.role != 'admin' %}
                <a href="/events" class="mobile-nav-link" style="--delay: 0.7s"><i class="fas fa-calendar-alt"></i>
                    Events</a>
                {% endif %}"""

if events_old in text:
    text = text.replace(events_old, events_new, 1)
    print("5. Replaced Events in Mobile Drawer")
else:
    print("5. Events pattern not found, checking...")

# 6. Add CSS for Faculty Events Card & Faculty PWA Banner
faculty_extra_css = """
        /* ===== FACULTY CAMPUS EVENTS SPOTLIGHT CARD ===== */
        .faculty-drawer-event-card-wrap {
            width: 100% !important;
            max-width: 480px !important;
            margin: 0.35rem auto 0.5rem !important;
        }

        .faculty-drawer-event-card {
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            padding: 1rem 1.15rem !important;
            background: linear-gradient(135deg, rgba(6, 44, 33, 0.96) 0%, rgba(15, 62, 48, 0.9) 100%) !important;
            border: 1.5px solid rgba(167, 139, 250, 0.38) !important;
            border-radius: 16px !important;
            text-decoration: none !important;
            box-shadow: 0 10px 26px -4px rgba(0, 0, 0, 0.45) !important;
            backdrop-filter: blur(14px) !important;
            -webkit-backdrop-filter: blur(14px) !important;
            transition: all 0.22s ease !important;
            position: relative !important;
            overflow: hidden !important;
        }

        .faculty-drawer-event-card::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 4px !important;
            height: 100% !important;
            background: linear-gradient(180deg, #c084fc 0%, #10b981 100%) !important;
        }

        .faculty-drawer-event-card:hover,
        .faculty-drawer-event-card:active {
            background: linear-gradient(135deg, rgba(9, 58, 44, 0.98) 0%, rgba(20, 78, 60, 0.94) 100%) !important;
            border-color: rgba(192, 132, 252, 0.65) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 14px 32px -4px rgba(168, 85, 247, 0.3) !important;
        }

        .f-event-card-top {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }

        .f-event-card-badge {
            display: inline-flex !important;
            align-items: center !important;
            font-size: 0.72rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.06em !important;
            color: #d8b4fe !important;
            text-transform: uppercase !important;
        }

        .text-purple-glow {
            color: #c084fc !important;
            filter: drop-shadow(0 0 6px rgba(192, 132, 252, 0.5)) !important;
        }

        .f-event-status-pill {
            display: inline-flex !important;
            align-items: center !important;
            gap: 5px !important;
            font-size: 0.68rem !important;
            font-weight: 700 !important;
            padding: 3px 9px !important;
            border-radius: 20px !important;
            background: rgba(168, 85, 247, 0.22) !important;
            color: #f3e8ff !important;
            border: 1px solid rgba(192, 132, 252, 0.35) !important;
        }

        .event-live-dot {
            width: 6px !important;
            height: 6px !important;
            border-radius: 50% !important;
            background: #a855f7 !important;
            box-shadow: 0 0 8px #c084fc !important;
            display: inline-block !important;
            animation: eventDotPulse 2s infinite !important;
        }

        @keyframes eventDotPulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.6; }
        }

        .f-event-card-title {
            color: #ffffff !important;
            font-size: 0.98rem !important;
            font-weight: 700 !important;
            line-height: 1.25 !important;
            margin-top: 2px !important;
        }

        .f-event-card-desc {
            color: #94a3b8 !important;
            font-size: 0.76rem !important;
            line-height: 1.35 !important;
        }

        .f-event-card-action {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding-top: 8px !important;
            margin-top: 4px !important;
            border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #6ee7b7 !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }

        .faculty-drawer-event-card:hover .f-event-card-action {
            color: #a7f3d0 !important;
        }

        .faculty-drawer-event-card:hover .f-event-arrow {
            transform: translateX(4px) !important;
            color: #34d399 !important;
        }

        /* Themed PWA Banner for Faculty Drawer */
        #mobileMenuOverlay.faculty-drawer-theme .mobile-pwa-banner {
            background: rgba(3, 39, 28, 0.94) !important;
            border: 1px solid rgba(52, 211, 153, 0.28) !important;
            box-shadow: 0 10px 24px -4px rgba(0, 0, 0, 0.45) !important;
        }

        #mobileMenuOverlay.faculty-drawer-theme .mobile-pwa-text strong {
            color: #ffffff !important;
        }

        #mobileMenuOverlay.faculty-drawer-theme .mobile-pwa-text small {
            color: #a7f3d0 !important;
        }

        #mobileMenuOverlay.faculty-drawer-theme .pwa-btn-install {
            background: #059669 !important;
            border-color: #10b981 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.35) !important;
        }
"""

# Insert CSS before </style> in <head>
css_marker = "/* Mobile Hamburger Button in Floating Header */"
if css_marker in text:
    text = text.replace(css_marker, faculty_extra_css + "\n        " + css_marker, 1)
    print("6. Added extra CSS to templates/base.html")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved templates/base.html successfully!")

