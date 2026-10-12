'use client';

import { createContext, useContext, useRef, useState, ReactNode } from 'react';
import {
  computeCloseTab,
  computeMoveTab,
  computeSplitTab,
  createPaneId,
  DragTabData,
  EditorLayoutState,
  OpenFile,
} from './editor-layout';
import { languageFromFilename, readFilesAsOpenFiles } from './file-utils';

import { Assignment } from '@/features/assignments/types';

type AssignmentFileContextType = {
  assignment?: Assignment;
  files: Record<string, OpenFile>;
  panes: EditorLayoutState['panes'];
  layout: EditorLayoutState['layout'];
  activePaneId: string;
  dragTab: DragTabData | null;
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

export function AssignmentFileProvider({ children, assignment }: { children: ReactNode; assignment?: Assignment }) {
  const [files, setFiles] = useState<Record<string, OpenFile>>({});
  const [editorLayout, setEditorLayout] = useState<EditorLayoutState>({
    panes: {
      [INITIAL_PANE_ID]: { id: INITIAL_PANE_ID, tabs: [], activeTab: null },
    },
    layout: { type: 'pane', paneId: INITIAL_PANE_ID },
    activePaneId: INITIAL_PANE_ID,
  });
  const [dragTab, setDragTab] = useState<DragTabData | null>(null);
  const dragActionInProgressRef = useRef(false);

  const openFileByName = async (
    filename: string,
    options?: { content?: string; language?: string; category?: OpenFile['category'] }
  ) => {
    let file = files[filename];

    if (!file) {
      file = {
        filename,
        content: options?.content ?? '',
        language: options?.language ?? languageFromFilename(filename),
        category: options?.category ?? 'workspace',
      };
      setFiles((prev) => ({ ...prev, [filename]: file! }));
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

    setFiles((prev) => {
      const next = { ...prev };
      for (const file of openFiles) {
        next[file.filename] = file;
      }
      return next;
    });

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
    setFiles((prev) => {
      const existing = prev[filename];
      if (!existing || existing.content === content) return prev;
      return {
        ...prev,
        [filename]: {
          ...existing,
          content,
        },
      };
    });
  };

  const deleteFile = (filename: string) => {
    setFiles((prev) => {
      const next = { ...prev };
      delete next[filename];
      return next;
    });

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
    if (!trimmedOld || !trimmedNew || trimmedOld === trimmedNew) return false;

    const existing = files[trimmedOld];
    if (!existing || existing.category !== 'workspace') return false;
    if (files[trimmedNew]) return false;

    setFiles((prev) => {
      const target = prev[trimmedOld];
      if (!target || prev[trimmedNew]) return prev;
      const next = { ...prev };
      delete next[trimmedOld];
      next[trimmedNew] = {
        ...target,
        filename: trimmedNew,
        language: target.kind === 'image' ? 'image' : languageFromFilename(trimmedNew),
      };
      return next;
    });

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
