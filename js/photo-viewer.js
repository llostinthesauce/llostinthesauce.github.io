/* Photo viewer — click a photo, see the whole thing.
 *
 * Grids show an 800px copy in a small cell; the build wraps every grid photo
 * in <a class="gallery-photo" href="original">, so without JavaScript (or with
 * cmd/ctrl/middle-click) a photo still opens full size in its own tab. A plain
 * click opens it here instead: fitted to the screen, arrows / swipe to move
 * through the grid, Esc or back to close, and a link out to the original.
 *
 * Photos inside a post (either theme) get the same viewer, one at a time.
 * Loaded by js/include.js only on pages that have something to view.
 */
(function () {
    // Post images below this width are icons and badges, not photos.
    var MIN_POST_WIDTH = 480;
    var SWIPE_DISTANCE = 50;

    function postPhotos(post) {
        return Array.prototype.filter.call(post.querySelectorAll('img'), function (img) {
            if (img.closest('a, .gallery-grid-item, .goodreads-widgets, .spec-box')) return false;
            var width = parseInt(img.getAttribute('width'), 10) || img.naturalWidth;
            return width >= MIN_POST_WIDTH;
        });
    }

    // Each entry: { img, href } — the element that was clicked and the full-size URL.
    function galleryEntries(grid) {
        return Array.prototype.map.call(grid.querySelectorAll('a.gallery-photo'), function (link) {
            return { trigger: link, img: link.querySelector('img'), href: link.href };
        });
    }

    function caption(img) {
        var item = img.closest('.gallery-grid-item');
        var text = item && item.querySelector('p');
        if (text && text.textContent.trim()) return text.textContent.trim();
        var figure = img.closest('figure');
        var figcaption = figure && figure.querySelector('figcaption');
        if (figcaption && figcaption.textContent.trim()) return figcaption.textContent.trim();
        return '';
    }

    function button(className, label, text) {
        var node = document.createElement('button');
        node.type = 'button';
        node.className = className;
        node.setAttribute('aria-label', label);
        node.textContent = text;
        return node;
    }

    // ---- the dialog, built once ------------------------------------------
    var dialog = document.createElement('dialog');
    dialog.className = 'photo-viewer';
    dialog.setAttribute('aria-label', 'photo viewer');

    var stage = document.createElement('figure');
    stage.className = 'photo-viewer-stage';
    var image = document.createElement('img');
    image.className = 'photo-viewer-image';
    image.alt = '';
    var figcaption = document.createElement('figcaption');
    figcaption.className = 'photo-viewer-caption';
    stage.appendChild(image);
    stage.appendChild(figcaption);

    var close = button('photo-viewer-close', 'close', '×');
    var prev = button('photo-viewer-prev', 'previous photo', '‹');
    var next = button('photo-viewer-next', 'next photo', '›');

    var bar = document.createElement('div');
    bar.className = 'photo-viewer-bar';
    var count = document.createElement('span');
    count.className = 'photo-viewer-count';
    var original = document.createElement('a');
    original.className = 'photo-viewer-original';
    original.target = '_blank';
    original.rel = 'noopener';
    original.textContent = 'open original ↗';
    bar.appendChild(count);
    bar.appendChild(original);

    dialog.appendChild(stage);
    dialog.appendChild(prev);
    dialog.appendChild(next);
    dialog.appendChild(close);
    dialog.appendChild(bar);
    document.body.appendChild(dialog);

    var entries = [];
    var index = 0;
    var pushedState = false;
    var loadToken = 0;

    function show(at) {
        index = (at + entries.length) % entries.length;
        var entry = entries[index];
        var token = ++loadToken;

        // Start from what the grid already downloaded, then swap in the
        // original once it arrives, so the viewer never opens on a blank.
        image.src = entry.img.currentSrc || entry.img.src;
        image.alt = entry.img.alt || '';
        dialog.classList.add('is-loading');
        var full = new Image();
        full.onload = function () {
            if (token !== loadToken) return;
            image.src = entry.href;
            dialog.classList.remove('is-loading');
        };
        full.onerror = function () {
            if (token === loadToken) dialog.classList.remove('is-loading');
        };
        full.src = entry.href;

        var text = caption(entry.img);
        figcaption.textContent = text;
        figcaption.hidden = !text;
        original.href = entry.href;
        var many = entries.length > 1;
        count.textContent = many ? (index + 1) + ' / ' + entries.length : '';
        prev.hidden = next.hidden = !many;

        // Warm the next one so arrowing forward feels instant.
        if (many) new Image().src = entries[(index + 1) % entries.length].href;
    }

    function open(list, at) {
        entries = list;
        show(at);
        if (!dialog.open) {
            dialog.showModal();
            document.documentElement.classList.add('photo-viewer-open');
            // One history entry, so the back button (or gesture) closes the
            // viewer instead of leaving the page.
            try {
                history.pushState({ photoViewer: true }, '');
                pushedState = true;
            } catch (_) { pushedState = false; }
        }
    }

    // Every way out (button, Esc, backdrop, back) ends here, including the
    // forced close a browser does on a repeated Esc.
    dialog.addEventListener('close', function () {
        document.documentElement.classList.remove('photo-viewer-open');
        loadToken++;
        if (pushedState) {
            pushedState = false;
            history.back(); // drop the entry open() pushed
        }
    });

    window.addEventListener('popstate', function () {
        if (!dialog.open) return;
        pushedState = false; // the back button already took the entry
        dialog.close();
    });

    function requestClose() { dialog.close(); }

    close.addEventListener('click', requestClose);
    prev.addEventListener('click', function () { show(index - 1); });
    next.addEventListener('click', function () { show(index + 1); });

    // Clicking the dark space around the photo closes it (not the tail of a swipe).
    var swiped = false;
    dialog.addEventListener('click', function (event) {
        if (swiped) { swiped = false; return; }
        if (event.target === dialog || event.target === stage) requestClose();
    });
    dialog.addEventListener('keydown', function (event) {
        if (entries.length < 2) return;
        if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
        if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
    });

    var swipeX = null;
    dialog.addEventListener('pointerdown', function (event) {
        if (event.pointerType !== 'mouse') swipeX = event.clientX;
    });
    dialog.addEventListener('pointerup', function (event) {
        if (swipeX === null || entries.length < 2) return;
        var distance = event.clientX - swipeX;
        swipeX = null;
        if (Math.abs(distance) < SWIPE_DISTANCE) return;
        swiped = true;
        setTimeout(function () { swiped = false; }, 400);
        show(index + (distance < 0 ? 1 : -1));
    });

    // ---- wiring -----------------------------------------------------------
    document.addEventListener('click', function (event) {
        if (event.defaultPrevented || event.button || event.metaKey || event.ctrlKey ||
            event.shiftKey || event.altKey) return;
        var link = event.target.closest && event.target.closest('a.gallery-photo');
        if (!link) return;
        var grid = link.closest('.gallery-grid') || document;
        var list = galleryEntries(grid);
        var at = list.findIndex(function (entry) { return entry.trigger === link; });
        if (at === -1) return;
        event.preventDefault();
        open(list, at);
    });

    Array.prototype.forEach.call(document.querySelectorAll('.blog-post-content'), function (post) {
        var photos = postPhotos(post);
        var list = photos.map(function (img) {
            return { trigger: img, img: img, href: img.currentSrc || img.src };
        });
        photos.forEach(function (img, at) {
            img.classList.add('photo-viewable');
            img.tabIndex = 0;
            img.setAttribute('role', 'button');
            img.setAttribute('aria-label', 'view photo' + (img.alt ? ': ' + img.alt : ''));
            // A post's photos are its own set; arrows move between them.
            var launch = function () { open(list, at); };
            img.addEventListener('click', launch);
            img.addEventListener('keydown', function (event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    launch();
                }
            });
        });
    });
})();
