import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssignmentEditorProvider, useAssignmentEditor } from "../assignment-editor-context";
import { apiClient } from "@/lib/api-client";
import { syncStaffTests } from "@/features/assignments/api";
import type { StaffAssignmentSetup } from "@/features/assignments/types";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/features/assignments/api", () => ({
  getConceptsMetadata: vi.fn().mockResolvedValue({}), deleteStaffAssignment: vi.fn(), syncStaffTests: vi.fn(),
}));
vi.mock("@/lib/api-client", () => ({
  apiClient: { get: vi.fn(), getText: vi.fn(), put: vi.fn(), postForm: vi.fn() },
}));

let setup: StaffAssignmentSetup;

function Controls() {
  const editor = useAssignmentEditor();
  if (editor.loading) return <p>Loading</p>;
  return <>
    <button onClick={() => editor.setTitle("Updated title")}>Change title</button>
    <button onClick={() => editor.setLanguage("web")}>Switch to Web</button>
    <button onClick={() => editor.updateTestSuiteCode("# updated tests\n")}>Change tests</button>
    <button onClick={() => void editor.syncTestsFromSource("def test(): pass")}>Sync tests</button>
    <span data-testid="error">{editor.errorMessage}</span>
    <span data-testid="framework">{editor.testFramework}</span>
    <span data-testid="suite-code">{editor.testSuiteCode}</span>
    <button onClick={editor.handleSave}>Save setup</button>
    <span data-testid="scoring-items-count">{editor.scoringItems.length}</span>
    {editor.scoringItems.map((item) => (
      <span key={item.key} data-testid={`item-${item.key}`}>
        {item.comparison_mode}:{String(item.tolerance)}
      </span>
    ))}
    {editor.scoringItems.map((item) => (
      <span key={`meta-${item.key}`} data-testid={`meta-${item.key}`}>
        {item.label}|{item.points}|{(item.inputs || []).join(",")}|{(item.outputs || []).join(",")}
      </span>
    ))}
  </>;
}

async function openEditor() {
  render(<AssignmentEditorProvider courseId="cs1410" assignmentId="lab1"><Controls /></AssignmentEditorProvider>);
  await screen.findByRole("button", { name: "Change title" });
}

beforeEach(() => {
  vi.clearAllMocks();
  setup = {
    course_id: "cs1410", assignment_id: "lab1", title: "Lab 1", language: "python",
    sandbox_enabled: true, canvas_ref: null, base_points: 10, extra_credit_points: 0,
    entrypoint_path: "main.py", scoring_items: [], artifacts: [
      { artifact_key: "suite_primary", artifact_type: "pytest_file", display_filename: "test_main.py", size_bytes: 10 },
    ],
    config: {
      bundle: { entrypoint: "main.py", file_requirements: [{ paths: ["main.py"] }] },
      scoring_items: [],
      artifacts: { suite_primary: { type: "pytest_file", display_filename: "test_main.py" } },
      completion_requirements: [{ key: "objective", label: "Complete one test", test_keys: ["main"], minimum_passed: 1 }],
    },
  };
  vi.mocked(apiClient.get).mockImplementation(async (path) => path.endsWith("/concepts")
    ? { default_concepts: [], modules: [] } : setup);
  vi.mocked(apiClient.getText).mockResolvedValue("# original tests\n");
  vi.mocked(apiClient.put).mockResolvedValue({});
  vi.mocked(apiClient.postForm).mockResolvedValue({ data: {}, response: new Response() });
});
afterEach(cleanup);

async function saveTitle() {
  fireEvent.click(screen.getByRole("button", { name: "Change title" }));
  fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
  await waitFor(() => expect(apiClient.put).toHaveBeenCalled());
  return vi.mocked(apiClient.put).mock.calls[0][1] as { config: StaffAssignmentSetup["config"] };
}

