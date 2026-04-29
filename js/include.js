(function () {
    const script = document.currentScript;
    const rawBase = (script && script.dataset.base) ? script.dataset.base : '.';
    const base = (rawBase || '.').replace(/\/+$/, '') || '.';

    // Validate data-base matches page depth
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

    // Load bot-blocker first to ensure scrapers are blocked immediately
    const botBlockerScript = document.createElement('script');
    botBlockerScript.src = `${base}/js/bot-blocker.js`;
    document.head.appendChild(botBlockerScript);

    window.nublogBase = base;

    const loadPartial = (file, target) => {
        if (!target) return Promise.resolve();

        return fetch(`${base}/partials/${file}?v=${new Date().getTime()}`)
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
