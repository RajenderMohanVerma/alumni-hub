/* ============================================================
   Alumni Hub — shared floating quick-action button (FAB)
   Behaviour for the `quick_fab` macro (templates/common/quick_fab.html):
   tap + to open, tap again / click outside / Escape to close.
   While the page footer (#mainFooter) is on screen the FAB "parks"
   (fades out) so it never covers footer content.
   ============================================================ */
(function () {
    function initFab(container) {
        if (!container || container.dataset.ahFabInit) return;
        container.dataset.ahFabInit = '1';

        var toggle = container.querySelector('[data-ah-fab-toggle]');
        var actions = container.querySelector('.ah-fab-actions');
        if (!toggle || !actions) return;

        function setOpen(open) {
            container.classList.toggle('ah-fab-open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            actions.setAttribute('aria-hidden', open ? 'false' : 'true');
        }

        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            setOpen(!container.classList.contains('ah-fab-open'));
        });
        document.addEventListener('click', function (e) {
            if (container.classList.contains('ah-fab-open') && !container.contains(e.target)) setOpen(false);
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') setOpen(false);
        });
        actions.addEventListener('click', function () { setOpen(false); });

        /* Park the FAB while the footer is on screen so it never covers
           footer content. NOTE: this script can run while the page is
           still parsing (inside the content block), so #mainFooter may
           not exist yet — defer the lookup to DOMContentLoaded when the
           footer is not found immediately. */
        function setupFabPark() {
            var footer = document.getElementById('mainFooter');
            if (footer && 'IntersectionObserver' in window) {
                new IntersectionObserver(function (entries) {
                    var visible = entries[0] && entries[0].isIntersecting;
                    container.classList.toggle('ah-fab-parked', !!visible);
                    if (visible) setOpen(false);
                }, { rootMargin: '0px 0px -40px 0px' }).observe(footer);
            }
        }
        if (document.getElementById('mainFooter')) {
            setupFabPark();
        } else {
            document.addEventListener('DOMContentLoaded', setupFabPark);
        }
    }

    function initAll() {
        var containers = document.querySelectorAll('[data-ah-fab]');
        for (var i = 0; i < containers.length; i++) initFab(containers[i]);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();
