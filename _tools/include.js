(function () {
    const script = document.currentScript;
    const rawBase = (script && script.dataset.base) ? script.dataset.base : '.';
    const base = (rawBase || '.').replace(/\/+$/, '') || '.';

    // Load bot-blocker first to ensure scrapers are blocked immediately
    const botBlockerScript = document.createElement('script');
    botBlockerScript.src = `${base}/_tools/bot-blocker.js`;
    document.head.appendChild(botBlockerScript);

    window.nublogBase = base;

    const loadPartial = (file, target) => {
        if (!target) return Promise.resolve();

        return fetch(`${base}/partials/${file}`)
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
        counterScript.src = `${base}/_tools/counter.js`;
        document.body.appendChild(counterScript);
    });

    // Load oneko
    const onekoScript = document.createElement('script');
    onekoScript.src = `${base}/_tools/oneko.js`;
    document.body.appendChild(onekoScript);

    // Load music player
    const musicScript = document.createElement('script');
    musicScript.src = `${base}/_tools/music.js`;
    document.body.appendChild(musicScript);

})();
