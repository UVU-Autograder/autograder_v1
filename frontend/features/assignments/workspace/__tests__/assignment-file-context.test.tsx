import React from "react";
import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  AssignmentFileProvider,
  useAssignmentFile,
} from "../assignment-file-context";

describe("AssignmentFileContext - renameFile", () => {
  it("renames a workspace file and updates layout tabs and active tab", async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AssignmentFileProvider>{children}</AssignmentFileProvider>
    );

    const { result } = renderHook(() => useAssignmentFile(), { wrapper });

    await act(async () => {
      await result.current.openFileByName("old_name.py", {
        content: "print('hello')",
        category: "workspace",
      });
    });

    expect(result.current.files["old_name.py"]).toBeDefined();
    expect(result.current.files["old_name.py"].content).toBe("print('hello')");
    expect(result.current.panes[result.current.activePaneId].tabs).toContain("old_name.py");
    expect(result.current.panes[result.current.activePaneId].activeTab).toBe("old_name.py");

    let renameSuccess = false;
    act(() => {
      renameSuccess = result.current.renameFile("old_name.py", "new_name.py");
    });

    expect(renameSuccess).toBe(true);
    expect(result.current.files["old_name.py"]).toBeUndefined();
    expect(result.current.files["new_name.py"]).toBeDefined();
    expect(result.current.files["new_name.py"].content).toBe("print('hello')");
    expect(result.current.files["new_name.py"].language).toBe("python");

    // Layout check
    const activePane = result.current.panes[result.current.activePaneId];
    expect(activePane.tabs).toContain("new_name.py");
    expect(activePane.tabs).not.toContain("old_name.py");
    expect(activePane.activeTab).toBe("new_name.py");
  });

  it("updates file language when extension changes", async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AssignmentFileProvider>{children}</AssignmentFileProvider>
    );

    const { result } = renderHook(() => useAssignmentFile(), { wrapper });

    await act(async () => {
      await result.current.openFileByName("notes.txt", {
        content: "some text",
        category: "workspace",
      });
    });

    expect(result.current.files["notes.txt"].language).toBe("plaintext");

    act(() => {
      result.current.renameFile("notes.txt", "notes.py");
    });

    expect(result.current.files["notes.py"].language).toBe("python");
  });

  it("rejects rename when target filename collides with another file", async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AssignmentFileProvider>{children}</AssignmentFileProvider>
    );

    const { result } = renderHook(() => useAssignmentFile(), { wrapper });

    await act(async () => {
      await result.current.openFileByName("file1.py", {
        content: "one",
        category: "workspace",
      });
      await result.current.openFileByName("file2.py", {
        content: "two",
        category: "workspace",
      });
    });

    let renameSuccess = true;
    act(() => {
      renameSuccess = result.current.renameFile("file1.py", "file2.py");
    });

    expect(renameSuccess).toBe(false);
    expect(result.current.files["file1.py"]).toBeDefined();
    expect(result.current.files["file2.py"]).toBeDefined();
  });

  it("rejects rename on non-workspace files (e.g. overview or provided)", async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AssignmentFileProvider>{children}</AssignmentFileProvider>
    );

    const { result } = renderHook(() => useAssignmentFile(), { wrapper });

    await act(async () => {
      await result.current.openFileByName("Problem Overview", {
        content: "details",
        category: "overview",
      });
    });

    let renameSuccess = true;
    act(() => {
      renameSuccess = result.current.renameFile("Problem Overview", "Custom Overview.md");
    });

    expect(renameSuccess).toBe(false);
    expect(result.current.files["Problem Overview"]).toBeDefined();
  });
});
