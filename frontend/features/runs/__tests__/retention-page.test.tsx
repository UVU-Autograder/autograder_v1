import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Page from "@/app/staff/courses/[courseId]/assignments/[assignmentId]/runs/[runId]/page";

const mocks = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), download: vi.fn() }));
vi.mock("react", async original => ({
  ...await original<typeof import("react")>(),
  use: () => ({ courseId: "cs1400", assignmentId: "simple", runId: "1" }),
}));
vi.mock("@/lib/api-client", () => ({ apiClient: mocks }));
vi.mock("@/features/runs/components/grade-histogram", () => ({ GradeHistogram: () => null }));
vi.mock("@/features/runs/components/student-filter-toolbar", () => ({ StudentFilterToolbar: () => null }));
vi.mock("@/features/runs/components/student-review-card", () => ({
  StudentReviewCard: ({ student }: { student: { student_name: string } }) => <div>{student.student_name}</div>,
}));
vi.mock("@/features/runs/components/student-inspect-dialog", () => ({ StudentInspectDialog: () => null }));

describe("review expiry in the run page", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-21T22:59:59Z"));
    mocks.get.mockImplementation(async (path: string) => path.endsWith("/details") ? {
      run_id: 1, status: "complete", exports_ready: true, requires_manual_grading: false,
      completed_students: 1, total_students: 1,
      students: [{ student_name: "Synthetic Student", canvas_id: "123", manual_results: {}, status: "success" }],
    } : {
      id: 1, status: "complete", total_submission_count: 1,
      created_at: "2026-09-21T00:00:00Z", review_expires_at: "2026-09-21T23:00:00Z",
      retention_state: "available",
    });
  });
  afterEach(() => { cleanup(); vi.useRealTimers(); vi.clearAllMocks(); });

  async function show() {
    await act(async () => {
      render(<Page params={Promise.resolve({ courseId: "cs1400", assignmentId: "simple", runId: "1" })} />);
    });
  }

  it("clears private data and disables exports without waiting for another request", async () => {
    await show();
    expect(screen.getByText("Synthetic Student")).toBeTruthy();
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(screen.queryByText("Synthetic Student")).toBeNull();
    expect((screen.getByRole("button", { name: /Export Grades CSV/ }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("status").textContent).toContain("Review expired");
  });

  it("clears cached review data when any review request reports HTTP 410", async () => {
    await show();
    act(() => window.dispatchEvent(new CustomEvent("official-review-expired", {
      detail: "/staff/courses/cs1400/assignments/simple/runs/1/students/123/files",
    })));
    expect(screen.queryByText("Synthetic Student")).toBeNull();
  });

  it("does not offer manual cleanup during grading", async () => {
    mocks.get.mockResolvedValue({ id: 1, status: "run", created_at: "2026-09-21T00:00:00Z", review_expires_at: "2026-09-21T23:00:00Z", students: [] });
    await show();
    const button = screen.getByRole("button", { name: /Delete review data/ }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(mocks.post).not.toHaveBeenCalled();
  });
});
