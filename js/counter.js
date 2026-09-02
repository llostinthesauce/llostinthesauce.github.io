(function () {
    var goatCounterEndpoint = 'https://badcovers.goatcounter.com/count';
    var totalEndpoint = 'https://badcovers.goatcounter.com/counter/TOTAL.json';
    var legacyOffset = 11028;
    var trackerSource = 'https://gc.zgo.at/count.js';
    var CACHE_KEY = 'nuBlogCounterCache';
    var REQUEST_TIMEOUT = 8000;

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

    function loadTracker() {
        if (document.querySelector('script[data-goatcounter]')) return;

        var tracker = document.createElement('script');
        tracker.setAttribute('data-goatcounter', goatCounterEndpoint);
        tracker.async = true;
        tracker.src = trackerSource;
        document.head.appendChild(tracker);
    }

    function parseCount(value) {
        var digits = String(value).trim();
        if (!/^\d+(?:,\d{3})*$/.test(digits)) return NaN;
        var count = Number(digits.replace(/,/g, ''));
        return Number.isSafeInteger(count) ? count : NaN;
    }

    function initCounter() {
        var span = document.getElementById('hit-counter');
        if (!span) return;

        var cached = readCachedTotal();
        paint(span, cached !== null ? cached + '+' : 'loading...');

        loadTracker();

        var controller = new AbortController();
        var timer;
        var deadline = new Promise(function (_, reject) {
            timer = setTimeout(function () {
                controller.abort();
                reject(new Error('Counter request timed out'));
            }, REQUEST_TIMEOUT);
        });
        var request = fetch(totalEndpoint, { cache: 'no-store', signal: controller.signal })
            .then(function (resp) {
                if (!resp.ok) throw new Error('Counter request failed: ' + resp.status);
                return resp.json();
            });

        Promise.race([request, deadline])
            .then(function (result) {
                var total = parseCount(result.count) + legacyOffset;
                if (!Number.isFinite(total)) throw new Error('Counter returned a non-numeric value');
                paint(span, total + '+');
                writeCachedTotal(total);
            })
            .catch(function (err) {
                console.error('Counter Error:', err);
                if (cached === null) paint(span, 'unavailable');
            })
            .finally(function () {
                clearTimeout(timer);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCounter);
    } else {
        initCounter();
    }
})();
