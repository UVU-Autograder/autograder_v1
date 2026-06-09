'use client';

import { createContext, useContext, useRef, useState, ReactNode } from 'react';
import { getFile } from './api';
import {
  computeCloseTab,
  computeMoveTab,
  computeSplitTab,
  createPaneId,
  DragTabData,
  EditorLayoutState,
  OpenFile,
} from './editor-layout';

type AssignmentFileContextType = {
  files: Record<string, OpenFile>;
  panes: EditorLayoutState['panes'];
  layout: EditorLayoutState['layout'];
  activePaneId: string;
  dragTab: DragTabData | null;
  openFileByName: (filename: string) => Promise<void>;
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
};

const AssignmentFileContext = createContext<AssignmentFileContextType | null>(null);

const INITIAL_PANE_ID = createPaneId();

export function AssignmentFileProvider({ children }: { children: ReactNode }) {
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

  const openFileByName = async (filename: string) => {
    let file = files[filename];

    if (!file) {
      const response = await getFile(filename);
      const content = await response.text();
      const language = filename.endsWith('.py') ? 'python' : 'plaintext';
      file = { filename, content, language };
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

  const { panes, layout, activePaneId } = editorLayout;

  return (
    <AssignmentFileContext.Provider
      value={{
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
