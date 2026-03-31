(function () {
    const k = "ut_h42O8JiN5ZFc7BJrafpu2s9fzfR8bY8D1uQg3JNN";
    const offset = 6500;
    fetch(`https://api.counterapi.dev/v1/${k}/first-counter-2997/up`)
        .then(r => r.json())
        .then(d => {
            const countSpan = document.getElementById('hit-count');
            if (countSpan && d.count != null) {
                const total = d.count + offset;
                countSpan.innerText = total.toString().padStart(4, '0');
            }
        })
        .catch(e => console.error('Counter Error:', e));
})();
