import { ApiError } from "@/lib/api-client";
import type { RunStatusResponse } from "@/features/assignments/types";

/** Keep retrying a full grading queue for at most this long before asking the student. */
export const MAX_ADMISSION_WAIT_MS = 5 * 60_000;
/** Keep polling a queued/running run for at most this long, then offer "Check again". */
export const MAX_POLL_DURATION_MS = 10 * 60_000;
/** Give up on polling after this many consecutive transient errors. */
export const MAX_CONSECUTIVE_POLL_ERRORS = 8;
/** Automatic AI feedback retries when the tutor is busy or slow. */
export const MAX_AI_ATTEMPTS = 4;

/**
 * Exponential backoff with +/-20% jitter, so a crowd of waiting students does not
 * retry in lockstep. The server's hint (retry_after_seconds) wins when present.
 */
export function backoffDelayMs(attempt: number, retryAfterSeconds?: number, random: () => number = Math.random): number {
    const exponential = Math.min(30_000, 2_000 * 2 ** Math.max(0, attempt));
    const target = retryAfterSeconds && retryAfterSeconds > 0 ? retryAfterSeconds * 1000 : exponential;
    const capped = Math.min(Math.max(target, 1_000), 60_000);
    return Math.round(capped * (0.8 + 0.4 * random()));
}

/** Upload rejected before it was counted against the run limit, so retrying is free. */
export function isRetryableAdmissionError(err: unknown): err is ApiError {
    if (!(err instanceof ApiError) || err.status !== 503) return false;
    // Older backends send a plain string detail for a full queue (no code).
    return err.code === undefined || err.code === "queue_full" || err.code === "busy";
}

/** Poll errors worth riding out: network blips, client timeouts, 5xx, and "not ready" 409s. */
export function isTransientPollError(err: unknown): boolean {
    if (!(err instanceof ApiError)) return true;
    return err.status === 0 || err.status === 409 || err.status === 429 || err.status >= 500;
}

const AI_RETRY_CODES = new Set(["ai_busy", "ai_timeout", "ai_error", "client_timeout", "grading_not_complete"]);

/** What to do after an AI feedback attempt failed. */
export function aiFailureAction(err: unknown): "retry" | "fallback" | "stop" {
    if (err instanceof ApiError) {
        if (err.code === "network_error") return "fallback";
        if (err.code && AI_RETRY_CODES.has(err.code)) return "retry";
        // Older backends: no code, but a 5xx is still worth a retry.
        if (!err.code && err.status >= 500) return "retry";
        return "stop";
    }
    return "fallback";
}

// Older backends return model outages as 200 responses with these warning texts.
const LEGACY_AI_FAILURE =
    /^\s*⚠️\s*(Local AI assistant request timed out|Local AI assistant is currently unreachable|An error occurred while generating AI feedback)/;

export function isLegacyAiFailureText(text: string): boolean {
    return LEGACY_AI_FAILURE.test(text);
}

// Infrastructure failures (the grader's fault, not the student's code).
const GRADER_FAULT_CATEGORIES = new Set([
    "cleanup_failure",
    "cleanup_service_unavailable",
    "execution_interrupted",
    "heartbeat_unavailable",
    "infrastructure_error",
    "internal_error",
    "judge0_error",
    "preparation_error",
    "workspace_deletion_failed",
]);

export const GRADER_FAULT_MESSAGE =
    "The grader had a problem with this run, not with your code. Please run it again.";

export function isGraderFault(category: string | null | undefined, flag?: boolean): boolean {
    return Boolean(flag) || (!!category && GRADER_FAULT_CATEGORIES.has(category));
}

/** Polling stopped while the run was still queued or running; the run itself continues. */
export class RunStillPendingError extends Error {
    lastStatus: RunStatusResponse | null;

    constructor(lastStatus: RunStatusResponse | null) {
        super("Your run is taking longer than usual. It is still in line; check again in a moment.");
        this.name = "RunStillPendingError";
        this.lastStatus = lastStatus;
    }
}

/** The backend no longer knows this run (for example after a restart). */
export class RunLostError extends Error {
    constructor() {
        super("This run is no longer available on the grader. Please run your code again.");
        this.name = "RunLostError";
    }
}

/** A wait the student can cut short ("Try now") or cancel. */
export class WaitControl {
    private skipFn: (() => void) | null = null;
    cancelled = false;

    wait(ms: number): Promise<void> {
        // Cancelled before this wait started (e.g. between two retries): don't wait at all.
        if (this.cancelled) return Promise.resolve();
        return new Promise((resolve) => {
            const timer = setTimeout(() => {
                this.skipFn = null;
                resolve();
            }, ms);
            this.skipFn = () => {
                clearTimeout(timer);
                this.skipFn = null;
                resolve();
            };
        });
    }

    skip(): void {
        this.skipFn?.();
    }

    cancel(): void {
        this.cancelled = true;
        this.skip();
    }
}

export class RetryCancelledError extends Error {
    constructor() {
        super("Cancelled.");
        this.name = "RetryCancelledError";
    }
}
