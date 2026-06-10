(function () {
    var namespace = 'ut_h42O8JiN5ZFc7BJrafpu2s9fzfR8bY8D1uQg3JNN';
    var counterName = 'first-counter-2997';
    var offset = 9000;
    var base = 'https://api.counterapi.dev/v1/' + namespace + '/' + counterName;
    var CACHE_KEY = 'nuBlogCounterCache';
    // Increment once per browser session ("/up"), then read-only fetches,
    // so the number approximates visitors instead of raw page views.
    var SESSION_KEY = 'nuBlogCounted';

    function readCachedTotal() {
        try {
            var raw = localStorage.getItem(CACHE_KEY);
            if (!raw) return null;
            var total = JSON.parse(raw).total;
            return Number.isFinite(total) ? total : null;
        } catch (_) { return null; }
    }

    function writeCachedTotal(total) {
        try {
            localStorage.setItem(CACHE_KEY, JSON.stringify({ total: total, ts: Date.now() }));
        } catch (_) { /* private mode / quota: ignore */ }
    }

    function paint(span, label) {
        while (span.firstChild) span.removeChild(span.firstChild);
        span.appendChild(document.createTextNode('VISITOR COUNT: '));
        var inner = document.createElement('span');
        inner.style.color = '#33CCAA';
        inner.textContent = label;
        span.appendChild(inner);
    }

    function initCounter() {
        var span = document.getElementById('hit-counter');
        if (!span) return;

        // Optimistic paint from cache so return visitors never see "loading..." or "unavailable" during transient failures.
        var cached = readCachedTotal();
        if (cached !== null) paint(span, cached + '+');

        var endpoint = base + '/';
        try {
            if (!sessionStorage.getItem(SESSION_KEY)) {
                // Flag before the request so parallel tabs don't double-count;
                // worst case a failed request costs one missed increment.
                sessionStorage.setItem(SESSION_KEY, 'true');
                endpoint = base + '/up';
            }
        } catch (_) { /* private mode: stay read-only */ }

        fetch(endpoint, { cache: 'no-store' })
            .then(function (resp) {
                if (!resp.ok) throw new Error('Counter request failed: ' + resp.status);
                return resp.json();
            })
            .then(function (result) {
                var total = Number(result.count) + offset;
                if (!Number.isFinite(total)) throw new Error('Counter returned a non-numeric value');
                paint(span, total + '+');
                writeCachedTotal(total);
            })
            .catch(function (err) {
                console.error('Counter Error:', err);
                if (cached === null) paint(span, 'unavailable');
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCounter);
    } else {
        initCounter();
    }
})();
