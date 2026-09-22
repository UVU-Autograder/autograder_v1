import { describe, expect, it } from "vitest";
import { retentionMessage, reviewAvailable } from "../lib/retention";
import type { RunSummary } from "../types";

const run: RunSummary = {
  id: 1, status: "complete", total_submission_count: 1, success_count: 1,
  warning_count: 0, failure_count: 0, timeout_count: 0,
  created_at: "2026-09-21T00:00:00Z", review_expires_at: "2026-09-21T23:00:00Z",
  retention_state: "available",
};

describe("official retention", () => {
  it("closes review exactly at expiry, including older responses without explicit deadlines", () => {
    const boundary = Date.parse(run.review_expires_at!);
    expect(reviewAvailable(run, boundary - 1)).toBe(true);
    expect(reviewAvailable(run, boundary)).toBe(false);
    expect(reviewAvailable({ ...run, review_expires_at: null }, boundary)).toBe(false);
    expect(retentionMessage(run, boundary)).toContain("Review expired");
  });

  it.each(["cleanup_pending", "cleanup_failed", "deleted"] as const)("never reopens %s data", state => {
    const value = { ...run, retention_state: state };
    expect(reviewAvailable(value, Date.parse(run.created_at))).toBe(false);
    expect(retentionMessage(value)).not.toContain("Export your results");
  });
});
