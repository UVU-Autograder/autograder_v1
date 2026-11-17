import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LivePreview, bundleHtmlPreview } from '../live-preview';
import { AssignmentFileContext, AssignmentFileContextType } from '../assignment-file-context';
import { WorkspaceVFS } from '../vfs/workspace-vfs';
import type { OpenFile } from '../editor-layout';

function createMockFileContext(
  files: Record<string, OpenFile> = {},
  overrides?: Partial<AssignmentFileContextType>
): AssignmentFileContextType {
  const vfs = new WorkspaceVFS();
  return {
    assignment: {
      id: 'test-1',
      course_id: 'cs2550',
      title: 'Web Dev Lab',
      sandbox_enabled: true,
      language: 'web',
      max_score: 100,
      description: 'Web development lab',
      upload_quota: {
        limit: 10,
        window_seconds: 3600,
        remaining: 10,
        reset_at: '2026-10-06T00:00:00Z',
      },
      config: {
        bundle: {
          entrypoint: 'index.html',
          file_requirements: [{ paths: ['index.html'] }],
          language: 'web',
        },
        scoring_items: [],
      },
      accepted_bundle_types: ['zip'],
      max_upload_bytes: 1024 * 1024,
      constraints: [],
      rubric: [],
      rubric_groups: [],
    },
    files,
    panes: {
      'pane-1': {
        id: 'pane-1',
        tabs: ['index.html'],
        activeTab: 'index.html',
      },
    },
    layout: { type: 'pane', paneId: 'pane-1' },
    activePaneId: 'pane-1',
    dragTab: null,
    vfs,
    openFileByName: vi.fn(),
    setActiveTab: vi.fn(),
    setActivePane: vi.fn(),
    closeTab: vi.fn(),
    startTabDrag: vi.fn(),
    endTabDrag: vi.fn(),
    splitTabToPane: vi.fn(),
    moveTabToPane: vi.fn(),
    uploadFiles: vi.fn(),
    updateFileContent: vi.fn(),
    deleteFile: vi.fn(),
    renameFile: vi.fn(),
    openLivePreview: vi.fn(),
    ...overrides,
  };
}

function workspaceFile(
  filename: string,
  content: string,
  language = 'plaintext',
  extra: Partial<OpenFile> = {}
): OpenFile {
  return { filename, content, language, category: 'workspace', ...extra };
}

function toFiles(...list: OpenFile[]): Record<string, OpenFile> {
  return Object.fromEntries(list.map((f) => [f.filename, f]));
}

function parseBundle(html: string): Document {
  return new DOMParser().parseFromString(html, 'text/html');
}

function decodeDataUrl(url: string | null): string {
  expect(url).toBeTruthy();
  const comma = (url as string).indexOf(',');
  expect((url as string).startsWith('data:')).toBe(true);
  return decodeURIComponent((url as string).slice(comma + 1));
}

function readImportMap(doc: Document): Record<string, string> {
  const script = doc.querySelector('script[type="importmap"]');
  expect(script).not.toBeNull();
  return (JSON.parse(script?.textContent ?? '{}') as { imports: Record<string, string> })
    .imports;
}

