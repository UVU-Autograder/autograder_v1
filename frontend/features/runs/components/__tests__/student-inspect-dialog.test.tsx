import { act, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { StudentInspectDialog, type StudentInspectDialogProps } from "../student-inspect-dialog";
import { StudentRunDetail, type StudentFile } from "../../types";
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

function dialogProps(student = mockStudent): StudentInspectDialogProps {
  return {
    isOpen: true,
    onOpenChange: vi.fn(),
    student,
    courseId: "1",
    assignmentId: "2",
    runId: "3",
    onSaveManualGrades: vi.fn().mockResolvedValue(undefined),
    isSavingGrades: false,
  };
}

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

  it("starts a fresh grading draft when switching students", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ files: [] });
    const props = dialogProps(mockUngradedStudent);
    const { rerender } = render(<StudentInspectDialog {...props} />);
    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "5" } });
    fireEvent.change(screen.getByPlaceholderText("Feedback for this item..."), {
      target: { value: "Unsaved first-student feedback" },
    });

    rerender(
      <StudentInspectDialog
        {...props}
        student={{ ...mockUngradedStudent, canvas_id: "67890", overall_comment: "Second student" }}
      />,
    );
    expect((screen.getByRole("spinbutton") as HTMLInputElement).value).toBe("");
    fireEvent.click(screen.getByRole("button", { name: /^Save$/ }));
    expect(props.onSaveManualGrades).toHaveBeenCalledWith(
      "67890",
      { rubric1: { score: null, comments: "" } },
      "Second student",
      false,
    );
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(2));
  });

  it("preserves unsaved feedback through a same-student polling update", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ files: [] });
    const props = dialogProps();
    const { rerender } = render(<StudentInspectDialog {...props} />);
    const input = screen.getByLabelText("Overall student feedback");
    fireEvent.change(input, { target: { value: "Unsaved feedback" } });
    rerender(<StudentInspectDialog {...props} student={{ ...mockStudent, score: 90 }} />);

    expect((screen.getByLabelText("Overall student feedback") as HTMLTextAreaElement).value)
      .toBe("Unsaved feedback");
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(1));
  });

  it("resets feedback and file state when reopened or moved to another run", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ files: [] });
    const props = dialogProps();
    const { rerender } = render(<StudentInspectDialog {...props} />);
    fireEvent.change(screen.getByLabelText("Overall student feedback"), {
      target: { value: "Discarded feedback" },
    });
    rerender(<StudentInspectDialog {...props} isOpen={false} />);
    expect(screen.queryByLabelText("Overall student feedback")).toBeNull();
    rerender(<StudentInspectDialog {...props} />);
    expect((screen.getByLabelText("Overall student feedback") as HTMLTextAreaElement).value)
      .toBe("Good submission");

    fireEvent.change(screen.getByLabelText("Overall student feedback"), {
      target: { value: "Feedback for the previous run" },
    });
    rerender(<StudentInspectDialog {...props} runId="4" />);
    expect((screen.getByLabelText("Overall student feedback") as HTMLTextAreaElement).value)
      .toBe("Good submission");
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(3));
  });

  it("ignores a previous student's late file response", async () => {
    let resolvePrevious!: (value: { files: StudentFile[] }) => void;
    vi.mocked(apiClient.get)
      .mockReturnValueOnce(new Promise((resolve) => { resolvePrevious = resolve; }))
      .mockResolvedValueOnce({
        files: [{ filepath: "current.py", size_bytes: 10, previewable: false }],
      });
    const props = dialogProps();
    const { rerender } = render(<StudentInspectDialog {...props} />);
    rerender(<StudentInspectDialog {...props} student={{ ...mockStudent, canvas_id: "67890" }} />);
    fireEvent.mouseDown(screen.getByRole("tab", { name: "Code Explorer" }), {
      button: 0,
      ctrlKey: false,
    });
    await screen.findByText("current.py");

    await act(async () => {
      resolvePrevious({ files: [{ filepath: "previous.py", size_bytes: 10, previewable: true }] });
    });
    expect(screen.queryByText("previous.py")).toBeNull();
    expect(screen.getByText("current.py")).toBeDefined();
    expect(apiClient.get).toHaveBeenCalledTimes(2);
  });
});
