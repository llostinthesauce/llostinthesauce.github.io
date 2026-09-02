(function () {
    var widgets = document.querySelector('.goodreads-widgets');
    if (!widgets) return;
    var prepared = new WeakSet();

    function trimArchive(selector) {
        var oldestReview = widgets.dataset.oldestReview;
        if (!oldestReview) return;
        var entries = Array.from(widgets.querySelectorAll(selector));
        var boundary = entries.findIndex(function (entry) {
            return entry.querySelector('a[href*="/review/show/' + oldestReview + '?"]') ||
                entry.querySelector('a[href$="/review/show/' + oldestReview + '"]');
        });
        // Keep the original archive boundary even as new books enter the feed.
        if (boundary >= 0) entries.slice(boundary + 1).forEach(function (entry) { entry.remove(); });
    }

    function prepareImages() {
        widgets.querySelectorAll('img').forEach(function (img) {
            if (prepared.has(img)) return;
            prepared.add(img);
            img.loading = 'lazy';
            img.decoding = 'async';
            if (!img.hasAttribute('alt')) img.alt = '';

            function setDimensions() {
                if (!img.naturalWidth || !img.naturalHeight) return;
                img.width = img.naturalWidth;
                img.height = img.naturalHeight;
            }
            if (img.naturalWidth) setDimensions();
            else img.addEventListener('load', setDimensions, { once: true });
        });
    }

    function prepareWidgets() {
        trimArchive('[class^="gr_custom_each_container_"]');
        trimArchive('.gr_grid_book_container');
        prepareImages();
    }

    // Goodreads replaces its fallback HTML after its feed arrives.
    new MutationObserver(prepareWidgets).observe(widgets, { childList: true, subtree: true });
    prepareWidgets();
})();
