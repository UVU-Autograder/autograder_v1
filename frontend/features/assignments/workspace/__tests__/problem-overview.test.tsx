import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProblemOverview } from "../problem-overview";
import type { Assignment } from "@/features/assignments/types";

const baseAssignment: Assignment = {
  id: "test-assignment-1",
  course_id: "cs1410",
  title: "Lab 1: Image Processing",
  sandbox_enabled: true,
  language: "python",
  max_score: 100,
  upload_quota: {
    limit: 10,
    window_seconds: 3600,
    remaining: 10,
    reset_at: "2026-10-06T00:00:00Z",
  },
  description: "## Overview\n\nWrite a program to process images with `filter` functions.",
  accepted_bundle_types: ["zip"],
  max_upload_bytes: 1024 * 1024,
  constraints: [
    { label: "File Format", value: "ZIP archive" },
  ],
  allowed_concepts: ["functions", "loops"],
  rubric: [],
  rubric_groups: [],
};

describe("ProblemOverview", () => {
  it("renders the title, max score, and constraints", () => {
    render(<ProblemOverview assignment={baseAssignment} />);

    expect(screen.getByText("Lab 1: Image Processing")).toBeDefined();
    expect(screen.getByText("100 pts")).toBeDefined();
    expect(screen.getByText("Submission Rules")).toBeDefined();
    expect(screen.getByText("File Format:")).toBeDefined();
  });

  it("renders assignment description with markdown formatting when present", () => {
    render(<ProblemOverview assignment={baseAssignment} />);

    const descCard = screen.getByTestId("assignment-description-card");
    expect(descCard).toBeDefined();
    expect(screen.getByText("Overview")).toBeDefined();
    expect(screen.getByText(/Write a program to process images/)).toBeDefined();
  });

  it("renders pipe tables in the description, but not ones inside fenced code", () => {
    const tableAssignment: Assignment = {
      ...baseAssignment,
      description: [
        "| Criteria | Points |",
        "| --- | :---: |",
        "| Correct output | 50 |",
        "",
        "```text",
        "| not | a table |",
        "```",
      ].join("\n"),
    };
    render(<ProblemOverview assignment={tableAssignment} />);

    expect(screen.getAllByRole("table")).toHaveLength(1);
    expect(screen.getByRole("columnheader", { name: "Criteria" })).toBeDefined();
    expect(screen.getByRole("cell", { name: "Correct output" })).toBeDefined();
    expect(screen.getByRole("cell", { name: "50" }).style.textAlign).toBe("center");
    expect(screen.getByText("| not | a table |")).toBeDefined();
  });

  it("does not render description card when description is empty", () => {
    const noDescAssignment: Assignment = {
      ...baseAssignment,
      description: "",
    };
    render(<ProblemOverview assignment={noDescAssignment} />);

    expect(screen.queryByTestId("assignment-description-card")).toBeNull();
  });
});
