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

export function bundleHtmlPreview(
  htmlFilename: string,
  files: Record<string, OpenFile>
): string {
  const htmlFile = files[htmlFilename];
  if (!htmlFile) return '';

  let html = htmlFile.content;

  // 1. Inlines stylesheet links if matching workspace CSS file exists
  // e.g. <link rel="stylesheet" href="style.css"> or <link href="style.css" rel="stylesheet">
  html = html.replace(
    /<link\s+[^>]*rel=["']\s*stylesheet\s*["'][^>]*href=["']([^"']+)["'][^>]*\/?>|<link\s+[^>]*href=["']([^"']+)["'][^>]*rel=["']\s*stylesheet\s*["'][^>]*\/?>/gi,
    (match, href1, href2) => {
      const rawHref = href1 || href2 || '';
      const href = rawHref.trim().replace(/^\.\//, '').replace(/^\//, '').split('?')[0].split('#')[0];
      const cssFile = files[href];
      if (cssFile) {
        return `<style data-inlined="${href}">\n${cssFile.content}\n</style>`;
      }
      return match;
    }
  );

  // 2. Inlines external script tags if matching workspace JS file exists
  // e.g. <script src="script.js"></script> or <script src="script.js"/>
  html = html.replace(
    /<script\s+[^>]*src=["']([^"']+)["'][^>]*>(?:[\s\S]*?<\/script>)?|<script\s+[^>]*src=["']([^"']+)["'][^>]*\/>/gi,
    (match, src1, src2) => {
      const rawSrc = src1 || src2 || '';
      const cleaned = rawSrc.trim().replace(/^\.\//, '').replace(/^\//, '').split('?')[0].split('#')[0];
      const jsFile = files[cleaned];
      if (jsFile) {
        return `<script data-inlined="${cleaned}">\n${jsFile.content}\n</script>`;
      }
      return match;
    }
  );

  // 3. Replaces relative image src with data URLs if image exists in workspace
  html = html.replace(
    /<img\s+([^>]*?)src=["']([^"']+)["']([^>]*?)\/?>/gi,
    (match, before, src, after) => {
      const cleaned = src.trim().replace(/^\.\//, '').replace(/^\//, '').split('?')[0].split('#')[0];
      const imgFile = files[cleaned];
      if (imgFile && imgFile.content.startsWith('data:')) {
        return `<img ${before}src="${imgFile.content}"${after} />`;
      }
      return match;
    }
  );

  return html;
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

  const [selectedHtmlFile, setSelectedHtmlFile] = useState<string>(defaultHtmlFile);
  const [viewport, setViewport] = useState<ViewportMode>('desktop');
  const [refreshKey, setRefreshKey] = useState(0);
  const [debouncedHtml, setDebouncedHtml] = useState<string>('');

  useEffect(() => {
    if (!selectedHtmlFile && defaultHtmlFile) {
      setSelectedHtmlFile(defaultHtmlFile);
    } else if (selectedHtmlFile && !htmlFiles.includes(selectedHtmlFile)) {
      setSelectedHtmlFile(defaultHtmlFile);
    }
  }, [defaultHtmlFile, htmlFiles, selectedHtmlFile]);

  useEffect(() => {
    if (!selectedHtmlFile) {
      setDebouncedHtml('');
      return;
    }
    const timer = setTimeout(() => {
      setDebouncedHtml(bundleHtmlPreview(selectedHtmlFile, files));
    }, 200);

    return () => clearTimeout(timer);
  }, [selectedHtmlFile, files]);

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
    setSelectedHtmlFile('index.html');
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
              onValueChange={(val) => setSelectedHtmlFile(val)}
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
