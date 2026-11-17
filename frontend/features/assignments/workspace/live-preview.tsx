'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  RotateCwIcon,
  MonitorIcon,
  TabletIcon,
  SmartphoneIcon,
  GlobeIcon,
  FileCodeIcon,
  PlusIcon,
} from 'lucide-react';
import { init as initEsModuleLexer, parse as parseEsModule } from 'es-module-lexer';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAssignmentFile } from './assignment-file-context';
import type { OpenFile } from './editor-layout';

type ViewportMode = 'desktop' | 'tablet' | 'mobile';

const MODULE_ID_PREFIX = '@workspace/';

const JS_MIME_TYPES = new Set([
  '',
  'text/javascript',
  'application/javascript',
  'application/x-javascript',
  'text/ecmascript',
  'application/ecmascript',
  'text/jscript',
  'text/livescript',
]);

/** True for references that point into the workspace (not absolute URLs, data URLs, etc.). */
function isLocalReference(ref: string): boolean {
  const value = ref.trim();
  if (!value || value.startsWith('#') || value.startsWith('//')) return false;
  return !/^[a-zA-Z][a-zA-Z\d+.-]*:/.test(value);
}

function dirname(path: string): string {
  const index = path.lastIndexOf('/');
  return index === -1 ? '' : path.slice(0, index);
}

/**
 * Resolves a local reference against a workspace directory into a normalized
 * workspace filename. A leading `/` resolves from the workspace root; query
 * strings and fragments are ignored.
 */
function resolveWorkspacePath(baseDir: string, ref: string): string {
  const cleaned = ref.trim().split('#')[0].split('?')[0];
  const segments = cleaned.startsWith('/') || !baseDir ? [] : baseDir.split('/');
  for (const part of cleaned.split('/')) {
    if (part === '' || part === '.') continue;
    if (part === '..') {
      segments.pop();
    } else {
      segments.push(part);
    }
  }
  return segments.join('/');
}

function lookupLocalFile(
  files: Record<string, OpenFile>,
  baseDir: string,
  ref: string
): { path: string; file: OpenFile } | null {
  if (!isLocalReference(ref)) return null;
  const path = resolveWorkspacePath(baseDir, ref);
  const file = path ? files[path] : undefined;
  return file ? { path, file } : null;
}

function toTextDataUrl(mime: string, content: string): string {
  return `data:${mime};charset=utf-8,${encodeURIComponent(content)}`;
}

function isModuleScript(script: Element): boolean {
  return (script.getAttribute('type') ?? '').trim().toLowerCase() === 'module';
}

function isClassicScript(script: Element): boolean {
  const type = (script.getAttribute('type') ?? '').trim().toLowerCase();
  return JS_MIME_TYPES.has(type);
}

interface ModuleContext {
  files: Record<string, OpenFile>;
  /** Import map entries: stable workspace identifier -> data URL. */
  importMap: Record<string, string>;
  /** Workspace paths already processed (guards import cycles). */
  visited: Set<string>;
}

function moduleDataUrl(source: string): string {
  return toTextDataUrl('text/javascript', source);
}

/**
 * Rewrites local import specifiers in an ES module's source to stable
 * `@workspace/<path>` identifiers and registers every reachable local module
 * in the import map. Non-local (bare, absolute URL) and missing imports are
 * left untouched.
 */
