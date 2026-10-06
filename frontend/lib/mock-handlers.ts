import {
  MOCK_ADMIN_ACCESS,
  MOCK_ADMIN_COURSES,
  MOCK_ADMIN_USERS,
  MOCK_ASSIGNMENT_DETAILS_DS1,
  MOCK_ASSIGNMENT_DETAILS_LAB1,
  MOCK_ASSIGNMENTS_CS1410,
  MOCK_CONCEPTS_METADATA,
  MOCK_MONITORING,
  MOCK_RUN_DETAILS,
  MOCK_RUN_SUMMARY,
  MOCK_SANDBOX_AI_FEEDBACK,
  MOCK_SANDBOX_COURSES,
  MOCK_SANDBOX_RUN_RESULT,
  MOCK_SECTIONS,
  MOCK_STAFF_ASSIGNMENT_SETUP_LAB1,
  MOCK_STAFF_COURSES,
  MOCK_STUDENT_FILES,
} from "./mock-data";

function makeMockResponse<T>(
  data: T,
  status = 200,
  contentType = "application/json"
): { data: T; response: Response } {
  const bodyText = typeof data === "string" ? data : JSON.stringify(data);
  const response = new Response(bodyText, {
    status,
    headers: {
      "content-type": contentType,
      "x-refresh-token": "mock-refreshed-token",
    },
  });
  return { data, response };
}

// In-memory editable assignment setup to mirror UI saves
let currentAssignmentSetup = { ...MOCK_STAFF_ASSIGNMENT_SETUP_LAB1 };

