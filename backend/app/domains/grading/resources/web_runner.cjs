// Guest-only instructor test runner. Kata/Judge0, rather than jsdom, provides isolation.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { JSDOM, ResourceLoader, VirtualConsole } = require('/opt/autograder/web/node_modules/jsdom');
const esbuild = require('/opt/autograder/web/node_modules/esbuild');
const root = fs.realpathSync(process.cwd());
const config = JSON.parse(fs.readFileSync('ag_config.json', 'utf8'));
const registered = [];
let activeWindows = [];

function localFile(name) {
  const resolved = fs.realpathSync(path.resolve(root, name));
  if (resolved !== root && !resolved.startsWith(root + path.sep)) throw new Error('Resource is outside the submission');
  return resolved;
}

class WorkspaceResources extends ResourceLoader {
  fetch(url) {
    const parsed = new URL(url);
    if (parsed.origin !== 'https://workspace.invalid') return null;
    try { return Promise.resolve(fs.readFileSync(localFile(decodeURIComponent(parsed.pathname).slice(1)))); }
    catch { return null; }
  }
}

async function loadSubmission(filename = config.entrypoint) {
  const entry = localFile(filename);
  const document = new JSDOM(fs.readFileSync(entry, 'utf8'), { url: 'https://workspace.invalid/' + filename });
  try {
    // jsdom does not execute module tags. Bundle local modules as deferred classic scripts.
    for (const script of document.window.document.querySelectorAll('script[type="module"]')) {
      const sourcePath = script.getAttribute('src');
      let source = script.textContent;
      if (sourcePath) {
        const url = new URL(sourcePath, document.window.document.URL);
        if (url.origin !== 'https://workspace.invalid') throw new Error('External modules are unavailable');
        source = fs.readFileSync(localFile(decodeURIComponent(url.pathname).slice(1)), 'utf8');
      }
      const result = await esbuild.build({
        stdin: { contents: source, resolveDir: sourcePath ? path.dirname(localFile(new URL(sourcePath, document.window.document.URL).pathname.slice(1))) : path.dirname(entry), sourcefile: sourcePath || filename },
        bundle: true, write: false, format: 'iife', platform: 'browser', target: 'es2022', logLevel: 'silent',
        plugins: [{ name: 'workspace-only', setup(build) {
          build.onResolve({ filter: /.*/ }, args => {
            if (!args.path.startsWith('.') && !args.path.startsWith('/')) throw new Error('Only local module imports are supported');
            const resolved = localFile(path.resolve(args.resolveDir, args.path));
            return { path: resolved };
          });
        } }],
      });
      script.removeAttribute('type');
      script.setAttribute('defer', '');
      script.setAttribute('src', 'data:text/javascript;base64,' + Buffer.from(result.outputFiles[0].text).toString('base64'));
      script.textContent = '';
    }
    const html = document.serialize();
    const errors = [];
    const virtualConsole = new VirtualConsole();
    virtualConsole.on('jsdomError', error => { if (error.type === 'unhandled-exception') errors.push(error); });
    class Resources extends WorkspaceResources {
      fetch(url, options) {
        if (url.startsWith('data:text/javascript;base64,')) return Promise.resolve(Buffer.from(url.split(',')[1], 'base64'));
        return super.fetch(url, options);
      }
    }
    const dom = new JSDOM(html, { url: 'https://workspace.invalid/' + filename,
      runScripts: 'dangerously', resources: new Resources(), virtualConsole });
    activeWindows.push(dom.window);
    await new Promise(resolve => {
      if (dom.window.document.readyState === 'complete') resolve();
      else dom.window.addEventListener('load', resolve, { once: true });
    });
    if (errors.length) throw new Error(errors.map(error => error.cause?.message || error.message).join('\n'));
    return { window: dom.window, document: dom.window.document, close: () => dom.window.close() };
  } finally { document.window.close(); }
}

async function main() {
  for (const filename of config.test_files) {
    const register = require(localFile(filename));
    if (typeof register !== 'function') throw new Error('Test suites must export a registration function');
    await register({ assert, loadSubmission, test(key, name, callback) {
      if (!/^[a-z][a-z0-9_]*$/.test(key) || typeof name !== 'string' || !name || typeof callback !== 'function') {
        throw new Error('Invalid test registration');
      }
      registered.push({ nodeid: filename + '::' + name, markers: ['ag_' + key], xfail: false, callback });
    } });
  }
  const collected = registered.map(({ callback, ...entry }) => entry);
  if (!collected.length || collected.length > 512 || new Set(collected.map(c => c.nodeid)).size !== collected.length) {
    throw new Error('Test discovery must return 1–512 distinct cases');
  }
  const tests = [];
  for (const { callback, ...entry } of registered) {
    let timer;
    const start = performance.now();
    try {
      await Promise.race([Promise.resolve().then(() => callback({ assert, loadSubmission })),
        new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('Test timed out')), 5000); })]);
      tests.push({ ...entry, outcome: 'passed', duration: (performance.now() - start) / 1000, message: null });
    } catch (error) {
      if (error.message === 'Test timed out') throw error;
      tests.push({ ...entry, outcome: 'failed', duration: (performance.now() - start) / 1000,
        message: String(error.message || error).slice(0, 2000) });
    } finally {
      clearTimeout(timer);
      for (const window of activeWindows) window.close();
      activeWindows = [];
    }
  }
  fs.writeFileSync(process.argv[2], JSON.stringify({ collected, tests }));
}
main().catch(error => { console.error(String(error.message || error)); process.exitCode = 2; });