describe('bundleHtmlPreview', () => {
  it('returns empty string if HTML file does not exist', async () => {
    expect(await bundleHtmlPreview('missing.html', {})).toBe('');
  });

  it('replaces local stylesheet href with a CSS data URL and keeps the link', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="style.css" media="screen"></head><body><h1>Hi</h1></body></html>',
        'html'
      ),
      workspaceFile('style.css', 'h1 { color: red; }', 'css')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    const link = doc.querySelector('link[rel="stylesheet"]');
    expect(link).not.toBeNull();
    expect(link?.getAttribute('media')).toBe('screen');
    expect(link?.getAttribute('href')).toMatch(/^data:text\/css/);
    expect(decodeDataUrl(link?.getAttribute('href') ?? null)).toBe('h1 { color: red; }');
    expect(doc.querySelector('style')).toBeNull();
  });

  it('matches stylesheet links regardless of attribute order and ignores external URLs', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        `<!DOCTYPE html><html><head>
          <link href="./style.css?v=2" rel="stylesheet">
          <link rel="stylesheet" href="https://cdn.example.com/lib.css">
          <link rel="stylesheet" href="data:text/css,body{}">
          <link rel="stylesheet" href="missing.css">
        </head><body></body></html>`,
        'html'
      ),
      workspaceFile('style.css', 'body { margin: 0; }', 'css')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    const hrefs = Array.from(doc.querySelectorAll('link')).map((l) => l.getAttribute('href'));
    expect(decodeDataUrl(hrefs[0])).toBe('body { margin: 0; }');
    expect(hrefs[1]).toBe('https://cdn.example.com/lib.css');
    expect(hrefs[2]).toBe('data:text/css,body{}');
    expect(hrefs[3]).toBe('missing.css');
  });

  it('uses a data URL src for classic scripts instead of inlining the body', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><body><h1>Hi</h1><script src="app.js"></script></body></html>',
        'html'
      ),
      workspaceFile('app.js', 'console.log("running");', 'javascript')
    );

    const bundled = await bundleHtmlPreview('index.html', files);
    const script = parseBundle(bundled).querySelector('script');
    expect(script?.getAttribute('src')).toMatch(/^data:text\/javascript/);
    expect(decodeDataUrl(script?.getAttribute('src') ?? null)).toBe('console.log("running");');
    expect(script?.textContent).toBe('');
    expect(bundled).not.toContain('console.log("running");');
  });

  it('preserves defer, async, type=module and other script attributes', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        `<!DOCTYPE html><html><head>
          <script src="defer.js" defer></script>
          <script src="async.js" async crossorigin="anonymous"></script>
          <script src="main.js" type="module" defer data-role="entry"></script>
        </head><body></body></html>`,
        'html'
      ),
      workspaceFile('defer.js', 'window.a = 1;', 'javascript'),
      workspaceFile('async.js', 'window.b = 2;', 'javascript'),
      workspaceFile('main.js', 'window.c = 3;', 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    const [deferred, asynced, module] = Array.from(doc.querySelectorAll('script[src]'));

    expect(deferred.hasAttribute('defer')).toBe(true);
    expect(deferred.getAttribute('src')).toMatch(/^data:text\/javascript/);

    expect(asynced.hasAttribute('async')).toBe(true);
    expect(asynced.getAttribute('crossorigin')).toBe('anonymous');
    expect(asynced.getAttribute('src')).toMatch(/^data:text\/javascript/);

    expect(module.getAttribute('type')).toBe('module');
    expect(module.hasAttribute('defer')).toBe(true);
    expect(module.getAttribute('data-role')).toBe('entry');
    expect(module.getAttribute('src')).toMatch(/^data:text\/javascript/);
  });

  it('leaves external and missing scripts untouched, including query strings on local ones', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        `<!DOCTYPE html><html><body>
          <script src="https://cdn.example.com/lib.js"></script>
          <script src="missing.js"></script>
          <script src="./app.js?v=4"></script>
        </body></html>`,
        'html'
      ),
      workspaceFile('app.js', 'window.__loaded = true;', 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    const srcs = Array.from(doc.querySelectorAll('script')).map((s) => s.getAttribute('src'));
    expect(srcs[0]).toBe('https://cdn.example.com/lib.js');
    expect(srcs[1]).toBe('missing.js');
    expect(decodeDataUrl(srcs[2])).toBe('window.__loaded = true;');
  });

  it('resolves references relative to the HTML file directory', async () => {
    const files = toFiles(
      workspaceFile(
        'site/index.html',
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="css/a.css"></head><body><script src="../shared/app.js"></script></body></html>',
        'html'
      ),
      workspaceFile('site/css/a.css', 'a{}', 'css'),
      workspaceFile('shared/app.js', 'window.shared = true;', 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('site/index.html', files));
    expect(decodeDataUrl(doc.querySelector('link')?.getAttribute('href') ?? null)).toBe('a{}');
    expect(decodeDataUrl(doc.querySelector('script')?.getAttribute('src') ?? null)).toBe(
      'window.shared = true;'
    );
  });

  it('replaces relative image src with workspace image data URLs', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><body><img src="logo.png" alt="Logo"><img src="missing.png"></body></html>',
        'html'
      ),
      workspaceFile('logo.png', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==', 'image', {
        kind: 'image',
      })
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    const [logo, missing] = Array.from(doc.querySelectorAll('img'));
    expect(logo.getAttribute('src')).toBe('data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==');
    expect(logo.getAttribute('alt')).toBe('Logo');
    expect(missing.getAttribute('src')).toBe('missing.png');
  });

  it('maps local module imports through an import map with stable workspace identifiers', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><head></head><body><script type="module" src="main.js"></script></body></html>',
        'html'
      ),
      workspaceFile(
        'main.js',
        "import { greet } from './lib/util.js';\nimport external from 'lodash';\nimport('./lib/lazy.js');\ngreet(external);",
        'javascript'
      ),
      workspaceFile(
        'lib/util.js',
        "import { base } from '../base.js';\nexport const greet = (n) => base + n;",
        'javascript'
      ),
      workspaceFile('lib/lazy.js', 'export default 1;', 'javascript'),
      workspaceFile('base.js', "export const base = 'hi ';", 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));

    // Import map precedes every module script.
    const firstScript = doc.querySelector('script');
    expect(firstScript?.getAttribute('type')).toBe('importmap');

    const imports = readImportMap(doc);
    expect(Object.keys(imports).sort()).toEqual([
      '@workspace/base.js',
      '@workspace/lib/lazy.js',
      '@workspace/lib/util.js',
      '@workspace/main.js',
    ]);

    const entry = doc.querySelector('script[type="module"]');
    const entryUrl = entry?.getAttribute('src') ?? null;
    expect(entryUrl).toBe(imports['@workspace/main.js']);

    const mainSource = decodeDataUrl(entryUrl);
    expect(mainSource).toContain("from '@workspace/lib/util.js'");
    expect(mainSource).toContain("from 'lodash'");
    expect(mainSource).toContain("import('@workspace/lib/lazy.js')");

    const utilSource = decodeDataUrl(imports['@workspace/lib/util.js']);
    expect(utilSource).toContain("from '@workspace/base.js'");
    expect(decodeDataUrl(imports['@workspace/base.js'])).toBe("export const base = 'hi ';");
  });

  it('handles circular module imports and leaves missing imports as-is', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><body><script type="module" src="a.js"></script></body></html>',
        'html'
      ),
      workspaceFile('a.js', "import './b.js';\nimport './nope.js';\nexport const a = 1;", 'javascript'),
      workspaceFile('b.js', "import { a } from './a.js';\nexport const b = a;", 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    const imports = readImportMap(doc);
    expect(Object.keys(imports).sort()).toEqual(['@workspace/a.js', '@workspace/b.js']);
    const aSource = decodeDataUrl(imports['@workspace/a.js']);
    expect(aSource).toContain("import '@workspace/b.js'");
    expect(aSource).toContain("import './nope.js'");
    expect(decodeDataUrl(imports['@workspace/b.js'])).toContain("from '@workspace/a.js'");
  });

  it('rewrites imports in inline module scripts and merges into an existing import map', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        `<!DOCTYPE html><html><head>
          <script type="importmap">{"imports":{"vue":"https://cdn.example.com/vue.js"}}</script>
        </head><body>
          <script type="module">import { x } from './x.js'; console.log(x);</script>
        </body></html>`,
        'html'
      ),
      workspaceFile('x.js', 'export const x = 1;', 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    expect(doc.querySelectorAll('script[type="importmap"]')).toHaveLength(1);
    const imports = readImportMap(doc);
    expect(imports.vue).toBe('https://cdn.example.com/vue.js');
    expect(decodeDataUrl(imports['@workspace/x.js'])).toBe('export const x = 1;');
    expect(doc.querySelector('script[type="module"]')?.textContent).toContain(
      "from '@workspace/x.js'"
    );
  });

  it('does not add an import map when there are no local modules', async () => {
    const files = toFiles(
      workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><body><script src="app.js"></script></body></html>',
        'html'
      ),
      workspaceFile('app.js', 'void 0;', 'javascript')
    );

    const doc = parseBundle(await bundleHtmlPreview('index.html', files));
    expect(doc.querySelector('script[type="importmap"]')).toBeNull();
  });

  it('reflects updated workspace content on each bundle (reload)', async () => {
    const html = workspaceFile(
      'index.html',
      '<!DOCTYPE html><html><body><script src="app.js"></script></body></html>',
      'html'
    );
    const first = await bundleHtmlPreview(
      'index.html',
      toFiles(html, workspaceFile('app.js', 'window.v = 1;', 'javascript'))
    );
    const second = await bundleHtmlPreview(
      'index.html',
      toFiles(html, workspaceFile('app.js', 'window.v = 2;', 'javascript'))
    );
    expect(decodeDataUrl(parseBundle(first).querySelector('script')?.getAttribute('src') ?? null)).toBe(
      'window.v = 1;'
    );
    expect(decodeDataUrl(parseBundle(second).querySelector('script')?.getAttribute('src') ?? null)).toBe(
      'window.v = 2;'
    );
  });
});