function rewriteModuleImports(
  source: string,
  fromDir: string,
  ctx: ModuleContext
): string {
  let imports: ReturnType<typeof parseEsModule>[0];
  try {
    imports = parseEsModule(source)[0];
  } catch {
    return source;
  }

  const edits: Array<{ start: number; end: number; text: string }> = [];

  for (const imp of imports) {
    if (imp.type === 'import-meta') continue;
    if (imp.type === 'dynamic' && (imp.glob || imp.specifier === undefined)) continue;
    const specifier = imp.specifier;
    if (!specifier) continue;

    const target = lookupLocalFile(ctx.files, fromDir, specifier);
    if (!target) continue;

    registerModule(target.path, ctx);
    const id = `${MODULE_ID_PREFIX}${target.path}`;

    let { start, end } = imp;
    if (imp.type === 'dynamic') {
      // Dynamic import ranges include the surrounding quotes of the literal.
      const raw = source.slice(start, end);
      const quote = raw[0];
      if (raw.length < 2 || (quote !== '"' && quote !== "'") || raw[raw.length - 1] !== quote) {
        continue;
      }
      start += 1;
      end -= 1;
    }
    edits.push({ start, end, text: id });
  }

  let result = source;
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    result = result.slice(0, edit.start) + edit.text + result.slice(edit.end);
  }
  return result;
}

function registerModule(path: string, ctx: ModuleContext): void {
  if (ctx.visited.has(path)) return;
  ctx.visited.add(path);
  const file = ctx.files[path];
  if (!file) return;
  const rewritten = rewriteModuleImports(file.content, dirname(path), ctx);
  ctx.importMap[`${MODULE_ID_PREFIX}${path}`] = moduleDataUrl(rewritten);
}

/** Data URL for a workspace module; shared with the import map so a module is only instantiated once. */
function moduleUrlForPath(path: string, ctx: ModuleContext): string {
  registerModule(path, ctx);
  return ctx.importMap[`${MODULE_ID_PREFIX}${path}`];
}

function injectImportMap(doc: Document, importMap: Record<string, string>): void {
  if (Object.keys(importMap).length === 0) return;

  for (const existing of Array.from(doc.querySelectorAll('script[type="importmap"]'))) {
    try {
      const parsed = JSON.parse(existing.textContent ?? '{}') as {
        imports?: Record<string, string>;
      };
      parsed.imports = { ...parsed.imports, ...importMap };
      existing.textContent = JSON.stringify(parsed).replace(/</g, '\\u003c');
      return;
    } catch {
      // Invalid existing import map: fall through and add our own.
    }
  }

  const script = doc.createElement('script');
  script.setAttribute('type', 'importmap');
  script.setAttribute('data-workspace-importmap', '');
  script.textContent = JSON.stringify({ imports: importMap }).replace(/</g, '\\u003c');
  // Import maps must precede every module script, so insert first in <head>.
  const head = doc.head ?? doc.documentElement;
  head.insertBefore(script, head.firstChild);
}

/**
 * Bundles a workspace HTML file into a self-contained `srcDoc` string for the
 * sandboxed preview iframe.
 *
 * Local stylesheets, scripts, images and ES modules are replaced by data URLs
 * so element attributes (defer, async, type, crossorigin, ...) and load
 * ordering are preserved. Local imports in ES modules are rewritten to stable
 * `@workspace/...` identifiers resolved through an import map. References to
 * files that are missing from the workspace are left untouched.
 */