describe("assignment setup saves", () => {
  it("preserves completion requirements when changing unrelated metadata", async () => {
    await openEditor();
    expect((await saveTitle()).config.completion_requirements).toEqual(setup.config.completion_requirements);
  });

  it("keeps the execution language aligned with the selected assignment language", async () => {
    setup.language = "cpp";
    await openEditor();
    expect((await saveTitle()).config.bundle).toMatchObject({ language: "cpp" });
  });

  it("uses the existing test suite without inventing a missing assignment_tests artifact", async () => {
    await openEditor();
    expect(Object.keys((await saveTitle()).config.artifacts || {})).toEqual(["suite_primary"]);
  });

  it("preserves the uploaded test filename when saving edited tests", async () => {
    await openEditor();
    fireEvent.click(screen.getByRole("button", { name: "Change tests" }));
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
    await waitFor(() => expect(apiClient.put).toHaveBeenCalled());
    const form = vi.mocked(apiClient.postForm).mock.calls[0][1];
    expect((form.get("file") as File).name).toBe("test_main.py");
    expect(form.get("artifact_key")).toBe("suite_primary");
  });

  it("merges backend sync results, preserving points and labels and adding missing keys", async () => {
    setup.config = {
      ...setup.config,
      scoring_items: [
        { key: "kept", label: "Kept label", points: 7, extra_credit: false, item_type: "pytest", pytest_marker: "ag_kept", rubric_group_key: null },
      ],
    };
    vi.mocked(syncStaffTests).mockResolvedValue({
      items: [
        { key: "kept", outputs: ["42"], comparison_mode: "exact", tolerance: 0.005 },
        { key: "fresh", inputs: ["1"], outputs: ["2"], comparison_mode: "numeric_tolerance", tolerance: 0.001 },
      ],
    });
    await openEditor();
    fireEvent.click(screen.getByRole("button", { name: "Sync tests" }));

    await waitFor(() => expect(screen.getByTestId("item-fresh")).toBeDefined());
    expect(syncStaffTests).toHaveBeenCalledWith("cs1410", "lab1", "def test(): pass");
    expect(screen.getByTestId("item-kept").textContent).toBe("exact:0.005");
    expect(screen.getByTestId("meta-kept").textContent).toBe("Kept label|7||42");
    expect(screen.getByTestId("item-fresh").textContent).toBe("numeric_tolerance:0.001");
    expect(screen.getByTestId("meta-fresh").textContent).toBe("Fresh Test|10|1|2");
  });

  it("surfaces a sync error without partially updating scoring items", async () => {
    setup.config = {
      ...setup.config,
      scoring_items: [
        { key: "kept", label: "Kept label", points: 7, extra_credit: false, item_type: "pytest", pytest_marker: "ag_kept", rubric_group_key: null },
      ],
    };
    vi.mocked(syncStaffTests).mockRejectedValue(new Error("Invalid Python syntax on line 1"));
    await openEditor();
    fireEvent.click(screen.getByRole("button", { name: "Sync tests" }));

    await waitFor(() => expect(screen.getByTestId("error").textContent).toBe("Invalid Python syntax on line 1"));
    expect(screen.getByTestId("scoring-items-count").textContent).toBe("1");
    expect(screen.getByTestId("meta-kept").textContent).toBe("Kept label|7||");
  });

  it("never calls the sync endpoint for non-Python assignments", async () => {
    setup.language = "cpp";
    setup.config = { ...setup.config, test_framework: "gtest" };
    await openEditor();
    fireEvent.click(screen.getByRole("button", { name: "Sync tests" }));
    await Promise.resolve();
    expect(syncStaffTests).not.toHaveBeenCalled();
  });

  it("uses a gtest starter, not a pytest stub, for a C++ assignment missing its suite", async () => {
    setup.language = "cpp";
    setup.artifacts = [];
    setup.config = { ...setup.config, test_framework: "gtest", artifacts: { model_entrypoint: { type: "model_solution" } } };
    vi.mocked(apiClient.getText).mockRejectedValue(new Error("not found"));
    await openEditor();
    expect(screen.getByTestId("framework").textContent).toBe("gtest");
    expect(screen.getByTestId("suite-code").textContent).toContain("#include <gtest/gtest.h>");
    expect(screen.getByTestId("suite-code").textContent).not.toContain("pytest");
  });

  it("uploads gtest suites as test_file named tests.cpp and persists test_framework", async () => {
    setup.language = "cpp";
    setup.artifacts = [];
    setup.config = { ...setup.config, test_framework: "gtest", artifacts: { model_entrypoint: { type: "model_solution" } } };
    vi.mocked(apiClient.getText).mockRejectedValue(new Error("not found"));
    await openEditor();
    fireEvent.click(screen.getByRole("button", { name: "Change tests" }));
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
    await waitFor(() => expect(apiClient.put).toHaveBeenCalled());
    const form = vi.mocked(apiClient.postForm).mock.calls[0][1];
    expect((form.get("file") as File).name).toBe("tests.cpp");
    expect(form.get("artifact_type")).toBe("test_file");
    const config = (vi.mocked(apiClient.put).mock.calls[0][1] as { config: StaffAssignmentSetup["config"] }).config;
    expect(config.test_framework).toBe("gtest");
    expect(config.artifacts?.assignment_tests).toMatchObject({ type: "test_file", display_filename: "tests.cpp" });
  });

  it("loads a web suite from a test_file artifact and defaults to jsdom", async () => {
    setup.language = "web";
    setup.artifacts = [{ artifact_key: "assignment_tests", artifact_type: "test_file", display_filename: "tests.cjs", size_bytes: 10 }];
    setup.config = { ...setup.config, artifacts: { assignment_tests: { type: "test_file", display_filename: "tests.cjs" } } };
    vi.mocked(apiClient.getText).mockResolvedValue("module.exports = () => {};\n");
    await openEditor();
    expect(screen.getByTestId("framework").textContent).toBe("jsdom");
    expect(screen.getByTestId("suite-code").textContent).toBe("module.exports = () => {};\n");
  });

  it("saves a compatible suite under a new key when changing language", async () => {
    setup.artifacts[0].artifact_key = "assignment_tests";
    setup.config.artifacts = { assignment_tests: { type: "pytest_file", display_filename: "test_main.py" } };
    await openEditor();
    fireEvent.click(screen.getByRole("button", { name: "Switch to Web" }));
    expect(screen.getByTestId("suite-code").textContent).toContain("module.exports");
    const payload = await saveTitle();
    const form = vi.mocked(apiClient.postForm).mock.calls[0][1];
    expect(form.get("artifact_key")).toBe("assignment_tests_jsdom");
    expect(form.get("artifact_type")).toBe("test_file");
    expect((form.get("file") as File).name).toBe("tests.cjs");
    expect(payload.config.artifacts).toEqual({
      assignment_tests_jsdom: { type: "test_file", display_filename: "tests.cjs" },
    });
  });

  it("does not load or upload a suite file for the io framework", async () => {
    setup.language = "c";
    setup.artifacts = [{ artifact_key: "model_entrypoint", artifact_type: "model_solution", display_filename: "main.c", size_bytes: 10 }];
    setup.config = { ...setup.config, test_framework: "io", artifacts: { model_entrypoint: { type: "model_solution" } } };
    await openEditor();
    expect(apiClient.getText).not.toHaveBeenCalled();
    expect(screen.getByTestId("framework").textContent).toBe("io");
    const saved = await saveTitle();
    expect(apiClient.postForm).not.toHaveBeenCalled();
    expect(saved.config.test_framework).toBe("io");
    expect(Object.keys(saved.config.artifacts || {})).toEqual(["model_entrypoint"]);
  });

  it("inherits assignment-level comparison_mode and tolerance on initial load", async () => {
    setup.config = {
      ...setup.config,
      comparison_mode: "exact",
      tolerance: 0.02,
      scoring_items: [
        { key: "inherited_item", label: "Inherited Item", points: 10, extra_credit: false, item_type: "pytest", pytest_marker: "ag_inherited_item", rubric_group_key: null },
      ],
    };
    await openEditor();
    expect(screen.getByTestId("item-inherited_item").textContent).toBe("exact:0.02");
  });
});
