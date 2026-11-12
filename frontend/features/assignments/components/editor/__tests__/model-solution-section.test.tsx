import React from "react";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssignmentEditorProvider, useAssignmentEditor } from "../assignment-editor-context";
import { AssignmentEditor } from "../assignment-editor";
import { apiClient } from "@/lib/api-client";
import type { StaffArtifact } from "@/features/assignments/types";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/features/assignments/api", () => ({
  getConceptsMetadata: vi.fn().mockResolvedValue({}),
  deleteStaffAssignment: vi.fn(),
}));
vi.mock("@/lib/api-client", () => ({
  apiClient: { get: vi.fn(), getText: vi.fn(), postForm: vi.fn(), post: vi.fn() },
}));
vi.mock("../metadata-section", () => ({ MetadataSection: () => null }));
vi.mock("../scoring-rules-section", () => ({ ScoringRulesSection: () => null }));
vi.mock("@/components/monaco-editor", () => ({
  default: ({ value, language, onChange }: {
    value: string; language: string; onChange: (value: string) => void;
  }) => (
    <textarea aria-label="Code editor" data-language={language} value={value}
      onChange={(event) => onChange(event.target.value)} />
  ),
}));

const artifactsUrl = "/staff/courses/cs1410/assignments/lab1/artifacts";
let artifacts: StaffArtifact[];

function UnsavedChangeControl() {
  const { setTitle } = useAssignmentEditor();
  return <button onClick={() => setTitle("Unsaved title")}>Change assignment title</button>;
}

async function openPage() {
  render(
    <AssignmentEditorProvider courseId="cs1410" assignmentId="lab1">
      <AssignmentEditor />
      <UnsavedChangeControl />
    </AssignmentEditorProvider>,
  );
  const tab = await screen.findByRole("tab", { name: "Model Solution" });
  fireEvent.mouseDown(tab, { button: 0, ctrlKey: false });
  await screen.findByRole("button", { name: "Create File" });
}

function createFile(filename: string) {
  fireEvent.change(screen.getByLabelText("New File Name"), { target: { value: filename } });
  fireEvent.click(screen.getByRole("button", { name: "Create File" }));
}

