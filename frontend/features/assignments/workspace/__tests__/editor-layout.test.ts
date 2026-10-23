import { describe, expect, it } from "vitest";
import { computeCloseTab, type EditorLayoutState } from "../editor-layout";

describe("computeCloseTab", () => {
  it("leaves the only pane open and empty when its last tab closes", () => {
    const state: EditorLayoutState = {
      panes: { a: { id: "a", tabs: ["main.py"], activeTab: "main.py" } },
      layout: { type: "pane", paneId: "a" },
      activePaneId: "a",
    };

    expect(computeCloseTab(state, "a", "main.py")).toEqual({
      panes: { a: { id: "a", tabs: [], activeTab: null } },
      layout: { type: "pane", paneId: "a" },
      activePaneId: "a",
    });
  });

  it("collapses a split pane when its last tab closes", () => {
    const state: EditorLayoutState = {
      panes: {
        a: { id: "a", tabs: ["main.py"], activeTab: "main.py" },
        b: { id: "b", tabs: ["utils.py"], activeTab: "utils.py" },
      },
      layout: {
        type: "split",
        direction: "column",
        children: [
          { type: "pane", paneId: "a" },
          { type: "pane", paneId: "b" },
        ],
      },
      activePaneId: "b",
    };

    expect(computeCloseTab(state, "b", "utils.py")).toEqual({
      panes: { a: { id: "a", tabs: ["main.py"], activeTab: "main.py" } },
      layout: { type: "pane", paneId: "a" },
      activePaneId: "a",
    });
  });
});
