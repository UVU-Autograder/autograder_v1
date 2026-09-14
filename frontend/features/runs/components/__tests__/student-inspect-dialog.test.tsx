import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { StudentInspectDialog } from "../student-inspect-dialog";
import { StudentRunDetail } from "../../types";
import { apiClient } from "@/lib/api-client";

vi.mock("@/components/monaco-editor", () => ({
  default: () => <div data-testid="mock-monaco-editor">Monaco Editor Mock</div>,
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockStudent: StudentRunDetail = {
  student_name: "Alice Smith",
  canvas_id: "12345",
  bundle_files: ["main.py"],
  bundle_file_count: 1,
  score: 85,
  max_score: 100,
  status: "success",
  feedback_preview: "Great job overall",
  feedback_html: "<div>Feedback details HTML</div>",
  manual_results: {
    rubric1: { label: "Design Pattern", points: 15, score: 12, comments: "Clean design" },
  },
  overall_comment: "Good submission",
  automated_results: [
    {
      key: "test1",
      label: "Unit Tests",
      outcome: "passed",
      passed: true,
      points_awarded: 73,
      points: 85,
    },
  ],
  automated_score: 73,
  automated_max_score: 85,
};

const mockUngradedStudent: StudentRunDetail = {
  ...mockStudent,
  manual_results: {
    rubric1: { label: "Design Pattern", points: 15, score: null, comments: "" },
  },
};

describe("StudentInspectDialog Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.get).mockResolvedValue({
      files: [
        { filepath: "main.py", size_bytes: 120, previewable: true, preview_kind: "text" },
      ],
    });
  });

  it("renders student name, canvas id, and tabs when open", async () => {
    render(
      <StudentInspectDialog
        isOpen={true}
        onOpenChange={vi.fn()}
        student={mockStudent}
        courseId="1"
        assignmentId="2"
        runId="3"
        onSaveManualGrades={vi.fn()}
        isSavingGrades={false}
      />,
    );

    expect(screen.getByText("Alice Smith")).toBeDefined();
    expect(screen.getByText(/Canvas ID: 12345/i)).toBeDefined();
    expect(screen.getByText("Feedback Preview")).toBeDefined();
    expect(screen.getByText("Code Explorer")).toBeDefined();
    expect(screen.getByText("Manual Grading")).toBeDefined();
  });

  it("opens manual tab for ungraded student and calls onSaveManualGrades on save", async () => {
    const handleSave = vi.fn().mockResolvedValue(undefined);
    render(
      <StudentInspectDialog
        isOpen={true}
        onOpenChange={vi.fn()}
        student={mockUngradedStudent}
        courseId="1"
        assignmentId="2"
        runId="3"
        onSaveManualGrades={handleSave}
        isSavingGrades={false}
      />,
    );

    expect(screen.getByText("Design Pattern")).toBeDefined();
    const saveBtn = screen.getByRole("button", { name: /^Save$/ });
    fireEvent.click(saveBtn);

    expect(handleSave).toHaveBeenCalledWith(
      "12345",
      expect.objectContaining({
        rubric1: expect.objectContaining({ score: null, comments: "" }),
      }),
      "Good submission",
      false,
    );
  });
});

