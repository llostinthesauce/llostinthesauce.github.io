/* nuBlog theme switch — two skins over one set of posts.
 *
 *   clean  the reader: writing only, serif, light/dark (the default)
 *   full   nuBlog as it has always been
 *
 * Loaded synchronously in <head>, BEFORE first paint, by the pages that care:
 *
 *   <script src="js/theme.js" data-page="home"></script>        index.html
 *   <script src="js/theme.js" data-page="blog-index"></script>  blog.html
 *   <script src="js/theme.js" data-page="writing"></script>     writing.html
 *   <script src="../js/theme.js" data-page="post"></script>     blog/*.html
 *
 * home / blog-index hand clean visitors to writing.html before anything
 * renders. writing is always clean (visiting it opts you in). A post keeps its
 * URL and swaps its stylesheet, so a shared link opens in the reader's own theme.
 *
 * Everything else on the site (photos, builds, plants…) is full-only and never
 * loads this file; its nav carries a plain link to writing.html.
 *
 * ?theme=clean|full on any of these pages sets the preference and is stripped.
 */
(function () {
    // Title case for the clean theme — the same rules as title_case() in
    // scripts/build-sitemap.py (which titles writing.html); both are held to
    // tests/title-case-cases.json. Raises case only, so FinTech stays FinTech.
    var SMALL_WORDS = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'if', 'in', 'into',
        'nor', 'of', 'on', 'or', 'per', 'than', 'the', 'to', 'via', 'vs', 'with'];
    var ACRONYMS = { ai: 'AI' };
    var ROMAN_RE = /^(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)$/;
    var INITIALS_RE = /^(?:[a-z]\.)+[a-z]?$/;

    function titleCase(text) {
        var words = text.split(' ');
        return words.map(function (word, index) {
            var lead = word.match(/^[^A-Za-z0-9]*/)[0];
            var core = word.slice(lead.length);
            var tail = core ? core.match(/[^A-Za-z0-9.]*$/)[0] : '';
            if (tail) core = core.slice(0, core.length - tail.length);
            var afterColon = index > 0 && /:$/.test(words[index - 1]);
            var edge = index === 0 || index === words.length - 1 || afterColon;
            var parts = core.split('-').map(function (part, partIndex) {
                var bare = part.replace(/\.+$/, '');
                if (!part || /[A-Z]/.test(part)) return part;
                if (Object.prototype.hasOwnProperty.call(ACRONYMS, bare)) return ACRONYMS[bare] + part.slice(bare.length);
                if (ROMAN_RE.test(bare) || INITIALS_RE.test(part)) return part.toUpperCase();
                if (partIndex === 0 && !edge && SMALL_WORDS.indexOf(part) !== -1) return part;
                return part.replace(/[a-z]/, function (ch) { return ch.toUpperCase(); });
            });
            return lead + parts.join('-') + tail;
        }).join(' ');
    }

    globalThis.nublogTitleCase = titleCase;
    if (typeof document === 'undefined') return; // loaded by the node tests

    var THEME_KEY = 'nublog.theme';
    var MODE_KEY = 'nublog.mode';
    var script = document.currentScript;
    var root = document.documentElement;
    var page = (script && script.dataset.page) || 'post';
    var siteRoot = new URL('..', script.src).href;

    function read(key) {
        try { return localStorage.getItem(key); } catch (_) { return null; }
    }

    function write(key, value) {
        try { localStorage.setItem(key, value); } catch (_) { /* private mode: session-only */ }
    }

    // ---- theme preference -------------------------------------------------
    var params = new URLSearchParams(location.search);
    var asked = params.get('theme');
    if (asked === 'clean' || asked === 'full') {
        write(THEME_KEY, asked);
        params.delete('theme');
        var rest = params.toString();
        history.replaceState(null, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
    }

    var theme = page === 'writing' ? 'clean' : (read(THEME_KEY) === 'full' ? 'full' : 'clean');
    if (page === 'writing') write(THEME_KEY, 'clean');

    if (theme === 'clean' && (page === 'home' || page === 'blog-index')) {
        location.replace(siteRoot + 'writing.html' + location.hash);
        return;
    }

    function setTheme(next, destination) {
        write(THEME_KEY, next);
        if (destination) location.href = destination;
        else location.reload();
    }

    // [data-theme-switch] links work without this handler (they point at a
    // page that sets the preference). On a post we intercept so you stay on
    // the same post instead of being bounced to a home page.
    document.addEventListener('click', function (event) {
        var link = event.target.closest && event.target.closest('[data-theme-switch]');
        if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.button) return;
        if (page !== 'post') {
            write(THEME_KEY, link.dataset.themeSwitch);
            return;
        }
        event.preventDefault();
        setTheme(link.dataset.themeSwitch);
    });

    window.nublogTheme = { theme: theme, isClean: theme === 'clean', siteRoot: siteRoot, set: setTheme };

    if (theme !== 'clean') {
        root.dataset.site = 'full';
        return;
    }

    // ---- clean skin -------------------------------------------------------
    root.dataset.site = 'clean';

    var systemDark = window.matchMedia('(prefers-color-scheme: dark)');
    function applyMode() {
        var stored = read(MODE_KEY);
        root.dataset.mode = stored === 'dark' || stored === 'light'
            ? stored
            : (systemDark.matches ? 'dark' : 'light');
        var toggle = document.querySelector('.clean-mode');
        if (toggle) toggle.setAttribute('aria-checked', String(root.dataset.mode === 'dark'));
    }
    applyMode();
    systemDark.addEventListener('change', applyMode);

    // Posts ship nuBlog's stylesheet: switch it off and write the reader's in
    // while the parser is still in <head>. document.write (rather than
    // appendChild) keeps the new sheet parser-inserted, so it blocks first
    // paint and a post never flashes black-and-purple on its way to ivory.
    Array.prototype.forEach.call(
        document.querySelectorAll('link[rel="stylesheet"][href*="style.css"]'),
        function (link) { link.media = 'not all'; }
    );
    if (!document.querySelector('link[href*="clean.css"]')) {
        document.write('<link rel="stylesheet" href="' + siteRoot + 'styles/clean.css">');
    }

    var CATEGORY_LABELS = {
        'essay': ['Essay', 'essays'],
        'university': ['University Essay', 'university-essays'],
        'field-notes': ['Field Notes', 'field-notes'],
        'creative': ['Creative Writing', 'creative-writing'],
        'other': ['Other', 'other']
    };

    function el(tag, attrs, text) {
        var node = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (key) { node.setAttribute(key, attrs[key]); });
        if (text) node.textContent = text;
        return node;
    }

    function modeToggle() {
        var toggle = el('button', {
            'class': 'clean-mode',
            type: 'button',
            role: 'switch',
            'aria-label': 'dark mode',
            'aria-checked': String(root.dataset.mode === 'dark')
        });
        toggle.addEventListener('click', function () {
            write(MODE_KEY, root.dataset.mode === 'dark' ? 'light' : 'dark');
            applyMode();
        });
        return toggle;
    }

    // Called by include.js in place of the nuBlog header/footer partials.
    function renderChrome() {
        var headerSlot = document.getElementById('site-header');
        var footerSlot = document.getElementById('site-footer');
        var writingUrl = siteRoot + 'writing.html';

        // writing.html carries its header statically (its <h1> is the name);
        // it only needs the toggle wired in.
        var staticToggleSlot = document.querySelector('[data-mode-toggle]');
        if (staticToggleSlot) {
            staticToggleSlot.replaceWith(modeToggle());
        } else if (headerSlot) {
            var header = el('header', { 'class': 'clean-header' });
            header.appendChild(el('a', { 'class': 'skip-link', href: '#main-content' }, 'skip to content'));
            header.appendChild(el('a', { 'class': 'clean-name', href: writingUrl }, 'nuBlog'));
            var swap = el('a', { 'class': 'clean-swap', href: siteRoot + 'index.html?theme=full', 'data-theme-switch': 'full' });
            swap.appendChild(el('span', { 'class': 'clean-swap-dot', 'aria-hidden': 'true' }));
            swap.appendChild(document.createTextNode('enter full site'));
            header.appendChild(swap);
            header.appendChild(modeToggle());
            headerSlot.replaceChildren(header);
        }

        if (footerSlot) {
            var footer = el('footer', { 'class': 'clean-footer' });
            footer.appendChild(el('span', {}, '© 2026 nuBlog'));
            var counter = el('span', { id: 'hit-counter' });
            footer.appendChild(counter);
            footerSlot.replaceChildren(footer);
        }

        // Post furniture: a category eyebrow over the title, and a plain date.
        var meta = document.querySelector('meta[name="nublog:category"]');
        var title = document.querySelector('main h1');
        var label = meta && CATEGORY_LABELS[meta.content];
        if (label && title && page === 'post') {
            var eyebrow = el('div', { 'class': 'clean-eyebrow' });
            eyebrow.appendChild(el('a', { href: writingUrl + '#' + label[1] }, label[0]));
            title.before(eyebrow);
        }
        if (title && page === 'post') {
            title.textContent = titleCase(title.textContent.trim());
            document.title = document.title.replace(/^(.*) - nuBlog$/, function (_, name) {
                return titleCase(name) + ' - nuBlog';
            });
        }
        var date = document.querySelector('.blog-post-date');
        if (date) date.textContent = date.textContent.replace(/^\s*originally published:\s*/i, '');
    }

    window.nublogTheme.renderChrome = renderChrome;
})();
