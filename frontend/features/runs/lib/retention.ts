import type { RunSummary } from "../types";

export function reviewAvailable(run: RunSummary | null, now = Date.now()): boolean {
  if (!run) return false;
  const expires = run.review_expires_at
    ? Date.parse(run.review_expires_at)
    : Date.parse(run.created_at) + 23 * 60 * 60 * 1000;
  return (!run.retention_state || run.retention_state === "available") && now < expires;
}

export function retentionMessage(run: RunSummary | null, now = Date.now()): string {
  if (!run) return "Checking review availability…";
  if (run.retention_state === "cleanup_failed") return "Cleanup failed. Review is unavailable; automatic cleanup will retry.";
  if (run.retention_state === "deleted") return "Review data has been deleted.";
  if (run.retention_state === "cleanup_pending") return "Cleanup pending. Review is unavailable.";
  if (!reviewAvailable(run, now)) return "Review expired. Automatic cleanup is pending.";
  const expires = run.review_expires_at ?? new Date(Date.parse(run.created_at) + 23 * 60 * 60 * 1000).toISOString();
  return `Review and downloads end ${new Date(expires).toLocaleString()}. Export your results before then.`;
}
