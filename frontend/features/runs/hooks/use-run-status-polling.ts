import { useState, useEffect, useCallback, useRef } from 'react';
import { reviewAvailable } from '@/features/runs/lib/retention';
import { apiClient } from '@/lib/api-client';
import type { RunStatusResponse } from '@/features/assignments/types';
import {
  getAdaptivePollDelayMs,
  getRunStatus,
  sleep,
} from '@/features/assignments/api';
import {
  staffRunCsvExportPath,
  staffRunFeedbackExportPath,
} from '@/features/staff/api';
import { sortStudentsByName } from '@/features/runs/lib/student-filter';
import type {
  RunSummary,
  RunDetailsResponse,
} from '@/features/runs/types';

export interface UseRunStatusPollingOptions {
  courseId: string;
  assignmentId: string;
  runId: string;
}

export function useRunStatusPolling({
  courseId,
  assignmentId,
  runId,
}: UseRunStatusPollingOptions) {
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [details, setDetailsState] = useState<RunDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewUnavailable, setReviewUnavailable] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);

  const summaryRef = useRef<RunSummary | null>(null);
  const blockedRef = useRef(false);
  const basePath = `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runId}`;

  const clearReview = useCallback(() => {
    blockedRef.current = true;
    setReviewUnavailable(true);
    setDetailsState(null);
  }, []);

  const setDetails = useCallback((value: RunDetailsResponse | null) => {
    if (value && (blockedRef.current || !reviewAvailable(summaryRef.current))) return;
    setDetailsState(value);
  }, []);

  const acceptSummary = useCallback(
    (value: RunSummary) => {
      summaryRef.current = value;
      setSummary(value);
      if (!reviewAvailable(value)) clearReview();
    },
    [clearReview]
  );

  // Initial load
  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        blockedRef.current = false;
        summaryRef.current = null;
        setReviewUnavailable(false);
        setDetailsState(null);
        setIsLoading(true);
        setError(null);
      }
    });

    const loadData = async () => {
      try {
        const summaryData = await apiClient.get<RunSummary>(basePath);
        if (!active) return;
        acceptSummary(summaryData);

        try {
          const detailsData = await apiClient.get<RunDetailsResponse>(
            `${basePath}/details`
          );
          if (!active) return;
          setDetails({
            ...detailsData,
            students: sortStudentsByName(detailsData.students),
          });
        } catch {
          if (!active) return;
          if (summaryData.status === 'queue' || summaryData.status === 'run') {
            setDetails(null);
          }
        }
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof Error ? err.message : 'Failed to load run details.'
        );
      } finally {
        if (!active) return;
        setIsLoading(false);
      }
    };

    void loadData();
    return () => {
      active = false;
    };
  }, [basePath, acceptSummary, setDetails]);

  // Periodic polling & retention checks
  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const value = await apiClient.get<RunSummary>(basePath);
        if (active) acceptSummary(value);
      } catch {
        /* Handled gracefully */
      }
    };

    const timer = setInterval(() => {
      if (summaryRef.current && !reviewAvailable(summaryRef.current)) clearReview();
    }, 1000);

    const poll = setInterval(() => void refresh(), 15000);

    const expired = (event: Event) => {
      const path = (event as CustomEvent<string>).detail;
      if (path.startsWith(`${basePath}/`)) clearReview();
    };
    window.addEventListener('official-review-expired', expired);

    return () => {
      active = false;
      clearInterval(timer);
      clearInterval(poll);
      window.removeEventListener('official-review-expired', expired);
    };
  }, [basePath, acceptSummary, clearReview]);

  // Adaptive run polling when in queue or run
  useEffect(() => {
    const status = summary?.status;
    if (status !== 'queue' && status !== 'run') {
      return;
    }

    let cancelled = false;

    const refreshFinished = async (state: string) => {
      const [summaryData, detailsData] = await Promise.all([
        apiClient.get<RunSummary>(basePath),
        state === 'complete'
          ? apiClient.get<RunDetailsResponse>(`${basePath}/details`)
          : Promise.resolve(null),
      ]);
      if (cancelled) return;
      acceptSummary(summaryData);
      if (detailsData) {
        setDetails({
          ...detailsData,
          students: sortStudentsByName(detailsData.students),
        });
      }
    };

    const pollRun = async () => {
      let attempt = 0;
      while (!cancelled) {
        try {
          const statusData = await getRunStatus(`/runs/${runId}/status`);
          if (cancelled) return;
          setRunStatus(statusData);
          if (
            statusData.state === 'complete' ||
            statusData.state === 'failure'
          ) {
            cancelled = true;
            await refreshFinished(statusData.state);
            return;
          }

          try {
            const detailsData = await apiClient.get<RunDetailsResponse>(
              `${basePath}/details`
            );
            if (!cancelled && detailsData) {
              setDetails({
                ...detailsData,
                students: sortStudentsByName(detailsData.students),
              });
            }
          } catch {
            // Details may not exist briefly at start of a run.
          }
        } catch {
          if (cancelled) return;
        }
        await sleep(getAdaptivePollDelayMs(attempt));
        attempt += 1;
      }
    };

    void pollRun();
    return () => {
      cancelled = true;
    };
  }, [summary?.status, basePath, runId, acceptSummary, setDetails]);

  const handleCleanup = async () => {
    setIsCleaning(true);
    try {
      await apiClient.post(`${basePath}/cleanup`, {});
      clearReview();
      acceptSummary(await apiClient.get<RunSummary>(basePath));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cleanup failed.');
      try {
        acceptSummary(await apiClient.get<RunSummary>(basePath));
      } catch {
        clearReview();
      }
    } finally {
      setIsCleaning(false);
    }
  };

  const handleCsvExport = async () => {
    setError(null);
    try {
      await apiClient.download(
        staffRunCsvExportPath(courseId, assignmentId, runId),
        `run-${runId}-grades.csv`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'CSV export failed.');
    }
  };

  const handleFeedbackExport = async () => {
    setError(null);
    try {
      await apiClient.download(
        staffRunFeedbackExportPath(courseId, assignmentId, runId),
        `run-${runId}-feedback.zip`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Feedback export failed.');
    }
  };

  return {
    summary,
    runStatus,
    details,
    setDetails,
    isLoading,
    error,
    setError,
    reviewUnavailable,
    isCleaning,
    clearReview,
    handleCleanup,
    handleCsvExport,
    handleFeedbackExport,
  };
}
