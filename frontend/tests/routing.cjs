const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const config = fs.readFileSync(path.join(root, 'nginx.conf'), 'utf8');
const proxyLocations = [...config.matchAll(/location\s+(=\s+)?([^\s{]+)\s*\{([^}]+)\}/g)]
    .filter(match => match[3].includes('proxy_pass'))
    .map(match => ({ exact: Boolean(match[1]), path: match[2] }));
function proxies(url) {
    const pathname = new URL(url, 'http://localhost:8080').pathname;
    return proxyLocations.some(location => location.exact ?
        pathname === location.path : pathname.startsWith(location.path));
}
assert.equal(proxies('/api'), true);
assert.equal(proxies('/api/health'), true);
assert.equal(proxies('/apiFunctions.js'), false);
assert.equal(proxies('/apiFunctions.js?v=20261117c'), false);
assert.equal(proxies('/employee1.html?id=159'), false);
const moduleSource = fs.readFileSync(path.join(root, 'apiFunctions.js'), 'utf8');
const exportedFunctions = moduleSource.slice(moduleSource.indexOf('export {'));
assert(exportedFunctions.includes('saveEmployeeDetails'));
console.log('Routing checks passed: API paths are proxied and the employee API module is served by the frontend.');
