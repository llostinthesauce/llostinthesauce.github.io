// Click-to-load YouTube embeds. Pages render <a class="lite-yt" data-yt-id="...">
// facades (thumbnail + play button); clicking swaps in the real iframe with
// autoplay. Without JS the facade is a plain link to the video on YouTube.
//
// Facades browse in a normal grid, so the swapped-in player would inherit a
// one-column-wide box. The grid cell gets .is-playing on swap and the page
// spans it across the row, which is what makes a 300px card playable.
(function () {
    document.addEventListener('click', function (e) {
        var facade = e.target.closest('a.lite-yt');
        if (!facade) return;
        e.preventDefault();

        var iframe = document.createElement('iframe');
        iframe.className = 'youtube-embed';
        iframe.src = 'https://www.youtube-nocookie.com/embed/' +
            facade.dataset.ytId + '?autoplay=1';
        iframe.title = facade.title;
        iframe.loading = 'lazy';
        iframe.allow = 'accelerometer; autoplay; clipboard-write; ' +
            'encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        var cell = facade.closest('.gallery-grid-item');
        if (cell) cell.classList.add('is-playing');
        facade.replaceWith(iframe);
    });
})();
