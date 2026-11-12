import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { StudentInspectDialog } from "../student-inspect-dialog";
import type { StudentRunDetail } from "../../types";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({ files: [] }),
    post: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/components/monaco-editor", () => ({
  default: () => <div data-testid="monaco-editor" />,
}));

describe("StudentInspectDialog Component - Comment Snippets", () => {
  const studentWithTemplates: StudentRunDetail = {
    student_name: "Alice Smith",
    canvas_id: "1001",
    bundle_files: ["main.py"],
    bundle_file_count: 1,
    score: 80,
    max_score: 100,
    status: "warning",
    feedback_preview: "Manual grading needed",
    feedback_html: "<p>Feedback</p>",
    manual_results: {
      code_style: {
        label: "Code Style & Naming",
        points: 10,
        score: null,
        comments: "",
        comment_templates: [
          "Missing docstrings on helper functions",
          "Variable names should follow PEP 8 snake_case",
        ],
      },
    },
    overall_comment: "",
    automated_results: [],
    automated_score: 80,
    automated_max_score: 90,
  };

  it("renders 1-click comment snippets for manual rubric items", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);

    await act(async () => {
      render(
        <StudentInspectDialog
          isOpen={true}
          onOpenChange={vi.fn()}
          student={studentWithTemplates}
          courseId="cs1400"
          assignmentId="lab1"
          runId="42"
          onSaveManualGrades={onSave}
          isSavingGrades={false}
        />
      );
    });

    expect(screen.getByText("Quick comments:")).toBeDefined();
    expect(
      screen.getByRole("button", {
        name: /\+ Missing docstrings on helper functions/i,
      })
    ).toBeDefined();
    expect(
      screen.getByRole("button", {
        name: /\+ Variable names should follow PEP 8 snake_case/i,
      })
    ).toBeDefined();
  });

  it("inserts and appends comment snippets cleanly into the textarea on click", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);

    await act(async () => {
      render(
        <StudentInspectDialog
          isOpen={true}
          onOpenChange={vi.fn()}
          student={studentWithTemplates}
          courseId="cs1400"
          assignmentId="lab1"
          runId="42"
          onSaveManualGrades={onSave}
          isSavingGrades={false}
        />
      );
    });

    const textarea = screen.getByPlaceholderText(
      /feedback for this item\.\.\./i
    ) as HTMLTextAreaElement;
    expect(textarea.value).toBe("");

    // Click first snippet
    const snippet1 = screen.getByRole("button", {
      name: /\+ Missing docstrings on helper functions/i,
    });
    await act(async () => {
      fireEvent.click(snippet1);
    });
    expect(textarea.value).toBe("Missing docstrings on helper functions");

    // Click second snippet: should append with newline
    const snippet2 = screen.getByRole("button", {
      name: /\+ Variable names should follow PEP 8 snake_case/i,
    });
    await act(async () => {
      fireEvent.click(snippet2);
    });
    expect(textarea.value).toBe(
      "Missing docstrings on helper functions\nVariable names should follow PEP 8 snake_case"
    );

    // Save button should be enabled and submit the comments
    const saveBtn = screen.getByRole("button", { name: /^save$/i });
    await act(async () => {
      fireEvent.click(saveBtn);
    });

    expect(onSave).toHaveBeenCalledWith(
      "1001",
      expect.objectContaining({
        code_style: {
          score: null,
          comments:
            "Missing docstrings on helper functions\nVariable names should follow PEP 8 snake_case",
        },
      }),
      "",
      false
    );
  });
});
