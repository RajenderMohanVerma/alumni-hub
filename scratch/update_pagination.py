import os

html_path = r'templates/faculty/dashboard.html'

with open(html_path, 'r', encoding='utf-8') as f:
    c = f.read()

# Target around the end of directoryTabContent
target_str = """                    {% else %}
                    <div class="col-12 text-center py-5">
                        <div class="empty-state-card p-4 rounded-4 bg-white border">
                            <i class="fas fa-chalkboard-teacher fa-3x text-muted mb-3"></i>
                            <h5 class="fw-bold">No Faculty Peers Registered</h5>
                            <p class="text-muted">Colleagues will be displayed here when registered.</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </section>"""

replacement_str = """                    {% else %}
                    <div class="col-12 text-center py-5">
                        <div class="empty-state-card p-4 rounded-4 bg-white border">
                            <i class="fas fa-chalkboard-teacher fa-3x text-muted mb-3"></i>
                            <h5 class="fw-bold">No Faculty Peers Registered</h5>
                            <p class="text-muted">Colleagues will be displayed here when registered.</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Zero Matches State (Filter/Search Empty State) -->
        <div id="zeroMatchesState" class="d-none text-center py-5 my-3">
            <div class="p-4 p-md-5 rounded-4 bg-white border border-slate-200 shadow-sm mx-auto" style="max-width: 520px;">
                <div class="avatar-lg bg-emerald-50 text-emerald-700 rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 64px; height: 64px; font-size: 1.75rem;">
                    <i class="fas fa-user-slash"></i>
                </div>
                <h5 class="fw-bold text-slate-900 mb-1">No Matching Members Found</h5>
                <p class="text-slate-500 small mb-3">Try adjusting your search query, selecting another department filter, or clearing filters.</p>
                <button class="btn btn-sm btn-emerald px-4 py-2 rounded-pill fw-semibold" onclick="resetAllDirectoryFilters()">
                    <i class="fas fa-rotate-left me-1"></i> Reset All Filters
                </button>
            </div>
        </div>

        <!-- Directory Modern Pagination Controls (Max 9 Items per Page) -->
        <div id="directoryPaginationWrap" class="d-flex flex-column flex-md-row justify-content-between align-items-center gap-3 mt-4 pt-3 border-top border-slate-200">
            <!-- Left: Range & Total Counter -->
            <div class="d-flex align-items-center gap-2 flex-wrap justify-content-center">
                <span class="badge bg-white text-slate-700 border border-slate-200 px-3 py-2 rounded-pill shadow-xs small" id="paginationInfoText">
                    <i class="fas fa-users-viewfinder text-emerald-600 me-1"></i> Showing <strong id="pageRangeText">1 - 9</strong> of <strong id="pageTotalCount">0</strong> members
                </span>
                <span class="badge bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1.5 rounded-pill small fw-semibold" id="pageNumberIndicator">
                    Page 1 / 1
                </span>
            </div>

            <!-- Right: Interactive Prev / Page Numbers / Next Navigation -->
            <nav aria-label="Directory Navigation" class="d-flex align-items-center gap-1 flex-wrap justify-content-center" id="paginationNav">
                <button type="button" class="btn btn-sm btn-pagination-nav" id="prevPageBtn" onclick="changeDirectoryPage(-1)" aria-label="Previous Page">
                    <i class="fas fa-chevron-left me-1"></i> <span>Prev</span>
                </button>

                <div class="d-flex align-items-center gap-1" id="paginationNumbersList">
                    <!-- Dynamic page numbers injected here -->
                </div>

                <button type="button" class="btn btn-sm btn-pagination-nav" id="nextPageBtn" onclick="changeDirectoryPage(1)" aria-label="Next Page">
                    <span>Next</span> <i class="fas fa-chevron-right ms-1"></i>
                </button>
            </nav>
        </div>
    </section>"""

if target_str in c:
    c = c.replace(target_str, replacement_str, 1)
    print("Markup replaced successfully.")
else:
    print("Could not find markup target_str.")

