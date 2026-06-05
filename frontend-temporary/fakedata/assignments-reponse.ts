export type AssignmentsDataType = {
    id: string;
    method: string;
    path: string;
    label: string;
    note: string;
    response: AssignmentsResponseType;
}

export type AssignmentsResponseType = {
    ok: boolean;
    data: {
        job_id: string;
        status: string;
        display_name: string;
        rate_limit: {
            uploads_used: number;
            uploads_limit: number;
            window_resets_at: string;
        }
        projected_result: ProjectedResult;
        zero_retention_notice: string;
    }
}

type ProjectedResult = {
    judge0_status: { id: number; description: string };
    execution_time_s: number;
    memory_kb: number;
    projected_score: number;
    max_score: number;
    constraint_result: {
        status: string;
        hard_blocks: string[];
        warnings: { concept: string; line: number; column: number; message: string }[];
    }
    test_results: TestResult[];
    feedback: Feedback;
}

type TestResult = {
    test_key: string;
    description: string;
    passed: boolean;
    stdout: string | null;
    stderr: string | null;
}

type Feedback = {
    summary: string;
    concept_feedback: string;
    warnings: string[];
}

export const assignmentsResponse: AssignmentsDataType = {
    id: "sandbox-result",
    method: "GET",
    path: "/sandbox/jobs/{jobId}/result",
    label: "Sandbox projected feedback (zero-retention)",
    note: "On-screen only. Not stored. Destroyed after session exit. Hallucination guard: LLM explains test results, never re-grades.",
    response: {
      ok: true,
      data: {
        job_id: "j1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
        status: "completed",
        display_name: "Anonymous Copper Narwhal",
        rate_limit: {
          uploads_used: 2,
          uploads_limit: 5,
          window_resets_at: "2025-03-16T10:30:00Z"
        },
        projected_result: {
          judge0_status: { id: 3, description: "Accepted" },
          execution_time_s: 0.041,
          memory_kb: 5124,
          projected_score: 78,
          max_score: 100,
          constraint_result: {
            status: "warning",
            hard_blocks: [],
            warnings: [
              { concept: "sorted", line: 14, column: 12,
                message: "sorted() is a future concept — implement sorting manually." }
            ]
          },
          test_results: [
            { test_key: "test_empty_list",    description: "Empty list returns empty list",  passed: true,  stdout: "[]",            stderr: null },
            { test_key: "test_sorted_asc",    description: "Sorts integers ascending",        passed: true,  stdout: "[1, 2, 3, 4]",  stderr: null },
            { test_key: "test_already_sorted",description: "Already-sorted list unchanged",   passed: false, stdout: "[3, 2, 1]",    stderr: "AssertionError: expected [1, 2, 3]" },
            { test_key: "test_negative",      description: "Handles negative integers",       passed: true,  stdout: "[-3, -1, 2]",  stderr: null },
            { test_key: "test_single_element",description: "Single element list",             passed: false, stdout: null,           stderr: "TypeError: 'int' object is not iterable" }
          ],
          feedback: {
            summary: "Your bubble sort works for most cases but fails when the list is already sorted or contains a single element. Check your inner loop termination — the algorithm should exit early when no swaps occur in a full pass.",
            concept_feedback: "sorted() on line 14 is doing the sorting for you. Replace it with your own comparison and swap logic.",
            warnings: ["sorted() is a future concept for this assignment"]
          }
        },
        zero_retention_notice: "This result is displayed on screen only and will not be saved when you leave this page."
      }
    }
  }