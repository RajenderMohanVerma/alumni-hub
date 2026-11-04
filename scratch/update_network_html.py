with open('templates/student/network.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings
content = content.replace('\r\n', '\n')

# 1. Update KPI Card 4 (Your Connections) to be clickable and active-styled
old_kpi_connections = """            <!-- Your Connections -->
            <div class="col-6 col-lg-3">
                <div class="network-kpi-card h-100">
                    <div class="kpi-icon-box bg-indigo-subtle text-indigo-700">
                        <i class="fas fa-handshake"></i>
                    </div>
                    <div>
                        <div class="kpi-number text-slate-900">{{ connections_count }}</div>
                        <div class="kpi-label text-slate-600">Your Connections</div>
                    </div>
                </div>
            </div>"""

new_kpi_connections = """            <!-- Your Connections -->
            <div class="col-6 col-lg-3">
                <a href="{{ url_for('network', scope='connections') }}" class="network-kpi-card h-100 text-decoration-none {% if selected_scope == 'connections' %}active-kpi-scope{% endif %}" title="Click to filter by only your connections">
                    <div class="kpi-icon-box bg-indigo-subtle text-indigo-700">
                        <i class="fas fa-handshake"></i>
                    </div>
                    <div>
                        <div class="kpi-number text-slate-900">{{ connections_count }}</div>
                        <div class="kpi-label text-slate-600">Your Connections {% if selected_scope == 'connections' %}<i class="fas fa-check-circle text-emerald-600 ms-1"></i>{% endif %}</div>
                    </div>
                </a>
            </div>"""

if old_kpi_connections in content:
    content = content.replace(old_kpi_connections, new_kpi_connections, 1)
    print("KPI connections updated")
else:
    print("KPI connections NOT matched")

# 2. Add Scope Switcher (All Members vs My Connections) and hidden scope input in filter form
old_filter_header = """        <!-- 3. SEARCH & ADVANCED FILTER TOOLBAR -->
        <div class="directory-control-card rounded-4 p-3 p-md-4 mb-4 shadow-sm border bg-white">
            <form method="GET" action="{{ url_for('network') }}" id="networkFilterForm">"""

new_filter_header = """        <!-- 3. SEARCH & ADVANCED FILTER TOOLBAR -->
        <div class="directory-control-card rounded-4 p-3 p-md-4 mb-4 shadow-sm border bg-white">
            <!-- Directory Scope Switcher (All Campus Directory vs My Connections) -->
            <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3 pb-3 border-bottom">
                <div class="d-inline-flex p-1 bg-slate-100 rounded-pill border border-slate-200">
                    <a href="{{ url_for('network', scope='all', role=selected_role, department=selected_dept, location=selected_loc, search=search_query) }}" 
                       class="btn btn-sm rounded-pill px-3.5 py-1.5 fw-bold text-decoration-none {% if selected_scope != 'connections' %}bg-white text-emerald-800 shadow-xs border border-slate-200{% else %}text-slate-600{% endif %}">
                        <i class="fas fa-globe me-1.5 text-emerald-600"></i> All Campus Directory
                    </a>
                    <a href="{{ url_for('network', scope='connections', role=selected_role, department=selected_dept, location=selected_loc, search=search_query) }}" 
                       class="btn btn-sm rounded-pill px-3.5 py-1.5 fw-bold text-decoration-none {% if selected_scope == 'connections' %}bg-white text-emerald-800 shadow-xs border border-slate-200{% else %}text-slate-600{% endif %}">
                        <i class="fas fa-handshake me-1.5 text-indigo-600"></i> My Connections Only ({{ connections_count }})
                    </a>
                </div>
                {% if selected_scope == 'connections' %}
                <span class="badge bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-pill small fw-semibold">
                    <i class="fas fa-filter text-indigo-500 me-1"></i> Filtered by: Accepted Connections
                </span>
                {% else %}
                <span class="badge bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-pill small fw-semibold">
                    <i class="fas fa-users-viewfinder text-emerald-600 me-1"></i> Full Campus Network
                </span>
                {% endif %}
            </div>

            <form method="GET" action="{{ url_for('network') }}" id="networkFilterForm">
                <input type="hidden" name="scope" value="{{ selected_scope or 'all' }}">"""

if old_filter_header in content:
    content = content.replace(old_filter_header, new_filter_header, 1)
    print("Filter header and scope switch updated")
else:
    print("Filter header NOT matched")

# 3. Update Quick Filter Chips to retain scope
old_quick_filter = """                    <a href="{{ url_for('network', role='all', department=selected_dept, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'all' or not selected_role %}active{% endif %}">
                        All ({{ total_count }})
                    </a>
                    <a href="{{ url_for('network', role='student', department=selected_dept, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'student' %}active{% endif %}">
                        <i class="fas fa-user-graduate me-1"></i> Students ({{ students_count }})
                    </a>
                    <a href="{{ url_for('network', role='alumni', department=selected_dept, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'alumni' %}active{% endif %}">
                        <i class="fas fa-user-tie me-1"></i> Alumni ({{ alumni_count }})
                    </a>
                    <a href="{{ url_for('network', role='faculty', department=selected_dept, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'faculty' %}active{% endif %}">
                        <i class="fas fa-chalkboard-user me-1"></i> Faculty ({{ faculty_count }})
                    </a>"""

new_quick_filter = """                    <a href="{{ url_for('network', scope=selected_scope, role='all', department=selected_dept, location=selected_loc, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'all' or not selected_role %}active{% endif %}">
                        All ({{ total_count }})
                    </a>
                    <a href="{{ url_for('network', scope=selected_scope, role='student', department=selected_dept, location=selected_loc, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'student' %}active{% endif %}">
                        <i class="fas fa-user-graduate me-1"></i> Students ({{ students_count }})
                    </a>
                    <a href="{{ url_for('network', scope=selected_scope, role='alumni', department=selected_dept, location=selected_loc, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'alumni' %}active{% endif %}">
                        <i class="fas fa-user-tie me-1"></i> Alumni ({{ alumni_count }})
                    </a>
                    <a href="{{ url_for('network', scope=selected_scope, role='faculty', department=selected_dept, location=selected_loc, search=search_query) }}"
                       class="btn btn-sm filter-pill {% if selected_role == 'faculty' %}active{% endif %}">
                        <i class="fas fa-chalkboard-user me-1"></i> Faculty ({{ faculty_count }})
                    </a>"""

if old_quick_filter in content:
    content = content.replace(old_quick_filter, new_quick_filter, 1)
    print("Quick filter pills updated")
else:
    print("Quick filter pills NOT matched")

# 4. Update section comment
content = content.replace("<!-- 4. REAL MEMBERS DIRECTORY GRID (16 PER PAGE) -->", "<!-- 4. REAL MEMBERS DIRECTORY GRID (MAX 12 PER PAGE) -->")

# 5. Update pagination markup with explicit arrow buttons and scope
old_pagination = """        <!-- 5. PAGINATION (16 ITEMS PER PAGE) -->
        {% if total_pages > 1 %}
        <nav aria-label="Directory pagination" class="my-5">
            <ul class="pagination justify-content-center gap-1">
                <!-- Previous Button -->
                <li class="page-item {% if page <= 1 %}disabled{% endif %}">
                    <a class="page-link rounded-pill px-3"
                       href="{{ url_for('network', page=page-1, search=search_query, role=selected_role, department=selected_dept, location=selected_loc) }}"
                       {% if page <= 1 %}tabindex="-1" aria-disabled="true"{% endif %}>
                        <i class="fas fa-chevron-left me-1"></i> Previous
                    </a>
                </li>

                <!-- Page Numbers -->
                {% for p in range(1, total_pages + 1) %}
                    {% if p == page %}
                    <li class="page-item active" aria-current="page">
                        <span class="page-link rounded-circle">{{ p }}</span>
                    </li>
                    {% elif p <= 3 or p >= total_pages - 2 or (p >= page - 1 and p <= page + 1) %}
                    <li class="page-item">
                        <a class="page-link rounded-circle"
                           href="{{ url_for('network', page=p, search=search_query, role=selected_role, department=selected_dept, location=selected_loc) }}">{{ p }}</a>
                    </li>
                    {% elif p == 4 and page > 5 %}
                    <li class="page-item disabled"><span class="page-link border-0">...</span></li>
                    {% elif p == total_pages - 3 and page < total_pages - 4 %}
                    <li class="page-item disabled"><span class="page-link border-0">...</span></li>
                    {% endif %}
                {% endfor %}

                <!-- Next Button -->
                <li class="page-item {% if page >= total_pages %}disabled{% endif %}">
                    <a class="page-link rounded-pill px-3"
                       href="{{ url_for('network', page=page+1, search=search_query, role=selected_role, department=selected_dept, location=selected_loc) }}"
                       {% if page >= total_pages %}tabindex="-1" aria-disabled="true"{% endif %}>
                        Next <i class="fas fa-chevron-right ms-1"></i>
                    </a>
                </li>
            </ul>
        </nav>
        {% endif %}"""

new_pagination = """        <!-- 5. PAGINATION (MAX 12 ITEMS PER PAGE WITH ARROWS) -->
        {% if total_pages > 1 %}
        <nav aria-label="Directory pagination" class="my-5">
            <ul class="pagination justify-content-center align-items-center gap-1 flex-wrap">
                <!-- Previous Arrow Button -->
                <li class="page-item {% if page <= 1 %}disabled{% endif %}">
                    <a class="page-link rounded-pill px-3.5 py-2 shadow-xs d-inline-flex align-items-center"
                       href="{{ url_for('network', page=page-1, search=search_query, role=selected_role, department=selected_dept, location=selected_loc, scope=selected_scope) }}"
                       {% if page <= 1 %}tabindex="-1" aria-disabled="true"{% endif %} aria-label="Previous Page">
                        <i class="fas fa-arrow-left me-1.5 text-emerald-600"></i> <span class="fw-bold">Prev</span>
                    </a>
                </li>

                <!-- Page Numbers -->
                {% for p in range(1, total_pages + 1) %}
                    {% if p == page %}
                    <li class="page-item active" aria-current="page">
                        <span class="page-link rounded-circle fw-bold">{{ p }}</span>
                    </li>
                    {% elif p <= 3 or p >= total_pages - 2 or (p >= page - 1 and p <= page + 1) %}
                    <li class="page-item">
                        <a class="page-link rounded-circle"
                           href="{{ url_for('network', page=p, search=search_query, role=selected_role, department=selected_dept, location=selected_loc, scope=selected_scope) }}">{{ p }}</a>
                    </li>
                    {% elif p == 4 and page > 5 %}
                    <li class="page-item disabled"><span class="page-link border-0">...</span></li>
                    {% elif p == total_pages - 3 and page < total_pages - 4 %}
                    <li class="page-item disabled"><span class="page-link border-0">...</span></li>
                    {% endif %}
                {% endfor %}

                <!-- Next Arrow Button -->
                <li class="page-item {% if page >= total_pages %}disabled{% endif %}">
                    <a class="page-link rounded-pill px-3.5 py-2 shadow-xs d-inline-flex align-items-center"
                       href="{{ url_for('network', page=page+1, search=search_query, role=selected_role, department=selected_dept, location=selected_loc, scope=selected_scope) }}"
                       {% if page >= total_pages %}tabindex="-1" aria-disabled="true"{% endif %} aria-label="Next Page">
                        <span class="fw-bold">Next</span> <i class="fas fa-arrow-right ms-1.5 text-emerald-600"></i>
                    </a>
                </li>
            </ul>
        </nav>
        {% endif %}"""

if old_pagination in content:
    content = content.replace(old_pagination, new_pagination, 1)
    print("Pagination updated")
else:
    print("Pagination NOT matched")

# 6. Update Empty State to handle both scopes
old_empty_state = """        <!-- EMPTY / ZERO MATCHES STATE -->
        <div class="empty-directory-card text-center py-5 my-4 bg-white rounded-4 border shadow-sm p-4">
            <div class="empty-icon-wrap mx-auto mb-3">
                <i class="fas fa-user-slash fa-3x text-slate-400"></i>
            </div>
            <h4 class="fw-bold text-slate-900 mb-2">No Members Found</h4>
            <p class="text-slate-600 mb-4 max-w-md mx-auto">No registered directory records matched your current search filters.</p>
            <a href="{{ url_for('network') }}" class="btn btn-emerald rounded-pill px-4 py-2 fw-semibold">
                <i class="fas fa-rotate-left me-1"></i> View All Members
            </a>
        </div>"""

new_empty_state = """        <!-- EMPTY / ZERO MATCHES STATE -->
        <div class="empty-directory-card text-center py-5 my-4 bg-white rounded-4 border shadow-sm p-4">
            <div class="empty-icon-wrap mx-auto mb-3">
                {% if selected_scope == 'connections' %}
                <i class="fas fa-user-group fa-2x text-indigo-400"></i>
                {% else %}
                <i class="fas fa-user-slash fa-2x text-slate-400"></i>
                {% endif %}
            </div>
            <h4 class="fw-bold text-slate-900 mb-2">
                {% if selected_scope == 'connections' %}
                No Connected Members Found
                {% else %}
                No Members Found
                {% endif %}
            </h4>
            <p class="text-slate-600 mb-4 max-w-md mx-auto">
                {% if selected_scope == 'connections' %}
                You haven't formed connections yet or none match your current search/filter. Connect with students, alumni, and faculty to build your network!
                {% else %}
                No registered directory records matched your current search filters.
                {% endif %}
            </p>
            <div class="d-flex align-items-center justify-content-center gap-2 flex-wrap">
                {% if selected_scope == 'connections' %}
                <a href="{{ url_for('network', scope='all') }}" class="btn btn-emerald rounded-pill px-4 py-2 fw-bold shadow-xs">
                    <i class="fas fa-globe me-1.5"></i> Browse All Campus Members
                </a>
                {% endif %}
                <a href="{{ url_for('network') }}" class="btn btn-outline-secondary rounded-pill px-4 py-2 fw-semibold">
                    <i class="fas fa-rotate-left me-1.5"></i> Reset All Filters
                </a>
            </div>
        </div>"""

if old_empty_state in content:
    content = content.replace(old_empty_state, new_empty_state, 1)
    print("Empty state updated")
else:
    print("Empty state NOT matched")

# 7. Add extra CSS rules for active-kpi-scope and rounded-pill pagination links
extra_css = """
.network-kpi-card.active-kpi-scope {
    border-color: #059669 !important;
    background: linear-gradient(180deg, #ffffff 0%, #ecfdf5 100%) !important;
    box-shadow: 0 8px 24px -4px rgba(5, 150, 105, 0.22) !important;
    transform: translateY(-2px);
}
.pagination .page-link.rounded-pill {
    width: auto !important;
    min-width: 96px;
    height: 42px;
}
"""

if '/* Real KPI Stats Cards */' in content:
    content = content.replace('/* Real KPI Stats Cards */', '/* Real KPI Stats Cards */' + extra_css, 1)
    print("CSS updated")

with open('templates/student/network.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("FILE SAVED")

