export type OpenFile = {
  filename: string;
  content: string;
  language: string;
};

export type PaneState = {
  id: string;
  tabs: string[];
  activeTab: string | null;
};

export type LayoutNode =
  | { type: "pane"; paneId: string }
  | { type: "split"; direction: "row" | "column"; children: [LayoutNode, LayoutNode] };

export type DragTabData = {
  filename: string;
  sourcePaneId: string;
};

export type EditorLayoutState = {
  panes: Record<string, PaneState>;
  layout: LayoutNode;
  activePaneId: string;
};

export function createPaneId() {
  return `pane-${crypto.randomUUID()}`;
}

export function containsPane(layout: LayoutNode, paneId: string): boolean {
  if (layout.type === "pane") return layout.paneId === paneId;
  return containsPane(layout.children[0], paneId) || containsPane(layout.children[1], paneId);
}

export function splitPane(
  layout: LayoutNode,
  targetPaneId: string,
  direction: "row" | "column",
  newPaneId: string
): LayoutNode {
  if (layout.type === "pane") {
    if (layout.paneId !== targetPaneId) return layout;
    return {
      type: "split",
      direction,
      children: [
        { type: "pane", paneId: targetPaneId },
        { type: "pane", paneId: newPaneId },
      ],
    };
  }

  if (containsPane(layout.children[0], targetPaneId)) {
    return {
      type: "split",
      direction: layout.direction,
      children: [
        splitPane(layout.children[0], targetPaneId, direction, newPaneId),
        layout.children[1],
      ],
    };
  }

  return {
    type: "split",
    direction: layout.direction,
    children: [
      layout.children[0],
      splitPane(layout.children[1], targetPaneId, direction, newPaneId),
    ],
  };
}

export function removePaneFromLayout(layout: LayoutNode, paneId: string): LayoutNode | null {
  if (layout.type === "pane") {
    return layout.paneId === paneId ? null : layout;
  }

  const first = removePaneFromLayout(layout.children[0], paneId);
  const second = removePaneFromLayout(layout.children[1], paneId);

  if (!first && !second) return null;
  if (!first) return second;
  if (!second) return first;

  return { type: "split", direction: layout.direction, children: [first, second] };
}

export function findFirstPaneId(layout: LayoutNode): string | null {
  if (layout.type === "pane") return layout.paneId;
  return findFirstPaneId(layout.children[0]) ?? findFirstPaneId(layout.children[1]);
}

export function computeSplitTab(
  state: EditorLayoutState,
  filename: string,
  sourcePaneId: string,
  targetPaneId: string,
  direction: "row" | "column",
  newPaneId: string
): EditorLayoutState | null {
  const sourcePane = state.panes[sourcePaneId];
  const targetPane = state.panes[targetPaneId];
  if (!sourcePane || !targetPane || !sourcePane.tabs.includes(filename)) return null;

  const sourceTabs = sourcePane.tabs.filter((tab) => tab !== filename);
  const closingIndex = sourcePane.tabs.indexOf(filename);
  const sourceActive =
    sourcePane.activeTab !== filename
      ? sourcePane.activeTab
      : sourceTabs.length === 0
        ? null
        : sourceTabs[Math.min(closingIndex, sourceTabs.length - 1)];

  const nextPanes: Record<string, PaneState> = { ...state.panes };

  nextPanes[sourcePaneId] = { ...sourcePane, tabs: sourceTabs, activeTab: sourceActive };
  if (sourcePaneId !== targetPaneId && sourceTabs.length === 0) {
    delete nextPanes[sourcePaneId];
  }

  nextPanes[newPaneId] = { id: newPaneId, tabs: [filename], activeTab: filename };

  let baseLayout = state.layout;
  if (sourceTabs.length === 0 && sourcePaneId !== targetPaneId) {
    const collapsed = removePaneFromLayout(baseLayout, sourcePaneId);
    if (collapsed) baseLayout = collapsed;
  }

  return {
    panes: nextPanes,
    layout: splitPane(baseLayout, targetPaneId, direction, newPaneId),
    activePaneId: newPaneId,
  };
}

export function computeMoveTab(
  state: EditorLayoutState,
  filename: string,
  sourcePaneId: string,
  targetPaneId: string
): EditorLayoutState | null {
  const sourcePane = state.panes[sourcePaneId];
  const targetPane = state.panes[targetPaneId];
  if (!sourcePane || !targetPane || !sourcePane.tabs.includes(filename)) return null;

  if (sourcePaneId === targetPaneId) {
    return {
      ...state,
      activePaneId: targetPaneId,
      panes: { ...state.panes, [targetPaneId]: { ...targetPane, activeTab: filename } },
    };
  }

  const sourceTabs = sourcePane.tabs.filter((tab) => tab !== filename);
  const closingIndex = sourcePane.tabs.indexOf(filename);
  const sourceActive =
    sourcePane.activeTab !== filename
      ? sourcePane.activeTab
      : sourceTabs.length === 0
        ? null
        : sourceTabs[Math.min(closingIndex, sourceTabs.length - 1)];

  const nextPanes: Record<string, PaneState> = { ...state.panes };

  const targetTabs = targetPane.tabs.includes(filename)
    ? targetPane.tabs
    : [...targetPane.tabs, filename];

  nextPanes[targetPaneId] = { ...targetPane, tabs: targetTabs, activeTab: filename };

  if (sourceTabs.length === 0) {
    delete nextPanes[sourcePaneId];
  } else {
    nextPanes[sourcePaneId] = { ...sourcePane, tabs: sourceTabs, activeTab: sourceActive };
  }

  let nextLayout = state.layout;
  if (sourceTabs.length === 0) {
    const collapsed = removePaneFromLayout(nextLayout, sourcePaneId);
    if (collapsed) nextLayout = collapsed;
  }

  return {
    panes: nextPanes,
    layout: nextLayout,
    activePaneId: targetPaneId,
  };
}

export function computeCloseTab(
  state: EditorLayoutState,
  paneId: string,
  filename: string
): EditorLayoutState | null {
  const pane = state.panes[paneId];
  if (!pane) return null;

  const closingIndex = pane.tabs.indexOf(filename);
  if (closingIndex === -1) return null;

  const nextTabs = pane.tabs.filter((tab) => tab !== filename);
  const nextActive =
    pane.activeTab !== filename
      ? pane.activeTab
      : nextTabs.length === 0
        ? null
        : nextTabs[Math.min(closingIndex, nextTabs.length - 1)];

  if (nextTabs.length > 0) {
    return {
      ...state,
      panes: { ...state.panes, [paneId]: { ...pane, tabs: nextTabs, activeTab: nextActive } },
    };
  }

  const nextPanes = { ...state.panes };
  delete nextPanes[paneId];

  const nextLayout = removePaneFromLayout(state.layout, paneId);
  if (!nextLayout) return null;

  const nextActivePaneId =
    state.activePaneId !== paneId
      ? state.activePaneId
      : findFirstPaneId(nextLayout) ?? state.activePaneId;

  return {
    panes: nextPanes,
    layout: nextLayout,
    activePaneId: nextActivePaneId,
  };
}
