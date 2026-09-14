const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '..');

test('theme.js title case matches the build script cases', () => {
    const context = {};
    vm.createContext(context);
    vm.runInContext(fs.readFileSync(path.join(root, 'js/theme.js'), 'utf8'), context);
    const cases = JSON.parse(fs.readFileSync(path.join(root, 'tests/title-case-cases.json'), 'utf8'));
    for (const [raw, expected] of Object.entries(cases)) {
        assert.equal(context.nublogTitleCase(raw), expected, raw);
    }
});
