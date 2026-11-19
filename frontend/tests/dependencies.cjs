const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { pathToFileURL, fileURLToPath } = require('node:url');
const { JSDOM } = require('jsdom');

const root = path.resolve(__dirname, '..');
const context = vm.createContext({});
const cache = new Map();
const external = new Set();
let linkedModules = 0;
let checkedFiles = 0;

function readModule(filename) {
    if (!cache.has(filename)) {
        cache.set(filename, new vm.SourceTextModule(fs.readFileSync(filename, 'utf8'), {
            context, identifier: pathToFileURL(filename).href
        }));
    }
    return cache.get(filename);
}

async function link(module) {
    if (module.status !== 'unlinked') return;
    await module.link((specifier, parent) => {
        const target = new URL(specifier, parent.identifier);
        assert.equal(target.protocol, 'file:', 'App module imports must resolve locally');
        target.search = '';
        target.hash = '';
        return readModule(fileURLToPath(target));
    });
    linkedModules++;
}

(async () => {
    for (const file of fs.readdirSync(root).filter(name => name.endsWith('.html'))) {
        const filename = path.join(root, file);
        const source = fs.readFileSync(filename, 'utf8');
        const dom = new JSDOM(source, { url: 'http://localhost:8080/' + file });
        const document = dom.window.document;
        if (source.includes('escapeSetupText(')) {
            assert(document.querySelector('script[src^="employee-import.js"]'), file + ' needs the shared escape helper');
        }
        for (const element of document.querySelectorAll('script[src], link[rel="stylesheet"], a[download]')) {
            const reference = element.getAttribute('src') || element.getAttribute('href');
            if (!reference) continue;
            if (/^https?:/.test(reference)) {
                assert(!/xlsx|sheetjs/i.test(reference), file + ' must use bundled SheetJS for offline imports');
                external.add(reference);
                continue;
            }
            const clean = reference.split(/[?#]/)[0];
            if (!clean) continue;
            const target = path.resolve(root, clean);
            assert(fs.existsSync(target), file + ' missing dependency ' + reference);
            checkedFiles++;
        }
        let index = 0;
        for (const element of document.querySelectorAll('script[type="module"]')) {
            const module = element.src ? readModule(path.resolve(root, element.getAttribute('src').split('?')[0])) :
                new vm.SourceTextModule(element.textContent, {
                    context, identifier: pathToFileURL(filename).href + '#module-' + index++
                });
            await link(module);
        }
        dom.window.close();
    }
    for (const filename of fs.readdirSync(root).filter(name => name.endsWith('.js'))) {
        await link(readModule(path.join(root, filename)));
    }
    console.log('Dependency checks passed:', linkedModules, 'JavaScript modules linked,', checkedFiles, 'local file references resolved.');
    console.log('External browser dependencies:', [...external].join(', '));
})().catch(error => { console.error(error); process.exitCode = 1; });
