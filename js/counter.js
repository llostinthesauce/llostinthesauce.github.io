(function () {
    document.addEventListener('DOMContentLoaded', function() {
        var countSpan = document.getElementById('hit-counter');
        if (!countSpan) return;
        countSpan.innerHTML = 'VISITOR COUNT: <span style="color: #33CCAA;">8592+</span>';
    });
})();
