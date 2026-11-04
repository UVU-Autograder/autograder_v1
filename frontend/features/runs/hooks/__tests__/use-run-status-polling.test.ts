import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useRunStatusPolling } from '../use-run-status-polling';
import type { RunDetailsResponse, RunSummary } from '@/features/runs/types';

const mocks = vi.hoisted(() => ({ get: vi.fn(), status: vi.fn() }));
vi.mock('@/lib/api-client', () => ({ apiClient: { get: mocks.get } }));
vi.mock('@/features/assignments/api', () => ({
  getRunStatus: mocks.status,
  getAdaptivePollDelayMs: () => 1000,
  sleep: (ms: number) => new Promise((resolve) => setTimeout(resolve, ms)),
}));

const basePath = '/staff/courses/cs1400/assignments/lab1/runs/1';
const options = { courseId: 'cs1400', assignmentId: 'lab1', runId: '1' };

function summary(status: string): RunSummary {
  return {
    id: 1, status, total_submission_count: 1, success_count: 1, warning_count: 0,
    failure_count: 0, timeout_count: 0, created_at: '2026-11-04T12:00:00Z',
    review_expires_at: '2026-11-05T11:00:00Z', retention_state: 'available',
  };
}

function details(status: string): RunDetailsResponse {
  return {
    run_id: 1, status, students: [], details_revision: 1,
    requires_manual_grading: false, completed_students: status === 'complete' ? 1 : 0,
    total_students: 1, exports_ready: status === 'complete',
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-11-04T13:00:00Z'));
  mocks.get.mockReset();
  mocks.status.mockReset();
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

async function show() {
  const view = renderHook(() => useRunStatusPolling(options));
  await act(async () => {});
  return view;
}

describe('official run completion polling', () => {
  it('loads final details and export readiness when adaptive polling observes completion', async () => {
    let summaryReads = 0;
    let detailReads = 0;
    mocks.get.mockImplementation(async (path: string) => {
      if (path === basePath) return summary(summaryReads++ === 0 ? 'run' : 'complete');
      if (path === `${basePath}/details`) return details(detailReads++ === 0 ? 'run' : 'complete');
      throw new Error(`Unexpected path: ${path}`);
    });
    mocks.status.mockResolvedValue({ state: 'complete' });
    const { result } = await show();
    expect(result.current.summary?.status).toBe('complete');
    expect(result.current.details?.status).toBe('complete');
    expect(result.current.details?.exports_ready).toBe(true);
  });

  it('loads final details when adaptive polling observes failure', async () => {
    let summaryReads = 0;
    mocks.get.mockImplementation(async (path: string) => {
      if (path === basePath) return summary(summaryReads++ === 0 ? 'run' : 'failure');
      if (path === `${basePath}/details`) return details('failure');
      throw new Error(`Unexpected path: ${path}`);
    });
    mocks.status.mockResolvedValue({ state: 'failure' });
    const { result } = await show();
    expect(result.current.summary?.status).toBe('failure');
    expect(result.current.details?.status).toBe('failure');
  });

  it('advances summary to complete when terminal details are temporarily unavailable', async () => {
    let phase: 'run' | 'complete' = 'run';
    let failTerminalDetails = true;
    mocks.get.mockImplementation(async (path: string) => {
      if (path === basePath) return summary(phase);
      if (path === `${basePath}/details`) {
        if (phase === 'complete' && failTerminalDetails) {
          failTerminalDetails = false;
          throw new Error('Details not ready');
        }
        return details(phase);
      }
      throw new Error(`Unexpected path: ${path}`);
    });
    mocks.status.mockImplementation(async () => {
      phase = 'complete';
      return { state: 'complete' };
    });
    const { result } = await show();
    expect(result.current.summary?.status).toBe('complete');
    expect(result.current.details?.exports_ready).not.toBe(true);
    await act(async () => { await vi.advanceTimersByTimeAsync(15000); });
    expect(result.current.details?.exports_ready).toBe(true);
  });

  it('catches up final details when the periodic summary sees completion first', async () => {
    let finished = false;
    mocks.get.mockImplementation(async (path: string) => path.endsWith('/details')
      ? details(finished ? 'complete' : 'run') : summary(finished ? 'complete' : 'run'));
    mocks.status.mockImplementation(() => new Promise(() => {}));
    const { result } = await show();
    expect(result.current.details?.status).toBe('run');
    finished = true;
    await act(async () => { await vi.advanceTimersByTimeAsync(15000); });
    expect(result.current.summary?.status).toBe('complete');
    expect(result.current.details?.exports_ready).toBe(true);
  });

  it('retries missing terminal details after a transient initial load failure', async () => {
    let detailReads = 0;
    mocks.get.mockImplementation(async (path: string) => {
      if (path.endsWith('/details')) {
        if (detailReads++ === 0) throw new Error('Temporary connection failure');
        return details('complete');
      }
      return summary('complete');
    });
    const { result } = await show();
    expect(result.current.details).toBeNull();
    await act(async () => { await vi.advanceTimersByTimeAsync(15000); });
    expect(result.current.details?.exports_ready).toBe(true);
  });

  it('does not let a delayed initial partial result overwrite the final batch results', async () => {
    let resolveInitialDetails!: (value: RunDetailsResponse) => void;
    let summaryReads = 0;
    let detailReads = 0;
    mocks.get.mockImplementation(async (path: string) => {
      if (path === basePath) return summary(summaryReads++ === 0 ? 'run' : 'complete');
      if (detailReads++ === 0) {
        return new Promise<RunDetailsResponse>((resolve) => { resolveInitialDetails = resolve; });
      }
      return details('complete');
    });
    mocks.status.mockResolvedValue({ state: 'complete' });
    const { result } = await show();
    expect(result.current.details?.exports_ready).toBe(true);
    await act(async () => { resolveInitialDetails(details('run')); });
    expect(result.current.details?.exports_ready).toBe(true);
  });
});
