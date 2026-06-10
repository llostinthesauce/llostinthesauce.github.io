(function () {
    var pathname = window.location.pathname;
    if (!/\/blog\/[^/]+\.html$/.test(pathname)) return;

    var currentFile = pathname.split('/').pop();
    // AUTOGEN-START blogPosts — populated by scripts/build-sitemap.py
    var blogPosts = [
        "2026-04-23-field-notes-march-30-april-8.html",
        "2026-03-29-untitled.html",
        "2025-12-01-aoip.html",
        "2025-11-09-please-for-the-love-of-god-slow-down-and-run-them-offline.html",
        "2025-10-17-some-rambling-thoughts-on-ai.html",
        "2025-09-30-gap.html",
        "2025-09-12-what-the-labubu.html",
        "2025-09-07-300.html",
        "2025-09-05-perpetuity.html",
        "2025-08-28-a-scruple-scruples.html",
        "2025-06-04-regeneration.html",
        "2025-05-15-review-nausea-plus-other.html",
        "2025-03-27-nature-being-paradoxical.html",
        "2024-12-31-m-c-t.html",
        "2023-08-04-fiction-airplane.html",
        "2021-09-02-five-essays-from-phil1000.html",
        "2021-04-28-final-project-for-fintech-2021.html",
        "2015-06-16-e-mail-to-myself-2015.html"
    ];
    // AUTOGEN-END blogPosts

    var currentIndex = blogPosts.indexOf(currentFile);
    if (currentIndex === -1) return;

    var backLink = document.querySelector('a.back-link');
    if (!backLink) return;

    var base = (window.nublogBase != null) ? window.nublogBase : '..';

    backLink.innerHTML = '\u2190 back to blog';
    backLink.href = base + '/blog.html';

    // blogPosts is newest-first, so index+1 is the chronologically older post.
    var olderIndex = currentIndex + 1;
    if (olderIndex < blogPosts.length) {
        var sep = document.createTextNode('\u00a0\u00a0\u00a0\u00a0');
        var olderLink = document.createElement('a');
        olderLink.href = blogPosts[olderIndex];
        olderLink.style.cssText = 'color:#99CCCC;font-style:italic;text-decoration:underline;font-size:1em;';
        olderLink.textContent = 'older \u2192';
        backLink.after(sep, olderLink);
    }
})();
