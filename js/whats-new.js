// whats-new.js — decides which card wears the '*new!' badge.
//
// Markup contract:
//   <div class="camera-preview-row" data-new-scope>
//       <a class="big-link-box" data-added="2026-05">...</a>
//
// Within each [data-new-scope] container, the single newest [data-added] gets
// .is-new — but only while it is still inside FRESH_DAYS. Once it ages out the
// badge disappears on its own, with no edit and no rebuild, so a quiet section
// simply stops advertising itself instead of flagging a year-old card forever.
//
// data-added accepts YYYY-MM or YYYY-MM-DD. YYYY-MM counts from the 1st, which
// errs toward expiring sooner.

(function () {
    'use strict';

    var FRESH_DAYS = 90;
    var DAY_MS = 24 * 60 * 60 * 1000;

    function parseAdded(value) {
        if (!value) return null;
        var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(value.trim());
        if (!m) return null;
        var year = Number(m[1]);
        var month = Number(m[2]);
        var day = m[3] ? Number(m[3]) : 1;
        if (month < 1 || month > 12 || day < 1 || day > 31) return null;
        var date = new Date(year, month - 1, day);
        return isNaN(date.getTime()) ? null : date;
    }

    function applyNewBadges(root) {
        var scope = root || document;
        var containers = scope.querySelectorAll('[data-new-scope]');

        Array.prototype.forEach.call(containers, function (container) {
            // data-new-count="2" on the scope badges the two newest dates
            // (blog.html does); the default is one.
            var wanted = Number(container.getAttribute('data-new-count')) || 1;
            var dated = [];

            Array.prototype.forEach.call(container.querySelectorAll('[data-added]'), function (el) {
                el.classList.remove('is-new');
                var date = parseAdded(el.getAttribute('data-added'));
                if (date) dated.push({ el: el, time: date.getTime() });
            });
            if (!dated.length) return;

            var times = dated.map(function (item) { return item.time; });
            var fresh = times
                .filter(function (time, index) { return times.indexOf(time) === index; })
                .sort(function (a, b) { return b - a; })
                .slice(0, wanted)
                .filter(function (time) { return (Date.now() - time) / DAY_MS <= FRESH_DAYS; });

            dated.forEach(function (item) {
                if (fresh.indexOf(item.time) !== -1) item.el.classList.add('is-new');
            });
        });
    }

    // exported so gallery.js can re-run it after it renders its cards
    window.nublogApplyNewBadges = applyNewBadges;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            applyNewBadges();
        });
    } else {
        applyNewBadges();
    }
})();
