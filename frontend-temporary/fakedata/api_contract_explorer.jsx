import { useState } from "react"

export const ENDPOINTS = [
  {
    group: "Auth",
    items: [
      {
        id: "auth-session",
        method: "POST",
        path: "/auth/session",
        label: "Staff login (MS OAuth callback)",
        note: "Returns user identity and role grants. @uvu.edu enforced server-side.",
        response: {
          ok: true,
          data: {
            user: {
              id: "f3a9c2b1-e4d7-4f6a-8b2c-5d9e1f3a7b4c",
              email: "easton.parkhurst@uvu.edu",
              name: "Easton Parkhurst",
              is_admin: false,
              roles: [
                { role: "instructor", course_id: "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c", section_id: null },
                { role: "ia",         course_id: "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a", section_id: "s1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d" }
              ]
            },
            session: {
              expires_at: "2025-04-23T09:00:00Z"
            }
          }
        }
      }
    ]
  },
  {
    group: "Courses",
    items: [
      {
        id: "courses-list",
        method: "GET",
        path: "/courses",
        label: "Staff course list",
        note: "Scoped to the authenticated user's role grants. No student data.",
        response: {
          ok: true,
          data: [
            {
              id: "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
              code: "CS 1400",
              name: "Introduction to Programming",
              term: "Spring 2025",
              sections: [
                { id: "s1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", crn: "12345", name: "Section 01" },
                { id: "s2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e", crn: "12346", name: "Section 02" }
              ],
              assignment_count: 4,
              sandbox_enabled_count: 3
            }
          ],
          meta: { total: 1 }
        }
      }
    ]
  },
  {
    group: "Assignments",
    items: [
      {
        id: "assignments-list",
        method: "GET",
        path: "/courses/{courseId}/assignments",
        label: "Assignment list for a course",
        note: "Course-shared. Section scope applies to runs, not setup.",
        response: {
          ok: true,
          data: [
            {
              id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
              title: "Assignment 3: Bubble Sort",
              canvas_id: "canvas_assign_7742",
              due_date: "2025-03-15T23:59:00Z",
              sandbox_enabled: true,
              opens_at: null,
              config: { id: "cfg-uuid", updated_at: "2025-02-20T14:30:00Z" },
              artifact_count: 2,
              concepts_inherited: true,
              run_count: 2
            },
            {
              id: "a2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
              title: "Assignment 4: Recursion",
              canvas_id: "canvas_assign_7743",
              due_date: "2025-04-01T23:59:00Z",
              sandbox_enabled: false,
              opens_at: "2025-04-01T00:00:00Z",
              config: { id: "cfg-uuid-2", updated_at: "2025-03-01T10:00:00Z" },
              artifact_count: 2,
              concepts_inherited: true,
              run_count: 0
            }
          ],
          meta: { total: 4, page: 1 }
        }
      },
      {
        id: "assignment-config",
        method: "GET",
        path: "/assignments/{id}/config",
        label: "Full assignment config (wizard output + concepts + artifacts)",
        note: "config.json is the source of truth. test_cases are derived projections only.",
        response: {
          ok: true,
          data: {
            assignment_id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            title: "Assignment 3: Bubble Sort",
            canvas_id: "canvas_assign_7742",
            due_date: "2025-03-15T23:59:00Z",
            sandbox_enabled: true,
            config: {
              id: "cfg-uuid",
              updated_at: "2025-02-20T14:30:00Z",
              raw: {
                assignment_title: "Bubble Sort",
                language: "python",
                max_score: 100,
                resource_limits: { time_limit_s: 10, memory_limit_kb: 262144 },
                test_cases: [
                  { test_key: "test_empty_list",    description: "Empty list returns empty list",  points: 20 },
                  { test_key: "test_sorted_asc",    description: "Sorts integers ascending",        points: 20 },
                  { test_key: "test_already_sorted",description: "Already-sorted list unchanged",   points: 20 },
                  { test_key: "test_negative",      description: "Handles negative integers",       points: 20 },
                  { test_key: "test_single_element",description: "Single element list",             points: 20 }
                ],
                constraints: [
                  { type: "forbidden_call",      target: "sorted",      message: "sorted() is a future concept",          report_only: false },
                  { type: "forbidden_call",      target: "sort",        message: "list.sort() is a future concept",       report_only: false },
                  { type: "required_definition", target: "bubble_sort", message: "bubble_sort function must be defined",  report_only: false }
                ]
              }
            },
            effective_concepts: {
              source: "course_defaults + assignment_additions",
              course_defaults: ["print","input","len","range","for","while","if","def","list","int","str","return"],
              assignment_additions: [],
              effective_list: ["print","input","len","range","for","while","if","def","list","int","str","return"]
            },
            artifacts: [
              { id: "art-uuid-1", artifact_type: "pytest_file",    display_name: "test_bubble_sort.py" },
              { id: "art-uuid-2", artifact_type: "model_solution", display_name: "bubble_sort_solution.py" }
            ]
          }
        }
      }
    ]
  },
  {
    group: "Official runs",
    items: [
      {
        id: "runs-post",
        method: "POST",
        path: "/runs/official",
        label: "Launch official grading run (Canvas ZIP upload)",
        note: "multipart/form-data. Returns run_id immediately. ZIP extracted to ephemeral workspace — never persisted.",
        response: {
          ok: true,
          data: {
            run_id: "r1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
            workflow_type: "official",
            status: "queued",
            assignment_id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            section_id: "s1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            queued_at: "2025-03-16T09:00:00Z",
            ingestion: {
              total_files_found: 28,
              matched: 26,
              unmatched: 1,
              duplicate_matches: 1
            }
          }
        }
      },
      {
        id: "runs-status-processing",
        method: "GET",
        path: "/runs/{id}/status",
        label: "Run status — in progress (2s polling)",
        note: "Only aggregate counts. No student identifiers, filenames, or code snippets.",
        response: {
          ok: true,
          data: {
            run_id: "r1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
            workflow_type: "official",
            status: "processing",
            assignment_id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            section_id: "s1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            started_at: "2025-03-16T09:00:05Z",
            progress: {
              total: 28,
              completed: 14,
              success: 11,
              warning: 2,
              failure: 1,
              timeout: 0,
              pending: 14
            }
          }
        }
      },
      {
        id: "runs-status-complete",
        method: "GET",
        path: "/runs/{id}/status",
        label: "Run status — completed",
        note: "RunSummary contract. Failure categories are coarse only. No traceback bodies, no feedback text.",
        response: {
          ok: true,
          data: {
            run_id: "r1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
            workflow_type: "official",
            status: "completed",
            assignment_id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            section_id: "s1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            started_at: "2025-03-16T09:00:05Z",
            completed_at: "2025-03-16T09:08:42Z",
            summary: {
              total_submissions: 28,
              success_count: 22,
              warning_count: 4,
              failure_count: 1,
              timeout_count: 1,
              failure_categories: {
                hard_block: 0,
                compile_error: 1,
                runtime_error: 0,
                timeout: 1,
                unmatched_filename: 1,
                duplicate_match: 1
              },
              token_usage: {
                prompt_tokens: 48200,
                completion_tokens: 12400
              }
            },
            exports_available: ["csv", "html_zip"],
            moss_available: true
          }
        }
      }
    ]
  },
  {
    group: "Sandbox",
    items: [
      {
        id: "sandbox-courses",
        method: "GET",
        path: "/sandbox/courses",
        label: "Globally visible sandbox-enabled courses (no auth required)",
        note: "No roster lookup. sandbox_enabled and opens_at gating only.",
        response: {
          ok: true,
          data: {
            courses: [
              {
                id: "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
                code: "CS 1400",
                name: "Introduction to Programming",
                assignments: [
                  { id: "uuid-1", title: "Assignment 1: Hello World",  sandbox_available: true,  opens_at: null },
                  { id: "uuid-2", title: "Assignment 2: Functions",    sandbox_available: true,  opens_at: null },
                  { id: "uuid-3", title: "Assignment 3: Bubble Sort",  sandbox_available: true,  opens_at: null },
                  { id: "uuid-4", title: "Assignment 4: Recursion",    sandbox_available: false, opens_at: "2025-04-01T00:00:00Z" }
                ]
              }
            ]
          }
        }
      },
      {
        id: "sandbox-submit",
        method: "POST",
        path: "/sandbox/submit",
        label: "Sandbox code submission",
        note: "Rate-limited to 5/hr per session. Returns job_id for polling. Session seed generates anonymous display name.",
        response: {
          ok: true,
          data: {
            job_id: "j1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
            status: "queued",
            display_name: "Anonymous Copper Narwhal",
            rate_limit: {
              uploads_used: 2,
              uploads_limit: 5,
              window_resets_at: "2025-03-16T10:30:00Z"
            }
          }
        }
      },
      {
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
    ]
  },
  {
    group: "Errors",
    items: [
      {
        id: "err-rate-limit",
        method: "POST",
        path: "/sandbox/submit → 429",
        label: "Rate limit exceeded",
        note: "Returned when the session has used all 5 uploads in the rolling window.",
        response: {
          ok: false,
          error: {
            code: "RATE_LIMIT_EXCEEDED",
            message: "Sandbox upload limit reached for this session.",
            details: { uploads_used: 5, uploads_limit: 5, window_resets_at: "2025-03-16T10:30:00Z" }
          }
        }
      },
      {
        id: "err-invalid-zip",
        method: "POST",
        path: "/runs/official → 422",
        label: "Invalid Canvas ZIP",
        note: "Rejected before queueing. No extraction attempted on malformed archives.",
        response: {
          ok: false,
          error: {
            code: "INVALID_CANVAS_ZIP",
            message: "The uploaded archive does not match the expected Canvas ZIP format.",
            details: { reason: "no_recognizable_submissions", files_inspected: 3 }
          }
        }
      },
      {
        id: "err-section-access",
        method: "POST",
        path: "/runs/official → 403",
        label: "Section access denied",
        note: "IA attempting to run on a section not in their access grant.",
        response: {
          ok: false,
          error: {
            code: "SECTION_ACCESS_DENIED",
            message: "You do not have run authority for this section.",
            details: { section_id: "s2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e", actor_role: "ia" }
          }
        }
      },
      {
        id: "err-hard-block",
        method: "GET",
        path: "/sandbox/jobs/{jobId}/result (hard block)",
        label: "Execution hard-blocked by constraint",
        note: "Code did not execute. AST check found a security-sensitive or hard-block constraint violation.",
        response: {
          ok: true,
          data: {
            job_id: "j9z8y7x6-w5v4-u3t2-s1r0-q9p8o7n6m5l4",
            status: "completed",
            display_name: "Anonymous Slate Pangolin",
            rate_limit: { uploads_used: 3, uploads_limit: 5, window_resets_at: "2025-03-16T10:30:00Z" },
            projected_result: {
              judge0_status: null,
              execution_time_s: null,
              memory_kb: null,
              projected_score: 0,
              max_score: 100,
              constraint_result: {
                status: "hard_blocked",
                hard_blocks: [
                  { concept: "import os", line: 2, column: 0, message: "System-level imports are not permitted." }
                ],
                warnings: []
              },
              test_results: [],
              feedback: {
                summary: "Your submission was not executed because it contains a security-sensitive import on line 2. Remove the import and resubmit.",
                concept_feedback: null,
                warnings: []
              }
            },
            zero_retention_notice: "This result is displayed on screen only and will not be saved when you leave this page."
          }
        }
      }
    ]
  }
]

const METHOD_COLORS = {
  GET:  { bg: "#E1F5EE", text: "#0F6E56", border: "#1D9E75" },
  POST: { bg: "#E6F1FB", text: "#185FA5", border: "#378ADD" },
}

function JsonLine({ line, depth = 0 }) {
  return (
    <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: "1.7",
                  color: "var(--color-text-primary)", whiteSpace: "pre" }}>
      {line}
    </div>
  )
}

