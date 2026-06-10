(function () {
    // Bump when partials/header.html or partials/footer.html change,
    // so cached copies are invalidated without defeating HTTP caching.
    const PARTIALS_VERSION = '2026-06-09';

    const script = document.currentScript;
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

    const loadPartial = (file, target) => {
        if (!target) return Promise.resolve();

        return fetch(`${base}/partials/${file}?v=${PARTIALS_VERSION}`)
            .then((resp) => resp.ok ? resp.text() : '')
            .then((html) => {
                const rendered = html.replace(/%BASE%/g, base);
                target.innerHTML = rendered;
            })
            .catch((err) => {
                console.error(`Failed to load ${file}`, err);
            });
    };

    Promise.all([
        loadPartial('header.html', document.getElementById('site-header')),
        loadPartial('footer.html', document.getElementById('site-footer'))
    ]).then(() => {
        // Load hit counter
        const counterScript = document.createElement('script');
        counterScript.src = `${base}/js/counter.js`;
        document.body.appendChild(counterScript);
    });

    // Load oneko
    const onekoScript = document.createElement('script');
    onekoScript.src = `${base}/js/oneko.js`;
    document.body.appendChild(onekoScript);

    // Load blog nav (injects next/prev links on blog posts)
    const blogNavScript = document.createElement('script');
    blogNavScript.src = `${base}/js/blog-nav.js`;
    document.body.appendChild(blogNavScript);



})();
