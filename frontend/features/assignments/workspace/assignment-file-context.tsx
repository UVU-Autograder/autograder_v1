'use client';

import { createContext, useContext, useRef, useState, useEffect, ReactNode } from 'react';
import {
  computeCloseTab,
  computeMoveTab,
  computeSplitTab,
  createPaneId,
  DragTabData,
  EditorLayoutState,
  OpenFile,
} from './editor-layout';
import { readFilesAsOpenFiles } from './file-utils';
import { WorkspaceVFS } from './vfs/workspace-vfs';
import { Assignment } from '@/features/assignments/types';

export type AssignmentFileContextType = {
  assignment?: Assignment;
  files: Record<string, OpenFile>;
  panes: EditorLayoutState['panes'];
  layout: EditorLayoutState['layout'];
  activePaneId: string;
  dragTab: DragTabData | null;
  vfs: WorkspaceVFS;
  openFileByName: (
    filename: string,
    options?: { content?: string; language?: string; category?: OpenFile['category'] }
  ) => Promise<void>;
  setActiveTab: (paneId: string, filename: string) => void;
  setActivePane: (paneId: string) => void;
  closeTab: (paneId: string, filename: string) => void;
  startTabDrag: (data: DragTabData) => void;
  endTabDrag: () => void;
  splitTabToPane: (
    filename: string,
    sourcePaneId: string,
    targetPaneId: string,
    direction: 'row' | 'column'
  ) => void;
  moveTabToPane: (filename: string, sourcePaneId: string, targetPaneId: string) => void;
  uploadFiles: (files: FileList | File[]) => Promise<void>;
  updateFileContent: (filename: string, content: string) => void;
  deleteFile: (filename: string) => void;
  renameFile: (oldFilename: string, newFilename: string) => boolean;
};

const AssignmentFileContext = createContext<AssignmentFileContextType | null>(null);

const INITIAL_PANE_ID = createPaneId();

const OVERVIEW_FILE: OpenFile = {
  filename: 'Problem Overview',
  content: '',
  language: 'markdown',
  category: 'overview',
};