function highlight(json) {
  return json
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
      let cls = "#B45309"
      if (/^"/.test(match)) {
        if (/:$/.test(match)) cls = "#185FA5"
        else cls = "#3B6D11"
      } else if (/true|false/.test(match)) cls = "#7D3C98"
      else if (/null/.test(match)) cls = "#888780"
      return `<span style="color:${cls}">${match}</span>`
    })
}

export default function ApiExplorer() {
  const [activeId, setActiveId] = useState("runs-status-complete")
  const [copyLabel, setCopyLabel] = useState("Copy")

  const allItems = ENDPOINTS.flatMap(g => g.items)
  const active = allItems.find(i => i.id === activeId)
  const json = JSON.stringify(active?.response, null, 2)

  function copy() {
    navigator.clipboard.writeText(json)
    setCopyLabel("Copied")
    setTimeout(() => setCopyLabel("Copy"), 1800)
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 0,
                  border: "0.5px solid var(--color-border-tertiary)",
                  borderRadius: "var(--border-radius-lg)", overflow: "hidden",
                  background: "var(--color-background-primary)" }}>

      <div style={{ borderRight: "0.5px solid var(--color-border-tertiary)",
                    background: "var(--color-background-secondary)",
                    overflowY: "auto", maxHeight: 640 }}>
        {ENDPOINTS.map(group => (
          <div key={group.group}>
            <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: "0.06em",
                          color: "var(--color-text-tertiary)", padding: "10px 12px 4px",
                          textTransform: "uppercase" }}>
              {group.group}
            </div>
            {group.items.map(item => {
              const mc = METHOD_COLORS[item.method] || METHOD_COLORS.GET
              const isActive = item.id === activeId
              return (
                <button key={item.id} onClick={() => setActiveId(item.id)}
                  style={{ display: "block", width: "100%", textAlign: "left",
                           padding: "6px 12px", border: "none", cursor: "pointer",
                           background: isActive ? "var(--color-background-primary)" : "transparent",
                           borderLeft: isActive ? `2px solid ${mc.border}` : "2px solid transparent" }}>
                  <span style={{ fontSize: 10, fontWeight: 500, padding: "1px 5px",
                                 borderRadius: 3, background: mc.bg, color: mc.text,
                                 marginRight: 6 }}>
                    {item.method}
                  </span>
                  <span style={{ fontSize: 11, color: isActive
                    ? "var(--color-text-primary)" : "var(--color-text-secondary)" }}>
                    {item.label}
                  </span>
                </button>
              )
            })}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", maxHeight: 640 }}>
        <div style={{ padding: "12px 16px", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            {(() => { const mc = METHOD_COLORS[active?.method] || METHOD_COLORS.GET; return (
              <span style={{ fontSize: 11, fontWeight: 500, padding: "2px 7px",
                             borderRadius: 4, background: mc.bg, color: mc.text }}>
                {active?.method}
              </span>
            )})()}
            <code style={{ fontSize: 12, color: "var(--color-text-primary)",
                           background: "var(--color-background-secondary)",
                           padding: "2px 7px", borderRadius: 4 }}>
              {active?.path}
            </code>
          </div>
          <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--color-text-secondary)" }}>
            {active?.note}
          </p>
        </div>

        <div style={{ flex: 1, overflowY: "auto", position: "relative" }}>
          <button onClick={copy}
            style={{ position: "absolute", top: 8, right: 8, zIndex: 2,
                     fontSize: 11, padding: "3px 10px",
                     color: "var(--color-text-secondary)", cursor: "pointer",
                     background: "var(--color-background-secondary)",
                     border: "0.5px solid var(--color-border-secondary)",
                     borderRadius: "var(--border-radius-md)" }}>
            {copyLabel}
          </button>
          <pre style={{ margin: 0, padding: "14px 16px", fontSize: 12,
                        fontFamily: "var(--font-mono)", lineHeight: 1.7, overflowX: "auto",
                        color: "var(--color-text-primary)", background: "transparent" }}
            dangerouslySetInnerHTML={{ __html: highlight(json) }} />
        </div>
      </div>
    </div>
  )
}
