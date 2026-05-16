(function () {
    var namespace = 'ut_h42O8JiN5ZFc7BJrafpu2s9fzfR8bY8D1uQg3JNN';
    var counterName = 'first-counter-2997';
    var offset = 9000;
    var endpoint = 'https://api.counterapi.dev/v1/' + namespace + '/' + counterName + '/up';

    function renderCount(countSpan, count) {
        var total = Number(count) + offset;
        if (!Number.isFinite(total)) throw new Error('Counter returned a non-numeric value');
        countSpan.innerHTML = 'VISITOR COUNT: <span style="color: #33CCAA;">' + total + '+</span>';
    }

    function initCounter() {
        var countSpan = document.getElementById('hit-counter');
        if (!countSpan) return;

        fetch(endpoint, { cache: 'no-store' })
            .then(function(resp) {
                if (!resp.ok) throw new Error('Counter request failed: ' + resp.status);
                return resp.json();
            })
            .then(function(result) {
                renderCount(countSpan, result.count);
            })
            .catch(function(err) {
                console.error('Counter Error:', err);
                countSpan.innerHTML = 'VISITOR COUNT: <span style="color: #33CCAA;">unavailable</span>';
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCounter);
    } else {
        initCounter();
    }
})();
