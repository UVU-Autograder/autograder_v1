import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
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

describe('bundleHtmlPreview', () => {
  it('returns empty string if HTML file does not exist', () => {
    expect(bundleHtmlPreview('missing.html', {})).toBe('');
  });

  it('inlines referenced workspace CSS files', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: '<!DOCTYPE html><html><head><link rel="stylesheet" href="style.css"></head><body><h1>Hi</h1></body></html>',
        language: 'html',
        category: 'workspace',
      },
      'style.css': {
        filename: 'style.css',
        content: 'h1 { color: red; }',
        language: 'css',
        category: 'workspace',
      },
    };

    const bundled = bundleHtmlPreview('index.html', files);
    expect(bundled).toContain('<style data-inlined="style.css">');
    expect(bundled).toContain('h1 { color: red; }');
    expect(bundled).not.toContain('<link rel="stylesheet" href="style.css">');
  });

  it('inlines referenced workspace JS files', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: '<!DOCTYPE html><html><body><h1>Hi</h1><script src="app.js"></script></body></html>',
        language: 'html',
        category: 'workspace',
      },
      'app.js': {
        filename: 'app.js',
        content: 'console.log("running");',
        language: 'javascript',
        category: 'workspace',
      },
    };

    const bundled = bundleHtmlPreview('index.html', files);
    expect(bundled).toContain('<script data-inlined="app.js">');
    expect(bundled).toContain('console.log("running");');
    expect(bundled).not.toContain('<script src="app.js"></script>');
  });

  it('replaces relative image src with workspace image data URLs', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: '<!DOCTYPE html><html><body><img src="logo.png" alt="Logo"></body></html>',
        language: 'html',
        category: 'workspace',
      },
      'logo.png': {
        filename: 'logo.png',
        content: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==',
        language: 'image',
        category: 'workspace',
        kind: 'image',
      },
    };

    const bundled = bundleHtmlPreview('index.html', files);
    expect(bundled).toContain('src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="');
  });
  it('inlines stylesheet and script tags with query parameters and self-closing syntax', () => {
    const files: Record<string, OpenFile> = {
      'index.html': {
        filename: 'index.html',
        content: `<!DOCTYPE html><html><head>
          <link rel="stylesheet" href="./style.css?v=2">
        </head><body>
          <script src="./app.js?v=4" />
        </body></html>`,
        language: 'html',
        category: 'workspace',
      },
      'style.css': {
        filename: 'style.css',
        content: 'body { margin: 0; }',
        language: 'css',
        category: 'workspace',
      },
      'app.js': {
        filename: 'app.js',
        content: 'window.__loaded = true;',
        language: 'javascript',
        category: 'workspace',
      },
    };

    const bundled = bundleHtmlPreview('index.html', files);
    expect(bundled).toContain('<style data-inlined="style.css">');
    expect(bundled).toContain('body { margin: 0; }');
    expect(bundled).toContain('<script data-inlined="app.js">');
    expect(bundled).toContain('window.__loaded = true;');
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
