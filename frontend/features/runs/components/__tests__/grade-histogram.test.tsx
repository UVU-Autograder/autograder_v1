import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import React from "react";
import { GradeHistogram } from "../grade-histogram";
import { StudentRunDetail } from "../../types";

const mockStudents: StudentRunDetail[] = [
  {
    student_name: "Alice Smith",
    canvas_id: "1001",
    bundle_files: ["dessert.py"],
    bundle_file_count: 1,
    score: 95,
    max_score: 100,
    status: "success",
    feedback_preview: "All passed",
    feedback_html: "<p>Passed</p>",
    manual_results: {},
    overall_comment: "",
    automated_results: [],
    automated_score: 95,
    automated_max_score: 100,
  },
];

describe("GradeHistogram Component", () => {
  it("renders empty state message when no students provided", () => {
    render(<GradeHistogram students={[]} />);
    expect(screen.getByText(/Grade Distribution/i)).toBeDefined();
    expect(
      screen.getByText(/Score distribution appears as student results load/i),
    ).toBeDefined();
  });

  it("renders histogram with role='img' and aria-label when students provided", () => {
    render(<GradeHistogram students={mockStudents} />);
    const histogramImg = screen.getByRole("img", {
      name: /Histogram of student scores by percent of max points/i,
    });
    expect(histogramImg).toBeDefined();
    expect(screen.getByText("90+")).toBeDefined();
  });
});