# 2. Add CSS for Pagination & Cards
css_target = "/* ----------------------------------------------------\n   FACULTY DASHBOARD MODERN STYLESHEET\n   ---------------------------------------------------- */"
css_addition = """/* ----------------------------------------------------
   FACULTY DASHBOARD MODERN STYLESHEET
   ---------------------------------------------------- */

/* Modern Directory Pagination Bar */
#directoryPaginationWrap {
    transition: all 0.3s ease;
}

.btn-pagination-nav {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 38px;
    padding: 0.38rem 0.95rem;
    font-size: 0.85rem;
    font-weight: 700;
    color: #0f172a;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 9999px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
}

.btn-pagination-nav:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #94a3b8;
    color: #047857;
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}

.btn-pagination-nav:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    background: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}

.pagination-num-btn {
    min-width: 38px;
    height: 38px;
    padding: 0 0.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    color: #334155;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 9999px;
    transition: all 0.2s ease;
    cursor: pointer;
}

.pagination-num-btn:hover {
    background: #ecfdf5;
    border-color: #a7f3d0;
    color: #065f46;
}

.pagination-num-btn.active {
    background: linear-gradient(135deg, #064e3b 0%, #047857 100%) !important;
    border-color: #047857 !important;
    color: #ffffff !important;
    box-shadow: 0 3px 10px rgba(4, 120, 87, 0.3) !important;
}

@media (max-width: 576px) {
    #directoryPaginationWrap {
        flex-direction: column !important;
        align-items: stretch !important;
        text-align: center;
    }
    #paginationNav {
        justify-content: center;
        width: 100%;
    }
    .btn-pagination-nav {
        flex: 1;
        min-height: 42px;
    }
}
"""

if css_target in c:
    c = c.replace(css_target, css_addition, 1)
    print("CSS replaced successfully.")
else:
    print("Could not find css_target.")

# 3. Update JavaScript logic for Pagination & Filtering
js_target = """    // 3. Global Directory Live Search & Professional Filters
    const searchInput = document.getElementById('globalDirectorySearch');
    const clearBtn = document.getElementById('clearSearchBtn');
    const resetBtn = document.getElementById('resetDirectoryFiltersBtn');
    const liveMatchBadge = document.getElementById('liveMatchCountBadge');
    let currentDeptFilter = 'all';

    function getActiveRoleName() {
        const activeTab = document.querySelector('#directoryTabs .nav-link.active');
        if (!activeTab) return 'Members';
        if (activeTab.id === 'tab-student') return 'Students';
        if (activeTab.id === 'tab-alumni') return 'Alumni';
        if (activeTab.id === 'tab-faculty') return 'Faculty Peers';
        return 'Members';
    }

    function applyDirectoryFilters() {
        const query = (searchInput ? (searchInput.value || '').trim().toLowerCase() : '');
        if (clearBtn) {
            clearBtn.classList.toggle('d-none', query.length === 0);
        }

        const isFiltered = (query.length > 0 || currentDeptFilter !== 'all');
        if (resetBtn) {
            resetBtn.classList.toggle('d-none', !isFiltered);
        }

        const activePane = document.querySelector('.tab-pane.active');
        if (!activePane) return;

        const items = activePane.querySelectorAll('.user-item');
        let visibleCount = 0;
        const totalInPane = items.length;

        items.forEach(item => {
            const searchData = (item.getAttribute('data-search') || '').toLowerCase();
            const deptData = (item.getAttribute('data-dept') || '').toLowerCase();

            const matchesQuery = query === '' || searchData.includes(query);
            const matchesDept = currentDeptFilter === 'all' || deptData.includes(currentDeptFilter);

            if (matchesQuery && matchesDept) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        // Update live match badge with clear count
        if (liveMatchBadge) {
            const roleName = getActiveRoleName();
            if (!isFiltered) {
                liveMatchBadge.innerHTML = `<i class="fas fa-check-circle me-1 text-emerald-600"></i> Showing All ${visibleCount} ${roleName}`;
            } else {
                liveMatchBadge.innerHTML = `<i class="fas fa-filter me-1 text-emerald-600"></i> Showing ${visibleCount} of ${totalInPane} ${roleName}`;
            }
        }

        // Toggle zero state
        const zeroState = document.getElementById('zeroMatchesState');
        if (zeroState) {
            zeroState.classList.toggle('d-none', visibleCount > 0);
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', applyDirectoryFilters);
    }

    // Department quick-filter pills
    const deptPills = document.querySelectorAll('.filter-pill');
    deptPills.forEach(pill => {
        pill.addEventListener('click', function () {
            deptPills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            currentDeptFilter = this.getAttribute('data-dept') || 'all';
            applyDirectoryFilters();
        });
    });

    // Reapply on tab switch
    const tabs = document.querySelectorAll('button[data-bs-toggle="pill"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', applyDirectoryFilters);
    });

    // Global reset function
    window.resetAllDirectoryFilters = function() {
        if (searchInput) searchInput.value = '';
        currentDeptFilter = 'all';
        deptPills.forEach(p => {
            if (p.getAttribute('data-dept') === 'all') p.classList.add('active');
            else p.classList.remove('active');
        });
        applyDirectoryFilters();
        if (searchInput) searchInput.focus();
    };"""

