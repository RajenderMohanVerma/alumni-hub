with open('templates/faculty/dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_needle = """                <button type="button" class="btn btn-sm btn-pagination-nav" id="prevPageBtn" onclick="changeDirectoryPage(-1)" aria-label="Previous Page">
                    <i class="fas fa-chevron-left me-1"></i> <span>Prev</span>
                </button>

                <div class="d-flex align-items-center gap-1" id="paginationNumbersList">
                    <!-- Dynamic page numbers injected here -->
                </div>

                <button type="button" class="btn btn-sm btn-pagination-nav" id="nextPageBtn" onclick="changeDirectoryPage(1)" aria-label="Next Page">
                    <span>Next</span> <i class="fas fa-chevron-right ms-1"></i>
                </button>"""

new_needle = """                <button type="button" class="btn btn-sm btn-pagination-nav shadow-xs" id="prevPageBtn" onclick="changeDirectoryPage(-1)" aria-label="Previous Page">
                    <i class="fas fa-arrow-left me-1.5 text-emerald-600"></i> <span class="fw-bold">Prev</span>
                </button>

                <div class="d-flex align-items-center gap-1" id="paginationNumbersList">
                    <!-- Dynamic page numbers injected here -->
                </div>

                <button type="button" class="btn btn-sm btn-pagination-nav shadow-xs" id="nextPageBtn" onclick="changeDirectoryPage(1)" aria-label="Next Page">
                    <span class="fw-bold">Next</span> <i class="fas fa-arrow-right ms-1.5 text-emerald-600"></i>
                </button>"""

# Normalize CRLF and LF
c_norm = c.replace('\r\n', '\n')
old_norm = old_needle.replace('\r\n', '\n')
new_norm = new_needle.replace('\r\n', '\n')

if old_norm in c_norm:
    c_norm = c_norm.replace(old_norm, new_norm, 1)
    with open('templates/faculty/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(c_norm)
    print("SUCCESS")
else:
    print("NOT FOUND")