export async function handleMockRequest<T>(
  path: string,
  init?: RequestInit
): Promise<{ data: T; response: Response } | null> {
  const method = (init?.method || "GET").toUpperCase();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  // 1. Sandbox courses & assignment catalog
  if (normalizedPath === "/sandbox/courses" && method === "GET") {
    return makeMockResponse(MOCK_SANDBOX_COURSES) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/courses\/\d+\/assignments$/) && method === "GET") {
    return makeMockResponse(MOCK_ASSIGNMENTS_CS1410) as { data: T; response: Response };
  }

  const sandboxAssignmentMatch = normalizedPath.match(/^\/sandbox\/courses\/\d+\/assignments\/([^\/]+)$/);
  if (sandboxAssignmentMatch && method === "GET") {
    const slug = sandboxAssignmentMatch[1];
    const assignment = slug === "ds1" ? MOCK_ASSIGNMENT_DETAILS_DS1 : MOCK_ASSIGNMENT_DETAILS_LAB1;
    return makeMockResponse(assignment) as { data: T; response: Response };
  }

  if (normalizedPath === "/sandbox/concepts/metadata" && method === "GET") {
    return makeMockResponse(MOCK_CONCEPTS_METADATA) as { data: T; response: Response };
  }

  // 2. Sandbox run lifecycle
  if (
    (normalizedPath === "/sandbox/runs" ||
      Boolean(normalizedPath.match(/^\/sandbox\/courses\/\d+\/assignments\/[^\/]+\/runs$/))) &&
    method === "POST"
  ) {
    const createPayload = {
      run_id: "mock-run-001",
      sandbox_session: "mock-sess-001",
      status_url: "/sandbox/runs/mock-run-001/status",
      result_url: "/sandbox/runs/mock-run-001/result",
      upload_quota: {
        limit: 10,
        window_seconds: 3600,
        remaining: 9,
        reset_at: new Date(Date.now() + 3600000).toISOString(),
      },
      initial_status: {
        run_id: "mock-run-001",
        state: "complete",
        queue_position: null,
        eta_band: null,
        message: "Offline mock grading complete.",
      },
    };
    return makeMockResponse(createPayload) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^\/]+\/status$/) && method === "GET") {
    const statusPayload = {
      run_id: "mock-run-001",
      state: "complete",
      queue_position: null,
      eta_band: null,
      message: "Grading complete.",
    };
    return makeMockResponse(statusPayload) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^\/]+\/result$/) && method === "GET") {
    return makeMockResponse(MOCK_SANDBOX_RUN_RESULT) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^\/]+\/ai-feedback$/) && method === "POST") {
    return makeMockResponse(MOCK_SANDBOX_AI_FEEDBACK) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^\/]+\/cancel$/) && method === "POST") {
    return makeMockResponse({ run_id: "mock-run-001", state: "cancelled", message: "Run cancelled." }) as {
      data: T;
      response: Response;
    };
  }

  // 3. Staff authentication
  if (normalizedPath === "/auth/mock-login" && method === "POST") {
    const loginPayload = {
      access_token: "mock-jwt-token-lead-staff",
      token_type: "bearer",
      email: "dev.staff@uvu.edu",
      display_name: "Lead Instructor",
      roles: ["admin", "instructor"],
    };
    return makeMockResponse(loginPayload) as { data: T; response: Response };
  }

  // 4. Staff courses & concepts
  if (normalizedPath === "/staff/courses" && method === "GET") {
    return makeMockResponse(MOCK_STAFF_COURSES) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/\d+\/concepts$/)) {
    if (method === "PUT") {
      return makeMockResponse({ status: "updated" }) as { data: T; response: Response };
    }
    return makeMockResponse({
      effective_allowed_concepts: ["variables", "conditionals", "functions", "classes", "inheritance"],
      modules: [
        { id: 1, name: "Module 1", concepts: ["variables", "conditionals", "functions"] },
        { id: 2, name: "Module 2", concepts: ["classes", "inheritance"] },
      ],
    }) as { data: T; response: Response };
  }

  // 5. Staff assignment setup & artifacts
  const setupMatch = normalizedPath.match(/^\/staff\/courses\/\d+\/assignments\/([^\/]+)\/setup$/);
  if (setupMatch) {
    if (method === "PUT" && init?.body) {
      try {
        const bodyObj = typeof init.body === "string" ? JSON.parse(init.body) : init.body;
        currentAssignmentSetup = {
          ...currentAssignmentSetup,
          ...bodyObj,
        };
      } catch {
        // preserve current state on unparseable body
      }
      return makeMockResponse(currentAssignmentSetup) as { data: T; response: Response };
    }
    return makeMockResponse(currentAssignmentSetup) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/\d+\/assignments\/[^\/]+\/artifacts\/[^\/]+$/) && method === "GET") {
    const sampleCode = `# Mock instructor test artifact
import pytest

def test_invert():
    """Verifies that invert_pixels flips RGB values accurately."""
    assert True
`;
    return makeMockResponse(sampleCode, 200, "text/plain") as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/\d+\/assignments\/[^\/]+\/artifacts$/) && method === "POST") {
    return makeMockResponse({ status: "uploaded" }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/\d+\/assignments\/[^\/]+\/model-solution\/validate$/)) {
    return makeMockResponse({ status: "valid", error: null }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/\d+\/assignments\/[^\/]+\/model-solution\/status$/)) {
    return makeMockResponse({ status: "valid", error: null }) as { data: T; response: Response };
  }

  // 6. Staff official runs & review
  if (normalizedPath.match(/\/assignments\/[^\/]+\/sections$/) && method === "GET") {
    return makeMockResponse({
      sections: [
        { id: 1, name: "Section 001", section_number: "001", term: "Fall 2026", instructor_name: "Staff Dev" },
      ],
    }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/assignments\/[^\/]+\/preflight$/) && method === "POST") {
    return makeMockResponse({ ready: true, issues: [] }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/\d+\/assignments\/[^\/]+\/runs$/) && method === "POST") {
    return makeMockResponse({
      run_id: 101,
      status: "created",
      message: "Canvas archive ingested into mock run 101.",
    }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/\d+\/summary$/) && method === "GET") {
    return makeMockResponse(MOCK_RUN_SUMMARY) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/\d+\/details$/) && method === "GET") {
    return makeMockResponse(MOCK_RUN_DETAILS) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/\d+\/students\/[^\/]+\/files$/) && method === "GET") {
    return makeMockResponse({ files: MOCK_STUDENT_FILES }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/\d+\/students\/[^\/]+\/files\/[^\/]+$/) && method === "GET") {
    const studentCode = `# Student submission code (Mock)
def invert_pixels(pixels):
    return [[255 - val for val in row] for row in pixels]
`;
    return makeMockResponse(studentCode, 200, "text/plain") as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/\d+\/students\/[^\/]+\/manual-grades$/) && method === "POST") {
    return makeMockResponse(MOCK_RUN_DETAILS.students[0]) as { data: T; response: Response };
  }

  // 7. Staff Admin API
  if (normalizedPath === "/staff/admin/courses" && method === "GET") {
    return makeMockResponse(MOCK_ADMIN_COURSES) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/admin\/courses\/\d+$/) && method === "PUT") {
    return makeMockResponse(MOCK_ADMIN_COURSES[0]) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/admin\/courses\/\d+$/) && method === "DELETE") {
    return makeMockResponse(undefined, 204) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/users" && method === "GET") {
    return makeMockResponse(MOCK_ADMIN_USERS) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/access" && method === "GET") {
    return makeMockResponse(MOCK_ADMIN_ACCESS) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/access" && method === "POST") {
    return makeMockResponse(MOCK_ADMIN_ACCESS[0]) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/admin\/access\/\d+$/) && method === "DELETE") {
    return makeMockResponse(undefined, 204) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/admin\/courses\/\d+\/sections$/) && method === "GET") {
    return makeMockResponse(MOCK_SECTIONS) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/monitoring" && method === "GET") {
    return makeMockResponse(MOCK_MONITORING) as { data: T; response: Response };
  }

  // Fallback for unhandled mock paths: return 404 response
  return null;
}

export async function handleMockDownload(path: string): Promise<Blob | null> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (normalizedPath.includes("/export/grades.csv")) {
    const csvContent = "Student,Canvas ID,Score,Max Score,Status\nJohn Doe,1001,100,100,success\nJane Smith,1002,80,100,warning\n";
    return new Blob([csvContent], { type: "text/csv" });
  }

  if (normalizedPath.includes("/export/feedback.zip")) {
    // Return dummy zip blob
    return new Blob(["PK\x05\x06" + "\x00".repeat(18)], { type: "application/zip" });
  }

  return new Blob(["Mock download file content"], { type: "text/plain" });
}
