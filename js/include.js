(function () {
    const script = document.currentScript;
    // The build hashes this loader and counter.js together, then versions every page.
    const COUNTER_VERSION = (script && new URL(script.src, window.location.href).searchParams.get('v')) || '2026-09-01';
    const rawBase = (script && script.dataset.base) ? script.dataset.base : '.';
    // data-base="/" means site root (used by 404.html, which GitHub Pages
    // serves at any URL depth, so relative paths can never work there).
    const isRootBase = rawBase === '/';
    const base = isRootBase ? '' : ((rawBase || '.').replace(/\/+$/, '') || '.');

    // Validate data-base matches page depth (skip for root-absolute pages)
    if (!isRootBase) {
        const pathSegments = window.location.pathname.split('/').filter(Boolean);
        const depth = Math.max(0, pathSegments.length - 1);
        const expectedBase = depth === 0 ? '.' : new Array(depth).fill('..').join('/');
        if (base !== expectedBase) {
            console.warn(
                `[nuBlog] data-base mismatch: page depth=${depth}, ` +
                `expected "${expectedBase}", got "${base}" — ` +
                `nav, CSS, and JS paths may be broken`
            );
        }
    }

    // Load bot-blocker first to ensure scrapers are blocked immediately
    const botBlockerScript = document.createElement('script');
    botBlockerScript.src = `${base}/js/bot-blocker.js`;
    document.head.appendChild(botBlockerScript);

    window.nublogBase = base;
    if (navigator.connection && navigator.connection.saveData) {
        document.documentElement.classList.add('save-data');
    }

    const loadCounter = () => {
        const counterScript = document.createElement('script');
        counterScript.src = `${base}/js/counter.js?v=${COUNTER_VERSION}`;
        document.body.appendChild(counterScript);
    };

    // The nuBlog header and footer are already in the page: the build writes
    // partials/*.html into every page, current nav link included. The clean
    // theme (js/theme.js, loaded in <head>) swaps in its own and leaves the
    // cat at home.
    const cleanTheme = window.nublogTheme && window.nublogTheme.isClean;

    if (cleanTheme) window.nublogTheme.renderChrome();
    loadCounter();

    // Load oneko only when the visitor has not requested reduced motion.
    if (!cleanTheme && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        const onekoScript = document.createElement('script');
        onekoScript.src = `${base}/js/oneko.js`;
        document.body.appendChild(onekoScript);
    }

    // Click-to-view for grid photos and photos in posts; versioned with this
    // loader (the build hashes all three), so a changed viewer is never stale.
    if (document.querySelector('a.gallery-photo, .blog-post-content img')) {
        const viewerScript = document.createElement('script');
        viewerScript.src = `${base}/js/photo-viewer.js?v=${COUNTER_VERSION}`;
        document.body.appendChild(viewerScript);
    }

    // Blog posts only: next/prev links under the post.
    if (/\/blog\/[^/]+\.html$/.test(window.location.pathname)) {
        const blogNavScript = document.createElement('script');
        blogNavScript.src = `${base}/js/blog-nav.js`;
        document.body.appendChild(blogNavScript);
    }
})();
