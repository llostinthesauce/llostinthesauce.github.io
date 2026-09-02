const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '..');
const flush = () => new Promise(resolve => setImmediate(resolve));

function element(text = '') {
    return {
        children: [], style: {}, dataset: {}, textContent: text,
        get firstChild() { return this.children[0]; },
        appendChild(child) { this.children.push(child); },
        removeChild(child) { this.children.splice(this.children.indexOf(child), 1); },
        setAttribute(name, value) { this[name] = value; }
    };
}

function counterHarness(fetch, cached) {
    const span = element();
    span.appendChild(element('loading...'));
    const timers = new Map();
    const saved = new Map(cached === undefined ? [] : [['nuBlogCounterCache', JSON.stringify({ total: cached })]]);
    const document = {
        readyState: 'complete', head: element(),
        getElementById: id => id === 'hit-counter' ? span : null,
        querySelector: () => null,
        createElement: () => element(), createTextNode: element
    };
    vm.runInNewContext(fs.readFileSync(path.join(root, 'js/counter.js'), 'utf8'), {
        document, fetch, AbortController,
        localStorage: { getItem: key => saved.get(key), setItem: (key, value) => saved.set(key, value) },
        console: { error() {} },
        setTimeout(callback, delay) { const key = Symbol(); timers.set(key, { callback, delay }); return key; },
        clearTimeout(key) { timers.delete(key); }
    });
    function text(node) { return node.textContent + node.children.map(text).join(''); }
    return {
        label: () => text(span), saved, timers,
        expire() { for (const { callback } of [...timers.values()]) callback(); }
    };
}

test('a live count includes the preserved total and refreshes the cache', async () => {
    const harness = counterHarness(async (url, options) => {
        assert.equal(url, 'https://badcovers.goatcounter.com/counter/TOTAL.json');
        assert.equal(options.cache, 'no-store');
        return { ok: true, json: async () => ({ count: '1,234', count_unique: '900' }) };
    });
    await flush();
    assert.equal(harness.label(), 'VISITOR COUNT: 12262+');
    assert.equal(JSON.parse(harness.saved.get('nuBlogCounterCache')).total, 12262);
    assert.equal(harness.timers.size, 0);
});

test('a stalled request stops loading within eight seconds and is cancelled', async () => {
    let signal;
    const harness = counterHarness((_url, options) => {
        signal = options.signal;
        return new Promise(() => {});
    });
    assert.ok(harness.timers.size > 0, 'a stalled count needs a deadline');
    assert.ok([...harness.timers.values()].every(timer => timer.delay <= 8000));
    harness.expire();
    await flush();
    assert.equal(harness.label(), 'VISITOR COUNT: unavailable');
    assert.equal(signal.aborted, true);
    assert.equal(harness.timers.size, 0);
});

test('a stalled response body is also covered by the deadline', async () => {
    const harness = counterHarness(async () => ({ ok: true, json: () => new Promise(() => {}) }));
    await flush();
    harness.expire();
    await flush();
    assert.equal(harness.label(), 'VISITOR COUNT: unavailable');
});

test('a timeout retains the last known count without overwriting the cache', async () => {
    const harness = counterHarness(() => new Promise(() => {}), 11030);
    harness.expire();
    await flush();
    assert.equal(harness.label(), 'VISITOR COUNT: 11030+');
    assert.equal(JSON.parse(harness.saved.get('nuBlogCounterCache')).total, 11030);
});

test('an HTTP failure shows unavailable rather than a fabricated total', async () => {
    const harness = counterHarness(async () => ({ ok: false, status: 503 }));
    await flush();
    assert.equal(harness.label(), 'VISITOR COUNT: unavailable');
});

for (const count of ['', ' ', '-1', '1.5', null, 'not a number']) {
    test(`invalid count ${JSON.stringify(count)} cannot replace the last known total`, async () => {
        const harness = counterHarness(async () => ({ ok: true, json: async () => ({ count }) }), 11030);
        await flush();
        assert.equal(harness.label(), 'VISITOR COUNT: 11030+');
        assert.equal(JSON.parse(harness.saved.get('nuBlogCounterCache')).total, 11030);
    });
}

test('a stalled header does not block the footer counter, which inherits the loader version', async () => {
    const body = element();
    const footer = element();
    const header = element();
    const script = { src: 'https://example.com/js/include.js?v=fresh-build', dataset: { base: '.' } };
    vm.runInNewContext(fs.readFileSync(path.join(root, 'js/include.js'), 'utf8'), {
        URL, console,
        document: {
            currentScript: script, body, head: element(),
            createElement: () => element(),
            getElementById: id => ({ 'site-header': header, 'site-footer': footer })[id],
            querySelectorAll: () => []
        },
        window: { location: { pathname: '/index.html', href: 'https://example.com/index.html' }, matchMedia: () => ({ matches: true }) },
        navigator: {},
        fetch: url => url.includes('header.html')
            ? new Promise(() => {})
            : Promise.resolve({ ok: true, text: async () => '<footer>ready</footer>' })
    });
    await flush();
    assert.equal(footer.innerHTML, '<footer>ready</footer>');
    assert.ok(body.children.some(child => child.src === './js/counter.js?v=fresh-build'));
});
