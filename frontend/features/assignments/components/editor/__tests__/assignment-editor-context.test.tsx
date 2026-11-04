import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssignmentEditorProvider, useAssignmentEditor } from "../assignment-editor-context";
import { apiClient } from "@/lib/api-client";
import type { StaffAssignmentSetup } from "@/features/assignments/types";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/features/assignments/api", () => ({
  getConceptsMetadata: vi.fn().mockResolvedValue({}), deleteStaffAssignment: vi.fn(),
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
    <button onClick={() => editor.updateTestSuiteCode("# updated tests\n")}>Change tests</button>
    <button onClick={editor.handleSave}>Save setup</button>
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
});