export async function bundleHtmlPreview(
  htmlFilename: string,
  files: Record<string, OpenFile>
): Promise<string> {
  const htmlFile = files[htmlFilename];
  if (!htmlFile) return '';

  await initEsModuleLexer();

  const doc = new DOMParser().parseFromString(htmlFile.content, 'text/html');
  const htmlDir = dirname(htmlFilename);
  const ctx: ModuleContext = { files, importMap: {}, visited: new Set() };

  // 1. Local stylesheets keep their <link> and get a data URL href.
  for (const link of Array.from(doc.querySelectorAll('link[href]'))) {
    const rel = (link.getAttribute('rel') ?? '').toLowerCase().split(/\s+/);
    if (!rel.includes('stylesheet')) continue;
    const target = lookupLocalFile(files, htmlDir, link.getAttribute('href') ?? '');
    if (!target) continue;
    link.setAttribute('href', toTextDataUrl('text/css', target.file.content));
    link.setAttribute('data-inlined', target.path);
  }

  // 2. Scripts keep all their attributes; only the source location changes.
  for (const script of Array.from(doc.querySelectorAll('script'))) {
    const moduleScript = isModuleScript(script);
    if (!moduleScript && !isClassicScript(script)) continue;

    const src = script.getAttribute('src');
    if (src === null) {
      if (moduleScript && script.textContent) {
        script.textContent = rewriteModuleImports(script.textContent, htmlDir, ctx);
      }
      continue;
    }

    const target = lookupLocalFile(files, htmlDir, src);
    if (!target) continue;

    const url = moduleScript
      ? moduleUrlForPath(target.path, ctx)
      : toTextDataUrl('text/javascript', target.file.content);
    script.setAttribute('src', url);
    script.setAttribute('data-inlined', target.path);
  }

  // 3. Images backed by workspace data URLs (or SVG text) are embedded.
  for (const img of Array.from(doc.querySelectorAll('img[src]'))) {
    const target = lookupLocalFile(files, htmlDir, img.getAttribute('src') ?? '');
    if (!target) continue;
    const { content } = target.file;
    if (content.startsWith('data:')) {
      img.setAttribute('src', content);
    } else if (target.path.toLowerCase().endsWith('.svg') && content.trim()) {
      img.setAttribute('src', toTextDataUrl('image/svg+xml', content));
    }
  }

  injectImportMap(doc, ctx.importMap);

  const doctype = doc.doctype ? '<!DOCTYPE html>\n' : '';
  return `${doctype}${doc.documentElement.outerHTML}`;
}

