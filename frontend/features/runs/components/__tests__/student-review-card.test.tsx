import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { StudentReviewCard } from "../student-review-card";
import { StudentRunDetail } from "../../types";

const studentWithUngraded: StudentRunDetail = {
  student_name: "Jane Doe",
  canvas_id: "54321",
  bundle_files: ["dessert.py"],
  bundle_file_count: 1,
  score: 80,
  max_score: 100,
  status: "success",
  feedback_preview: "Good job on dessert class",
  feedback_html: "<p>Good job</p>",
  manual_results: {
    rubric1: { label: "Formatting", points: 10, score: null, comments: "" },
  },
  overall_comment: "",
  automated_results: [],
  automated_score: 80,
  automated_max_score: 90,
};

describe("StudentReviewCard Component", () => {
  it("renders student information, score, and ungraded badge", () => {
    render(
      <StudentReviewCard
        student={studentWithUngraded}
        onInspect={vi.fn()}
      />,
    );

    expect(screen.getByText("Jane Doe")).toBeDefined();
    expect(screen.getByText(/Canvas ID: 54321/i)).toBeDefined();
    expect(screen.getByText("80 / 100 pts")).toBeDefined();
    expect(screen.getByText("Ungraded (1)")).toBeDefined();
    expect(screen.getByText("Good job on dessert class")).toBeDefined();
  });

  it("calls onInspect when the inspect button is clicked", () => {
    const handleInspect = vi.fn();
    render(
      <StudentReviewCard
        student={studentWithUngraded}
        onInspect={handleInspect}
      />,
    );

    const inspectBtn = screen.getByTestId("inspect-54321");
    fireEvent.click(inspectBtn);
    expect(handleInspect).toHaveBeenCalledTimes(1);
    expect(handleInspect).toHaveBeenCalledWith(studentWithUngraded);
  });
});