describe('LivePreview component', () => {
  it('renders empty state when no HTML files exist in workspace', async () => {
    const mockCtx = createMockFileContext({});
    render(
      <AssignmentFileContext.Provider value={mockCtx}>
        <LivePreview />
      </AssignmentFileContext.Provider>
    );

    expect(screen.getByText('No HTML file found')).toBeDefined();
    const createBtn = screen.getByRole('button', { name: /Create index\.html/i });
    expect(createBtn).toBeDefined();

    await act(async () => {
      fireEvent.click(createBtn);
    });
    expect(mockCtx.openFileByName).toHaveBeenCalledWith(
      'index.html',
      expect.objectContaining({ language: 'html', category: 'workspace' })
    );
  });

  it('renders sandboxed iframe with allow-scripts when HTML file exists', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: '<!DOCTYPE html><html><body><h1>Live Preview Test</h1></body></html>',
        language: 'html',
        category: 'workspace',
      },
    };
    const mockCtx = createMockFileContext(files);

    render(
      <AssignmentFileContext.Provider value={mockCtx}>
        <LivePreview />
      </AssignmentFileContext.Provider>
    );

    expect(screen.getByText('Live Preview')).toBeDefined();
    expect(screen.getByText('Live Sandboxed')).toBeDefined();

    const iframe = screen.getByTitle('Live HTML Preview') as HTMLIFrameElement;
    expect(iframe).toBeDefined();
    expect(iframe.getAttribute('sandbox')).toBe('allow-scripts');
    expect(iframe.getAttribute('sandbox')).not.toContain('allow-same-origin');
  });

  it('renders bundled srcDoc with data URL script and keeps the sandbox restricted', async () => {
    const files: Record<string, OpenFile> = {
      'index.html': workspaceFile(
        'index.html',
        '<!DOCTYPE html><html><body><script type="module" defer src="main.js"></script></body></html>',
        'html'
      ),
      'main.js': workspaceFile('main.js', 'window.ran = true;', 'javascript'),
    };
    const mockCtx = createMockFileContext(files);

    render(
      <AssignmentFileContext.Provider value={mockCtx}>
        <LivePreview />
      </AssignmentFileContext.Provider>
    );

    const iframe = screen.getByTitle('Live HTML Preview') as HTMLIFrameElement;
    await waitFor(() => {
      expect(iframe.getAttribute('srcdoc')).toContain('data:text/javascript');
    });
    const srcdoc = iframe.getAttribute('srcdoc') ?? '';
    expect(srcdoc).toContain('type="module"');
    expect(srcdoc).toContain('defer');
    expect(srcdoc).not.toContain('window.ran = true;');
    expect(iframe.getAttribute('sandbox')).toBe('allow-scripts');
  });

  it('derives the selected HTML file from the workspace without a user pick', () => {
    const files: Record<string, OpenFile> = {
      'index.html': workspaceFile('index.html', '<h1>Home</h1>', 'html'),
    };
    const mockCtx = createMockFileContext(files);

    render(
      <AssignmentFileContext.Provider value={mockCtx}>
        <LivePreview />
      </AssignmentFileContext.Provider>
    );

    expect(screen.getByText('(index.html)')).toBeDefined();
  });

  it('toggles viewport mode between desktop, tablet, and mobile', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: '<h1>Viewport Test</h1>',
        language: 'html',
        category: 'workspace',
      },
    };
    const mockCtx = createMockFileContext(files);

    render(
      <AssignmentFileContext.Provider value={mockCtx}>
        <LivePreview />
      </AssignmentFileContext.Provider>
    );

    const tabletBtn = screen.getByRole('button', { name: /Tablet viewport/i });
    fireEvent.click(tabletBtn);

    const mobileBtn = screen.getByRole('button', { name: /Mobile viewport/i });
    fireEvent.click(mobileBtn);

    const desktopBtn = screen.getByRole('button', { name: /Desktop viewport/i });
    fireEvent.click(desktopBtn);
  });

  it('allows clicking reload button to refresh iframe', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: '<h1>Reload Test</h1>',
        language: 'html',
        category: 'workspace',
      },
    };
    const mockCtx = createMockFileContext(files);

    render(
      <AssignmentFileContext.Provider value={mockCtx}>
        <LivePreview />
      </AssignmentFileContext.Provider>
    );

    const reloadBtn = screen.getByRole('button', { name: /Reload preview/i });
    fireEvent.click(reloadBtn);
  });
});