export function AssignmentFileProvider({
  children,
  assignment,
}: {
  children: ReactNode;
  assignment?: Assignment;
}) {
  // The assignment's details open on load. Seeding the overview as a starter
  // file keeps it from counting as an unsaved change.
  const [vfs] = useState<WorkspaceVFS>(
    () => new WorkspaceVFS(assignment ? [OVERVIEW_FILE] : undefined)
  );
  const [files, setFiles] = useState<Record<string, OpenFile>>(() => vfs.getAllFilesRecord());
  const [editorLayout, setEditorLayout] = useState<EditorLayoutState>(() => {
    const initialTabs = assignment ? [OVERVIEW_FILE.filename] : [];
    return {
      panes: {
        [INITIAL_PANE_ID]: {
          id: INITIAL_PANE_ID,
          tabs: initialTabs,
          activeTab: initialTabs[0] ?? null,
        },
      },
      layout: { type: 'pane', paneId: INITIAL_PANE_ID },
      activePaneId: INITIAL_PANE_ID,
    };
  });
  const [dragTab, setDragTab] = useState<DragTabData | null>(null);
  const dragActionInProgressRef = useRef(false);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (vfs.isDirty()) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [vfs]);

  const openFileByName = async (
    filename: string,
    options?: { content?: string; language?: string; category?: OpenFile['category'] }
  ) => {
    let file = vfs.readFile(filename);

    if (!file) {
      file = vfs.writeFile(filename, options?.content ?? '', {
        language: options?.language,
        category: options?.category ?? 'workspace',
      });
      setFiles(vfs.getAllFilesRecord());
    }

    setEditorLayout((prev) => {
      const pane = prev.panes[prev.activePaneId];
      if (!pane) return prev;

      const alreadyOpen = pane.tabs.includes(filename);
      return {
        ...prev,
        panes: {
          ...prev.panes,
          [prev.activePaneId]: {
            ...pane,
            tabs: alreadyOpen ? pane.tabs : [...pane.tabs, filename],
            activeTab: filename,
          },
        },
      };
    });
  };

  const setActiveTab = (paneId: string, filename: string) => {
    setEditorLayout((prev) => {
      const pane = prev.panes[paneId];
      if (!pane || !pane.tabs.includes(filename)) return prev;
      return {
        ...prev,
        activePaneId: paneId,
        panes: { ...prev.panes, [paneId]: { ...pane, activeTab: filename } },
      };
    });
  };

  const setActivePane = (paneId: string) => {
    setEditorLayout((prev) => ({ ...prev, activePaneId: paneId }));
  };

  const closeTab = (paneId: string, filename: string) => {
    setEditorLayout((prev) => computeCloseTab(prev, paneId, filename) ?? prev);
  };

  const startTabDrag = (data: DragTabData) => {
    setDragTab(data);
  };

  const endTabDrag = () => {
    setDragTab(null);
  };

  const runDragAction = (apply: (prev: EditorLayoutState) => EditorLayoutState | null) => {
    if (dragActionInProgressRef.current) return;
    dragActionInProgressRef.current = true;

    try {
      setEditorLayout((prev) => apply(prev) ?? prev);
      setDragTab(null);
    } finally {
      queueMicrotask(() => {
        dragActionInProgressRef.current = false;
      });
    }
  };

  const splitTabToPane = (
    filename: string,
    sourcePaneId: string,
    targetPaneId: string,
    direction: 'row' | 'column'
  ) => {
    const newPaneId = createPaneId();
    runDragAction((prev) =>
      computeSplitTab(prev, filename, sourcePaneId, targetPaneId, direction, newPaneId)
    );
  };

  const moveTabToPane = (
    filename: string,
    sourcePaneId: string,
    targetPaneId: string
  ) => {
    runDragAction((prev) => computeMoveTab(prev, filename, sourcePaneId, targetPaneId));
  };

  const uploadFiles = async (incoming: FileList | File[]) => {
    const fileArray = Array.from(incoming);
    if (fileArray.length === 0) return;

    const openFiles = await readFilesAsOpenFiles(fileArray);
    const filenames = openFiles.map((file) => file.filename);
    const lastFilename = filenames[filenames.length - 1];

    for (const file of openFiles) {
      vfs.writeFile(file.filename, file.content, {
        category: file.category,
        language: file.language,
        kind: file.kind,
      });
    }

    setFiles(vfs.getAllFilesRecord());

    setEditorLayout((prev) => {
      const pane = prev.panes[prev.activePaneId];
      if (!pane) return prev;

      const nextTabs = [...pane.tabs];
      for (const filename of filenames) {
        if (!nextTabs.includes(filename)) nextTabs.push(filename);
      }

      return {
        ...prev,
        panes: {
          ...prev.panes,
          [prev.activePaneId]: {
            ...pane,
            tabs: nextTabs,
            activeTab: lastFilename,
          },
        },
      };
    });
  };

  const updateFileContent = (filename: string, content: string) => {
    const existing = vfs.readFile(filename);
    if (!existing || existing.content === content) return;

    vfs.writeFile(filename, content);
    setFiles(vfs.getAllFilesRecord());
  };

  const deleteFile = (filename: string) => {
    const deleted = vfs.deleteFile(filename);
    if (!deleted) return;

    setFiles(vfs.getAllFilesRecord());

    setEditorLayout((prev) => {
      let nextLayout = { ...prev };
      let changed = false;
      for (const paneId of Object.keys(prev.panes)) {
        const updated = computeCloseTab(nextLayout, paneId, filename);
        if (updated) {
          nextLayout = updated;
          changed = true;
        }
      }
      return changed ? nextLayout : prev;
    });
  };

  const renameFile = (oldFilename: string, newFilename: string): boolean => {
    const trimmedOld = oldFilename.trim();
    const trimmedNew = newFilename.trim();

    const success = vfs.renameFile(trimmedOld, trimmedNew);
    if (!success) return false;

    setFiles(vfs.getAllFilesRecord());

    setEditorLayout((prev) => {
      const nextPanes = { ...prev.panes };
      let changed = false;

      for (const [paneId, pane] of Object.entries(prev.panes)) {
        const tabIndex = pane.tabs.indexOf(trimmedOld);
        const isActive = pane.activeTab === trimmedOld;

        if (tabIndex !== -1 || isActive) {
          changed = true;
          const nextTabs = [...pane.tabs];
          if (tabIndex !== -1) {
            nextTabs[tabIndex] = trimmedNew;
          }
          nextPanes[paneId] = {
            ...pane,
            tabs: nextTabs,
            activeTab: isActive ? trimmedNew : pane.activeTab,
          };
        }
      }

      return changed ? { ...prev, panes: nextPanes } : prev;
    });

    return true;
  };

  const { panes, layout, activePaneId } = editorLayout;

  return (
    <AssignmentFileContext.Provider
      value={{
        assignment,
        files,
        panes,
        layout,
        activePaneId,
        dragTab,
        vfs,
        openFileByName,
        setActiveTab,
        setActivePane,
        closeTab,
        startTabDrag,
        endTabDrag,
        splitTabToPane,
        moveTabToPane,
        uploadFiles,
        updateFileContent,
        deleteFile,
        renameFile,
      }}
    >
      {children}
    </AssignmentFileContext.Provider>
  );
}

export function useAssignmentFile() {
  const ctx = useContext(AssignmentFileContext);
  if (!ctx) throw new Error('useAssignmentFile must be used within AssignmentFileProvider');
  return ctx;
}
