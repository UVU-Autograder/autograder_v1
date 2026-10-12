import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StudentInspectDialog } from "../student-inspect-dialog";
import type { StudentRunDetail } from "../../types";

const mocks = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock("@/lib/api-client", () => ({ apiClient: mocks }));
vi.mock("@/components/monaco-editor", () => ({
  default: () => <div data-testid="monaco-mock" />,
}));

const studentA: StudentRunDetail = {
  student_name: "Alice Student",
  canvas_id: "101",
  bundle_files: ["main.py"],
  bundle_file_count: 1,
  score: 10,
  max_score: 20,
  automated_score: 10,
  automated_max_score: 10,
  status: "warning",
  feedback_preview: "Good start",
  feedback_html: "<p>Good start</p>",
  overall_comment: "",
  automated_results: [
    {
      key: "ag_add",
      label: "Addition",
      outcome: "passed",
      points: 10,
      points_awarded: 10,
      passed: true,
    },
  ],
  manual_results: {
    code_style: {
      label: "Code Style & Comments",
      points: 10,
      score: null,
      comments: "",
    },
  },
};

const studentB: StudentRunDetail = {
  ...studentA,
  student_name: "Bob Student",
  canvas_id: "102",
};

describe("StudentInspectDialog batch review ergonomics (#55)", () => {
  beforeEach(() => {
    mocks.get.mockResolvedValue({ files: [] });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("supports quick-score preset pills, Mark All Full Points, and Prev/Next student navigation", async () => {
    const onSaveManualGrades = vi.fn().mockResolvedValue(undefined);
    const onSelectStudent = vi.fn();

    render(
      <StudentInspectDialog
        isOpen={true}
        onOpenChange={vi.fn()}
        student={studentA}
        students={[studentA, studentB]}
        onSelectStudent={onSelectStudent}
        courseId="cs1400"
        assignmentId="hw1"
        runId="1"
        onSaveManualGrades={onSaveManualGrades}
        isSavingGrades={false}
      />,
    );

    expect(screen.getByText("1 / 2")).toBeTruthy();

    // Click 50% (5) preset pill
    fireEvent.click(screen.getByRole("button", { name: "50% (5)" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSaveManualGrades).toHaveBeenCalledWith(
      "101",
      { code_style: { score: 5, comments: "" } },
      "",
      false,
    );

    // Click Mark All Full Points
    fireEvent.click(
      screen.getByRole("button", { name: /Mark All Full Points/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onSaveManualGrades).toHaveBeenLastCalledWith(
      "101",
      { code_style: { score: 10, comments: "" } },
      "",
      false,
    );

    // Confirm navigation when clean or confirmed
    vi.spyOn(window, "confirm").mockReturnValue(true);
    fireEvent.click(screen.getByRole("button", { name: /^Next$/i }));
    expect(onSelectStudent).toHaveBeenCalledWith(studentB);
  });
});
