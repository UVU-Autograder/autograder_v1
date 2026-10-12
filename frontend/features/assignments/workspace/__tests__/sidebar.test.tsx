import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssignmentSidebar } from "../sidebar";
import { AssignmentFileProvider, useAssignmentFile } from "../assignment-file-context";
import { ViewProvider } from "@/lib/view-context";
import type { Assignment } from "@/features/assignments/types";

const mockAssignment: Assignment = {
  id: "1",
  course_id: "1",
  title: "Test Assignment",
  sandbox_enabled: true,
  language: "python",
  max_score: 100,
  upload_quota: {
    limit: 10,
    window_seconds: 3600,
    remaining: 10,
    reset_at: "2026-10-06T00:00:00Z",
  },
  description: "Test assignment description",
  accepted_bundle_types: ["zip"],
  max_upload_bytes: 1024 * 1024,
  constraints: [],
  rubric: [],
  rubric_groups: [],
  completion_requirements: [],
  config: {
    bundle: {
      entrypoint: "main.py",
      file_requirements: [],
    },
    scoring_items: [],
  },
};

function TestWrapper({
  initialFiles = ["main.py", "utils.py"],
  assignment = mockAssignment,
}: {
  initialFiles?: string[];
  assignment?: Assignment;
}) {
  return (
    <ViewProvider mode="sandbox">
      <AssignmentFileProvider assignment={assignment}>
        <TestInner initialFiles={initialFiles} assignment={assignment} />
      </AssignmentFileProvider>
    </ViewProvider>
  );
}

function TestInner({
  initialFiles,
  assignment,
}: {
  initialFiles: string[];
  assignment?: Assignment;
}) {
  const { openFileByName } = useAssignmentFile();
  const [initialized, setInitialized] = React.useState(false);

  React.useEffect(() => {
    if (!initialized) {
      initialFiles.forEach((file) => {
        void openFileByName(file, { content: "pass", category: "workspace" });
      });
      setInitialized(true);
    }
  }, [initialized, initialFiles, openFileByName]);

  if (!initialized) return <div>Loading...</div>;

  return <AssignmentSidebar courseId="1" assignment={assignment} />;
}

describe("AssignmentSidebar - Renaming & Bundle Indicators", () => {
  it("renders workspace files and identifies the entrypoint badge", async () => {
    render(<TestWrapper initialFiles={["main.py", "utils.py"]} />);

    expect(await screen.findByText("main.py")).toBeDefined();
    expect(screen.getByText("utils.py")).toBeDefined();
    expect(screen.getByText("entrypoint")).toBeDefined();
  });

  it("does not render missing entrypoint warning in sidebar when entrypoint is absent", async () => {
    render(<TestWrapper initialFiles={["helper.py"]} />);

    expect(await screen.findByText("helper.py")).toBeDefined();
    expect(screen.queryByText(/Missing entrypoint/)).toBeNull();
  });

  it("allows renaming a file via inline form", async () => {
    render(<TestWrapper initialFiles={["main.py", "utils.py"]} />);

    await screen.findByText("utils.py");

    const renameButtons = screen.getAllByTitle(/Rename/);
    const utilsRenameBtn = renameButtons.find((btn) =>
      btn.getAttribute("title")?.includes("utils.py")
    );
    expect(utilsRenameBtn).toBeDefined();

    fireEvent.click(utilsRenameBtn!);

    const input = screen.getByDisplayValue("utils.py");
    expect(input).toBeDefined();

    fireEvent.change(input, { target: { value: "helpers.py" } });

    const saveBtn = screen.getByTitle("Save rename");
    fireEvent.click(saveBtn);

    expect(await screen.findByText("helpers.py")).toBeDefined();
    expect(screen.queryByText("utils.py")).toBeNull();
  });

  it("displays inline error and blocks save on duplicate filename", async () => {
    render(<TestWrapper initialFiles={["main.py", "utils.py"]} />);

    await screen.findByText("utils.py");

    const renameButtons = screen.getAllByTitle(/Rename/);
    const utilsRenameBtn = renameButtons.find((btn) =>
      btn.getAttribute("title")?.includes("utils.py")
    );

    fireEvent.click(utilsRenameBtn!);

    const input = screen.getByDisplayValue("utils.py");
    fireEvent.change(input, { target: { value: "main.py" } });

    expect(await screen.findByText(/already exists/)).toBeDefined();

    const saveBtn = screen.getByTitle("Save rename") as HTMLButtonElement;
    expect(saveBtn.disabled).toBe(true);
  });

  it("cancels renaming on Escape key", async () => {
    render(<TestWrapper initialFiles={["main.py", "utils.py"]} />);

    await screen.findByText("utils.py");

    const renameButtons = screen.getAllByTitle(/Rename/);
    const utilsRenameBtn = renameButtons.find((btn) =>
      btn.getAttribute("title")?.includes("utils.py")
    );

    fireEvent.click(utilsRenameBtn!);

    const input = screen.getByDisplayValue("utils.py");
    fireEvent.change(input, { target: { value: "cancelled.py" } });
    fireEvent.keyDown(input, { key: "Escape" });

    expect(screen.queryByDisplayValue("cancelled.py")).toBeNull();
    expect(screen.getByText("utils.py")).toBeDefined();
  });
});
