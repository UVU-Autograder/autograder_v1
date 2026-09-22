import { describe, it, expect } from "vitest";
import {
  filterStudents,
  sortStudentsByName,
  formatBundleSummary,
  hasUngradedManualItems,
  buildScoreHistogram,
} from "../lib/student-filter";
import { StudentRunDetail } from "../types";

const mockStudents: StudentRunDetail[] = [
  {
    student_name: "Alice Smith",
    canvas_id: "1001",
    bundle_files: ["dessert.py"],
    bundle_file_count: 1,
    score: 95,
    max_score: 100,
    status: "success",
    feedback_preview: "All tests passed",
    feedback_html: "<p>All tests passed</p>",
    manual_results: {},
    overall_comment: "",
    automated_results: [],
    automated_score: 95,
    automated_max_score: 100,
  },
  {
    student_name: "Bob Jones",
    canvas_id: "1002",
    bundle_files: ["dessert.py", "candy.py"],
    bundle_file_count: 2,
    score: 40,
    max_score: 100,
    status: "failure",
    feedback_preview: "Failed 2 tests",
    feedback_html: "<p>Failed 2 tests</p>",
    manual_results: {
      style: { label: "Code Style", points: 10, score: null, comments: "" },
    },
    overall_comment: "",
    automated_results: [],
    automated_score: 40,
    automated_max_score: 90,
  },
  {
    student_name: "Charlie Brown",
    canvas_id: "1003",
    bundle_files: ["dessert.py"],
    bundle_file_count: 1,
    score: 85,
    max_score: 100,
    status: "success",
    feedback_preview: "Passed all automated tests",
    feedback_html: "<p>Passed</p>",
    manual_results: {
      style: { label: "Code Style", points: 10, score: 9, comments: "Clean code" },
    },
    overall_comment: "Nice job",
    automated_results: [],
    automated_score: 76,
    automated_max_score: 90,
  },
];

describe("Student filtering and sorting", () => {
  it("sorts students alphabetically by name", () => {
    const unsorted = [mockStudents[1], mockStudents[2], mockStudents[0]];
    const sorted = sortStudentsByName(unsorted);
    expect(sorted.map((s) => s.student_name)).toEqual([
      "Alice Smith",
      "Bob Jones",
      "Charlie Brown",
    ]);
  });

  it("formats bundle summary correctly", () => {
    expect(formatBundleSummary(mockStudents[0])).toBe("1 file");
    expect(formatBundleSummary(mockStudents[1])).toBe("2 files");
    expect(
      formatBundleSummary({
        ...mockStudents[0],
        bundle_files: [],
        bundle_file_count: 0,
      }),
    ).toBe("No submission files prepared");
  });

  it("correctly identifies ungraded manual items", () => {
    expect(hasUngradedManualItems(mockStudents[0])).toBe(false);
    expect(hasUngradedManualItems(mockStudents[1])).toBe(true);
    expect(hasUngradedManualItems(mockStudents[2])).toBe(false);
  });

  it("filters students by search query (name or ID)", () => {
    expect(filterStudents(mockStudents, "alice", "all")).toHaveLength(1);
    expect(filterStudents(mockStudents, "alice", "all")[0].student_name).toBe(
      "Alice Smith",
    );

    expect(filterStudents(mockStudents, "1002", "all")).toHaveLength(1);
    expect(filterStudents(mockStudents, "1002", "all")[0].student_name).toBe(
      "Bob Jones",
    );

    expect(filterStudents(mockStudents, "nonexistent", "all")).toHaveLength(0);
  });

  it("filters students by status: ungraded", () => {
    const ungraded = filterStudents(mockStudents, "", "ungraded");
    expect(ungraded).toHaveLength(1);
    expect(ungraded[0].student_name).toBe("Bob Jones");
  });

  it("filters students by status: graded", () => {
    const graded = filterStudents(mockStudents, "", "graded");
    expect(graded).toHaveLength(2);
    expect(graded.map((s) => s.student_name)).toEqual([
      "Alice Smith",
      "Charlie Brown",
    ]);
  });

  it("filters students by status: failed", () => {
    const failed = filterStudents(mockStudents, "", "failed");
    expect(failed).toHaveLength(1);
    expect(failed[0].student_name).toBe("Bob Jones");
  });

  it("combines search query and status filter", () => {
    // Bob Jones is failed and matches 'bob'
    expect(filterStudents(mockStudents, "bob", "failed")).toHaveLength(1);
    // Alice is not failed
    expect(filterStudents(mockStudents, "alice", "failed")).toHaveLength(0);
  });
});

describe("Score histogram builder", () => {
  it("builds 10 score buckets from 0 to 100 percent", () => {
    const buckets = buildScoreHistogram(mockStudents);
    expect(buckets).toHaveLength(10);
    // Alice: 95% -> bucket 9 (90+)
    // Bob: 40% -> bucket 4 (40-49%)
    // Charlie: 85% -> bucket 8 (80-89%)
    expect(buckets[9].count).toBe(1);
    expect(buckets[4].count).toBe(1);
    expect(buckets[8].count).toBe(1);
    expect(buckets[0].count).toBe(0);
  });
});