export function LivePreview() {
  const { files, openFileByName, assignment } = useAssignmentFile();

  const htmlFiles = useMemo(() => {
    return Object.values(files)
      .filter(
        (f) =>
          f.category === 'workspace' &&
          f.filename.toLowerCase().endsWith('.html')
      )
      .map((f) => f.filename)
      .sort((a, b) => {
        if (a === 'index.html') return -1;
        if (b === 'index.html') return 1;
        return a.localeCompare(b);
      });
  }, [files]);

  const defaultHtmlFile = useMemo(() => {
    const entrypoint = assignment?.config?.bundle?.entrypoint;
    if (entrypoint && htmlFiles.includes(entrypoint)) {
      return entrypoint;
    }
    if (htmlFiles.includes('index.html')) {
      return 'index.html';
    }
    return htmlFiles[0] || '';
  }, [htmlFiles, assignment]);

  // State only records an explicit user pick; the effective selection is derived.
  const [pickedHtmlFile, setPickedHtmlFile] = useState<string>('');
  const [viewport, setViewport] = useState<ViewportMode>('desktop');
  const [refreshKey, setRefreshKey] = useState(0);
  const [bundled, setBundled] = useState<{ file: string; html: string }>({
    file: '',
    html: '',
  });

  const selectedHtmlFile = htmlFiles.includes(pickedHtmlFile)
    ? pickedHtmlFile
    : defaultHtmlFile;

  useEffect(() => {
    if (!selectedHtmlFile) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      bundleHtmlPreview(selectedHtmlFile, files)
        .then((html) => {
          if (!cancelled) setBundled({ file: selectedHtmlFile, html });
        })
        .catch(() => {
          if (!cancelled) setBundled({ file: selectedHtmlFile, html: '' });
        });
    }, 200);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [selectedHtmlFile, files, refreshKey]);

  // Never show output bundled for a different file.
  const debouncedHtml =
    selectedHtmlFile && bundled.file === selectedHtmlFile ? bundled.html : '';

  const handleCreateDefaultHtml = async () => {
    await openFileByName('index.html', {
      content: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document</title>
</head>
<body>
  <h1>Hello, World!</h1>
</body>
</html>`,
      language: 'html',
      category: 'workspace',
    });
    setPickedHtmlFile('index.html');
  };

  const viewportContainerStyles: Record<ViewportMode, string> = {
    desktop: 'w-full h-full',
    tablet: 'w-[768px] h-full shadow-lg border border-border rounded-md overflow-hidden',
    mobile: 'w-[375px] h-full shadow-lg border border-border rounded-md overflow-hidden',
  };

  return (
    <div className="flex flex-col h-full w-full min-h-0 min-w-0 bg-muted/30">
      {/* Header Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-border bg-card text-card-foreground shrink-0 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <GlobeIcon className="size-4 text-primary shrink-0" />
          <span className="text-xs font-semibold shrink-0">Live Preview</span>

          {htmlFiles.length > 1 ? (
            <Select
              value={selectedHtmlFile}
              onValueChange={(val) => setPickedHtmlFile(val)}
            >
              <SelectTrigger className="h-7 text-xs font-mono px-2 py-0 w-36">
                <SelectValue placeholder="Select HTML file" />
              </SelectTrigger>
              <SelectContent>
                {htmlFiles.map((f) => (
                  <SelectItem key={f} value={f} className="text-xs font-mono">
                    {f}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : selectedHtmlFile ? (
            <span className="text-xs font-mono text-muted-foreground truncate">
              ({selectedHtmlFile})
            </span>
          ) : null}

          <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Live Sandboxed
          </span>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <div className="flex items-center border border-border rounded-md p-0.5 bg-muted/50">
            <Button
              type="button"
              variant={viewport === 'desktop' ? 'secondary' : 'ghost'}
              size="icon-xs"
              onClick={() => setViewport('desktop')}
              title="Desktop viewport (100%)"
              aria-label="Desktop viewport"
              className="h-6 w-6"
            >
              <MonitorIcon className="size-3.5" />
            </Button>
            <Button
              type="button"
              variant={viewport === 'tablet' ? 'secondary' : 'ghost'}
              size="icon-xs"
              onClick={() => setViewport('tablet')}
              title="Tablet viewport (768px)"
              aria-label="Tablet viewport"
              className="h-6 w-6"
            >
              <TabletIcon className="size-3.5" />
            </Button>
            <Button
              type="button"
              variant={viewport === 'mobile' ? 'secondary' : 'ghost'}
              size="icon-xs"
              onClick={() => setViewport('mobile')}
              title="Mobile viewport (375px)"
              aria-label="Mobile viewport"
              className="h-6 w-6"
            >
              <SmartphoneIcon className="size-3.5" />
            </Button>
          </div>

          <Button
            type="button"
            variant="outline"
            size="icon-xs"
            onClick={() => setRefreshKey((k) => k + 1)}
            title="Reload preview"
            aria-label="Reload preview"
            className="h-7 w-7"
          >
            <RotateCwIcon className="size-3.5" />
          </Button>
        </div>
      </div>

      {/* Preview Viewport */}
      <div className="flex-1 min-h-0 w-full overflow-auto flex items-center justify-center p-2 bg-muted/40">
        {selectedHtmlFile ? (
          <div
            className={`transition-all duration-200 flex flex-col bg-white ${viewportContainerStyles[viewport]}`}
          >
            <iframe
              key={`${selectedHtmlFile}-${refreshKey}`}
              srcDoc={
                debouncedHtml ||
                '<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;height:80vh;color:#888;">Empty document</body></html>'
              }
              sandbox="allow-scripts"
              title="Live HTML Preview"
              className="w-full h-full border-0 bg-white"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center gap-3 p-6 text-center max-w-sm rounded-lg border border-border bg-card shadow-xs">
            <FileCodeIcon className="size-8 text-muted-foreground" />
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-foreground">
                No HTML file found
              </h3>
              <p className="text-xs text-muted-foreground">
                Create an <code>index.html</code> file in your workspace to render
                a live sandboxed web preview.
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              onClick={handleCreateDefaultHtml}
              className="gap-1.5"
            >
              <PlusIcon className="size-3.5" /> Create index.html
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export default LivePreview;
