const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

function image(alt, width = 0, height = 0) {
    const attrs = alt === undefined ? {} : { alt };
    return {
        naturalWidth: width, naturalHeight: height,
        hasAttribute: name => name in attrs,
        get alt() { return attrs.alt; }, set alt(value) { attrs.alt = value; },
        addEventListener(name, callback) { this[name] = callback; }
    };
}

function run(images, groups = {}, oldestReview) {
    let update;
    const file = path.join(__dirname, '../js/goodreads-widgets.js');
    assert.ok(fs.existsSync(file), 'live widget images need the site image contract');
    vm.runInNewContext(fs.readFileSync(file, 'utf8'), {
        document: { querySelector: () => ({
            dataset: { oldestReview },
            querySelectorAll: selector => selector === 'img' ? images : (groups[selector] || [])
        }) },
        MutationObserver: class { constructor(callback) { update = callback; } observe() {} }
    });
    return () => update();
}

test('existing widget covers retain alt text and receive lazy loading and real geometry', () => {
    const cover = image('The Odyssey', 49, 75);
    run([cover]);
    assert.equal(cover.alt, 'The Odyssey');
    assert.equal(cover.loading, 'lazy');
    assert.equal(cover.width, 49);
    assert.equal(cover.height, 75);
});

function book(reviewId) {
    return {
        querySelector: selector => selector.includes('/review/show/' + reviewId + '?') ? {} : null,
        removed: false,
        remove() { this.removed = true; }
    };
}

test('both live widgets retain the archive boundary as new books arrive', () => {
    const reviews = [book('new'), book('oldest'), book('older')];
    const covers = [book('new'), book('oldest'), book('older')];
    const update = run([], {
        '[class^="gr_custom_each_container_"]': reviews,
        '.gr_grid_book_container': covers
    }, 'oldest');
    for (const entries of [reviews, covers]) {
        assert.deepEqual(entries.map(entry => entry.removed), [false, false, true]);
        entries.unshift(book('newer'));
    }
    update();
    for (const entries of [reviews, covers]) {
        assert.deepEqual(entries.map(entry => entry.removed), [false, false, false, true]);
    }
});

test('a feed missing the archive boundary does not silently discard any books', () => {
    const reviews = [book('new'), book('other')];
    run([], { '[class^="gr_custom_each_container_"]': reviews }, 'oldest');
    assert.ok(reviews.every(entry => !entry.removed));
});

test('provider replacements are normalized, including images that load later', () => {
    const images = [];
    const update = run(images);
    const star = image();
    images.push(star);
    update();
    assert.equal(star.alt, '');
    assert.equal(star.loading, 'lazy');
    star.naturalWidth = 15;
    star.naturalHeight = 15;
    star.load();
    assert.equal(star.width, 15);
    assert.equal(star.height, 15);
});