js_replacement = """    // 3. Global Directory Live Search, Professional Filters & 9-Item Pagination
    const PER_PAGE = 9;
    let currentPage = 1;
    let currentMatchedItems = [];

    const searchInput = document.getElementById('globalDirectorySearch');
    const clearBtn = document.getElementById('clearSearchBtn');
    const resetBtn = document.getElementById('resetDirectoryFiltersBtn');
    const liveMatchBadge = document.getElementById('liveMatchCountBadge');
    let currentDeptFilter = 'all';

    function getActiveRoleName() {
        const activeTab = document.querySelector('#directoryTabs .nav-link.active');
        if (!activeTab) return 'Members';
        if (activeTab.id === 'tab-student') return 'Students';
        if (activeTab.id === 'tab-alumni') return 'Alumni';
        if (activeTab.id === 'tab-faculty') return 'Faculty Peers';
        return 'Members';
    }

    function renderCurrentPageItems(shouldScroll = false) {
        const activePane = document.querySelector('.tab-pane.active');
        if (!activePane) return;

        const allItems = activePane.querySelectorAll('.user-item');
        allItems.forEach(item => item.style.display = 'none');

        const totalCount = currentMatchedItems.length;
        const totalPages = Math.ceil(totalCount / PER_PAGE) || 1;

        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;

        const startIndex = (currentPage - 1) * PER_PAGE;
        const endIndex = Math.min(startIndex + PER_PAGE, totalCount);

        for (let i = startIndex; i < endIndex; i++) {
            currentMatchedItems[i].style.display = '';
        }

        // Update range & counters
        const pageRangeText = document.getElementById('pageRangeText');
        const pageTotalCount = document.getElementById('pageTotalCount');
        const pageNumberIndicator = document.getElementById('pageNumberIndicator');
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        const numbersList = document.getElementById('paginationNumbersList');
        const paginationWrap = document.getElementById('directoryPaginationWrap');

        if (pageRangeText) {
            pageRangeText.textContent = totalCount > 0 ? `${startIndex + 1} - ${endIndex}` : '0 - 0';
        }
        if (pageTotalCount) {
            pageTotalCount.textContent = totalCount;
        }
        if (pageNumberIndicator) {
            pageNumberIndicator.textContent = `Page ${currentPage} / ${totalPages}`;
        }

        // Prev & Next Buttons state
        if (prevPageBtn) prevPageBtn.disabled = (currentPage <= 1 || totalCount === 0);
        if (nextPageBtn) nextPageBtn.disabled = (currentPage >= totalPages || totalCount === 0);

        // Generate Numeric Page Buttons
        if (numbersList) {
            numbersList.innerHTML = '';
            if (totalPages > 1) {
                let startP = Math.max(1, currentPage - 2);
                let endP = Math.min(totalPages, currentPage + 2);

                if (currentPage <= 3) {
                    endP = Math.min(totalPages, 5);
                }
                if (currentPage >= totalPages - 2) {
                    startP = Math.max(1, totalPages - 4);
                }

                for (let p = startP; p <= endP; p++) {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'pagination-num-btn' + (p === currentPage ? ' active' : '');
                    btn.textContent = p;
                    btn.onclick = (function(targetPage) {
                        return function() {
                            currentPage = targetPage;
                            renderCurrentPageItems(true);
                        };
                    })(p);
                    numbersList.appendChild(btn);
                }
            }
        }

        // Toggle pagination visibility if zero items
        if (paginationWrap) {
            paginationWrap.classList.toggle('d-none', totalCount === 0);
        }

        // Optional smooth scroll to directory top when user clicks next/prev
        if (shouldScroll) {
            const dirHeader = document.getElementById('directorySection');
            if (dirHeader) {
                const headerRect = dirHeader.getBoundingClientRect();
                if (headerRect.top < 0 || headerRect.top > 200) {
                    dirHeader.scrollIntoView({ behavior: 'smooth' });
                }
            }
        }
    }

    window.changeDirectoryPage = function(delta) {
        const totalPages = Math.ceil(currentMatchedItems.length / PER_PAGE) || 1;
        const newPage = currentPage + delta;
        if (newPage >= 1 && newPage <= totalPages) {
            currentPage = newPage;
            renderCurrentPageItems(true);
        }
    };

    function applyDirectoryFilters() {
        const query = (searchInput ? (searchInput.value || '').trim().toLowerCase() : '');
        if (clearBtn) {
            clearBtn.classList.toggle('d-none', query.length === 0);
        }

        const isFiltered = (query.length > 0 || currentDeptFilter !== 'all');
        if (resetBtn) {
            resetBtn.classList.toggle('d-none', !isFiltered);
        }

        const activePane = document.querySelector('.tab-pane.active');
        if (!activePane) return;

        const items = Array.from(activePane.querySelectorAll('.user-item'));
        currentMatchedItems = [];
        const totalInPane = items.length;

        items.forEach(item => {
            const searchData = (item.getAttribute('data-search') || '').toLowerCase();
            const deptData = (item.getAttribute('data-dept') || '').toLowerCase();

            const matchesQuery = query === '' || searchData.includes(query);
            const matchesDept = currentDeptFilter === 'all' || deptData.includes(currentDeptFilter);

            if (matchesQuery && matchesDept) {
                currentMatchedItems.push(item);
            }
        });

        const visibleCount = currentMatchedItems.length;

        // Reset page to 1 when filters or query change
        currentPage = 1;
        renderCurrentPageItems(false);

        // Update live match badge with clear count
        if (liveMatchBadge) {
            const roleName = getActiveRoleName();
            if (!isFiltered) {
                liveMatchBadge.innerHTML = `<i class="fas fa-check-circle me-1 text-emerald-600"></i> Showing All ${visibleCount} ${roleName}`;
            } else {
                liveMatchBadge.innerHTML = `<i class="fas fa-filter me-1 text-emerald-600"></i> Showing ${visibleCount} of ${totalInPane} ${roleName}`;
            }
        }

        // Toggle zero state
        const zeroState = document.getElementById('zeroMatchesState');
        if (zeroState) {
            zeroState.classList.toggle('d-none', visibleCount > 0);
        }
    }

    if (searchInput) {
        // Debounce search slightly for optimal performance
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(applyDirectoryFilters, 120);
        });
    }

    // Department quick-filter pills
    const deptPills = document.querySelectorAll('.filter-pill');
    deptPills.forEach(pill => {
        pill.addEventListener('click', function () {
            deptPills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            currentDeptFilter = this.getAttribute('data-dept') || 'all';
            applyDirectoryFilters();
        });
    });

    // Reapply on tab switch
    const tabs = document.querySelectorAll('button[data-bs-toggle="pill"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function() {
            applyDirectoryFilters();
        });
    });

    // Global reset function
    window.resetAllDirectoryFilters = function() {
        if (searchInput) searchInput.value = '';
        currentDeptFilter = 'all';
        deptPills.forEach(p => {
            if (p.getAttribute('data-dept') === 'all') p.classList.add('active');
            else p.classList.remove('active');
        });
        applyDirectoryFilters();
        if (searchInput) searchInput.focus();
    };

    // Initial page load pagination & filter run
    setTimeout(applyDirectoryFilters, 50);"""

if js_target in c:
    c = c.replace(js_target, js_replacement, 1)
    print("JS replaced successfully.")
else:
    print("Could not find js_target.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Finished writing to dashboard.html")

