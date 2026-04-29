(function () {
    const counter = new Counter({ 
        workspace: 'ut_h42O8JiN5ZFc7BJrafpu2s9fzfR8bY8D1uQg3JNN' 
    });
    const offset = 6500;

    document.addEventListener('DOMContentLoaded', function() {
        const countSpan = document.getElementById('hit-counter');
        if (!countSpan) return;

        counter.up('first-counter-2997')
            .then(result => {
                const total = result.value + offset;
                countSpan.innerText = total.toString().padStart(4, '0');
            })
            .catch(e => console.error('Counter Error:', e));
    });
})();