beforeEach(() => {
  vi.clearAllMocks();
  artifacts = [];
  vi.mocked(apiClient.get).mockImplementation(async (path) => {
    if (path.endsWith("/concepts")) return { default_concepts: [], modules: [] };
    return { title: "Lab 1", artifacts, config: { bundle: { entrypoint: "main.py" } } };
  });
  vi.mocked(apiClient.getText).mockResolvedValue("# existing source\n");
  vi.mocked(apiClient.post).mockResolvedValue({});
  vi.mocked(apiClient.postForm).mockImplementation(async (_path, form) => {
    const file = form.get("file") as File;
    const key = String(form.get("artifact_key"));
    artifacts = artifacts.filter((artifact) => artifact.artifact_key !== key);
    artifacts.push({ artifact_key: key, artifact_type: String(form.get("artifact_type")),
      display_filename: file.name, size_bytes: file.size });
    return { data: {}, response: new Response() };
  });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe("model solution authoring", () => {
  it("creates, saves, and reopens a solution without fetching a nonexistent file", async () => {
    await openPage();
    vi.mocked(apiClient.getText).mockClear();
    createFile("main.py");
    const dialog = screen.getByRole("dialog", { name: "Edit main.py" });
    expect(apiClient.getText).not.toHaveBeenCalled();
    expect(apiClient.postForm).not.toHaveBeenCalled();
    fireEvent.change(within(dialog).getByLabelText("Code editor"), { target: { value: "print('Hello')\n" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    const [path, form] = vi.mocked(apiClient.postForm).mock.calls[0];
    expect(path).toBe(artifactsUrl);
    expect(form.get("artifact_type")).toBe("model_solution");
    const file = form.get("file") as File;
    expect(file.name).toBe("main.py");
    expect(await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsText(file);
    })).toBe("print('Hello')\n");
    fireEvent.click(await screen.findByRole("button", { name: "Edit Code" }));
    await waitFor(() => expect(apiClient.getText).toHaveBeenCalledWith(`${artifactsUrl}/${form.get("artifact_key")}`));
    expect((await screen.findByLabelText("Code editor") as HTMLTextAreaElement).value).toBe("# existing source\n");
  }, 15000);

  it("cancels a new file without saving an artifact", async () => {
    await openPage();
    createFile("main.py");
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(apiClient.postForm).not.toHaveBeenCalled();
  });

  it("rejects ZIP uploads before sending them to the server", async () => {
    await openPage();
    const input = document.querySelector('input[type="file"]')!;
    fireEvent.change(input, {
      target: { files: [new File(["archive"], "solution.ZIP", { type: "application/zip" })] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload File" }));
    await screen.findByText(/ZIP.*individual/);
    expect(apiClient.postForm).not.toHaveBeenCalled();
  });

  it("does not overwrite another file with the same basename and a different extension", async () => {
    artifacts = [{ artifact_key: "solution_main", artifact_type: "model_solution", display_filename: "main.py", size_bytes: 10 }];
    await openPage();
    fireEvent.change(screen.getByLabelText("Upload Solution File"), {
      target: { files: [new File(["notes"], "main.txt")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload File" }));
    await waitFor(() => expect(apiClient.postForm).toHaveBeenCalled());
    expect(vi.mocked(apiClient.postForm).mock.calls[0][1].get("artifact_key")).not.toBe("solution_main");
    await screen.findByText("main.txt");
    expect(screen.getByText("main.py")).toBeTruthy();
  });

  it("reuses the key and type when replacing an existing file by filename", async () => {
    artifacts = [{ artifact_key: "seed_support", artifact_type: "support_file", display_filename: "data.txt", size_bytes: 10 }];
    await openPage();
    fireEvent.change(screen.getByLabelText("Upload Solution File"), {
      target: { files: [new File(["updated"], "data.txt")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload File" }));
    await waitFor(() => expect(apiClient.postForm).toHaveBeenCalled());
    const form = vi.mocked(apiClient.postForm).mock.calls[0][1];
    expect(form.get("artifact_key")).toBe("seed_support");
    expect(form.get("artifact_type")).toBe("support_file");
  });

  it("reports a validation polling failure and enables retry instead of staying stuck", async () => {
    await openPage();
    vi.useFakeTimers();
    vi.mocked(apiClient.get).mockRejectedValueOnce(new Error("Connection lost"));
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Test Model Solution" })); });
    await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
    expect(screen.getByText(/Could not check model solution status/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Test Model Solution" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("requires saving setup changes before validating the reference solution", async () => {
    await openPage();
    fireEvent.click(screen.getByRole("button", { name: "Change assignment title" }));
    await screen.findByText("Save assignment changes before testing the model solution.");
    const button = screen.getByRole("button", { name: "Test Model Solution" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  it.each(["", "../main.py", "photo.png", "conftest.py"])("rejects invalid or non-text filenames: %s", async (filename) => {
    await openPage();
    createFile(filename);
    expect(screen.getByRole("alert").textContent).toBeTruthy();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(apiClient.postForm).not.toHaveBeenCalled();
  });

  it("rejects duplicate filenames and avoids overwriting colliding artifact keys", async () => {
    artifacts = [{ artifact_key: "solution_mainpy", artifact_type: "model_solution", display_filename: "other.py", size_bytes: 10 }];
    await openPage();
    createFile("OTHER.py");
    expect(screen.getByRole("alert").textContent).toContain("already exists");
    createFile("main.py");
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(apiClient.postForm).toHaveBeenCalled());
    expect(vi.mocked(apiClient.postForm).mock.calls[0][1].get("artifact_key")).toBe("solution_mainpy_2");
  });

  it("edits C++ support files with the correct language and preserves their type and key", async () => {
    artifacts = [{ artifact_key: "helper", artifact_type: "support_file", display_filename: "helper.CPP", size_bytes: 10 }];
    await openPage();
    fireEvent.click(screen.getByRole("button", { name: "Edit Code" }));
    const editor = await screen.findByLabelText("Code editor");
    expect(editor.getAttribute("data-language")).toBe("cpp");
    fireEvent.change(editor, { target: { value: "int helper() { return 1; }" } });
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(apiClient.postForm).toHaveBeenCalled());
    const form = vi.mocked(apiClient.postForm).mock.calls[0][1];
    expect(form.get("artifact_key")).toBe("helper");
    expect(form.get("artifact_type")).toBe("support_file");
  });

  it("keeps draft content available after a failed save so the teacher can retry", async () => {
    await openPage();
    vi.mocked(apiClient.postForm).mockRejectedValueOnce(new Error("Save failed"));
    createFile("main.cpp");
    fireEvent.change(screen.getByLabelText("Code editor"), { target: { value: "int main() {}" } });
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Save" }));
    await screen.findByText("Save failed");
    expect((screen.getByLabelText("Code editor") as HTMLTextAreaElement).value).toBe("int main() {}");
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(screen.queryByText("Save failed")).toBeNull();
  });

  it("closes the editor when loading fails instead of allowing a blank overwrite", async () => {
    artifacts = [{ artifact_key: "main", artifact_type: "model_solution", display_filename: "main.py", size_bytes: 10 }];
    await openPage();
    vi.mocked(apiClient.getText).mockRejectedValueOnce(new Error("Could not load file"));
    fireEvent.click(screen.getByRole("button", { name: "Edit Code" }));
    await screen.findByText("Could not load file");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(apiClient.postForm).not.toHaveBeenCalled();
  });

  it("renders comparison preview with badges and toggles diff viewer upon successful validation", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path) => {
      if (path.endsWith("/concepts")) return { default_concepts: [], modules: [] };
      if (path.endsWith("/validation-status")) {
        return {
          status: "success",
          errors: [],
          score: 20,
          max_score: 20,
          test_results: [
            {
              key: "part1_files",
              label: "Required files exist",
              points: 10,
              points_awarded: 10,
              passed: true,
              actual: "file1.txt\nfile2.txt",
              expected: "file1.txt\nfile2.txt",
            },
            {
              key: "part2_calc",
              label: "Calculations match",
              points: 10,
              points_awarded: 10,
              passed: true,
              actual: "123.456",
              expected: "123.45",
            },
          ],
        };
      }
      return {
        title: "Lab 1",
        artifacts,
        config: {
          bundle: { entrypoint: "main.py" },
          scoring_items: [
            { key: "part1_files", label: "Required files exist", points: 10, extra_credit: false, item_type: "pytest", comparison_mode: "exact" },
            { key: "part2_calc", label: "Calculations match", points: 10, extra_credit: false, item_type: "pytest", comparison_mode: "numeric_tolerance", tolerance: 0.01 },
          ],
        },
      };
    });

    await openPage();
    vi.useFakeTimers();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Test Model Solution" })); });
    await act(async () => { await vi.advanceTimersByTimeAsync(1500); });

    expect(screen.getByText("Comparison Results Preview")).toBeDefined();
    expect(screen.getByText("Exact")).toBeDefined();
    expect(screen.getByText("Numeric (±0.01)")).toBeDefined();

    const viewDiffButtons = screen.getAllByRole("button", { name: /view diff/i });
    expect(viewDiffButtons.length).toBeGreaterThan(0);
    fireEvent.click(viewDiffButtons[0]);
    expect(screen.getByRole("button", { name: /hide diff/i })).toBeDefined();
    vi.useRealTimers();
  });
});
