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
            var candidates = container.querySelectorAll('[data-added]');
            var newest = null;
            var newestDate = null;

            Array.prototype.forEach.call(candidates, function (el) {
                el.classList.remove('is-new');
                var date = parseAdded(el.getAttribute('data-added'));
                if (!date) return;
                if (!newestDate || date > newestDate) {
                    newestDate = date;
                    newest = el;
                }
            });

            if (!newest) return;
            var ageDays = (Date.now() - newestDate.getTime()) / DAY_MS;
            if (ageDays <= FRESH_DAYS) newest.classList.add('is-new');
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
