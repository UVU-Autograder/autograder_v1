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
  MOCK_AUDIT_RECORDS,
  MOCK_AUDIT_STATS,
  MOCK_AUDIT_VERIFICATION,
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
  const normalizedWithQuery = path.startsWith("/") ? path : `/${path}`;
  const [normalizedPath] = normalizedWithQuery.split("?");

  // 1. Sandbox courses & assignment catalog
  if (normalizedPath === "/sandbox/courses" && method === "GET") {
    return makeMockResponse(MOCK_SANDBOX_COURSES) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/courses\/[^/]+\/assignments$/) && method === "GET") {
    return makeMockResponse(MOCK_ASSIGNMENTS_CS1410) as { data: T; response: Response };
  }

  const sandboxAssignmentMatch = normalizedPath.match(/^\/sandbox\/courses\/[^/]+\/assignments\/([^/]+)$/);
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
      Boolean(normalizedPath.match(/^\/sandbox\/courses\/[^/]+\/assignments\/[^/]+\/runs$/))) &&
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

  if (normalizedPath.match(/^\/(?:sandbox\/)?runs\/[^/]+\/status$/) && method === "GET") {
    const statusPayload = {
      run_id: "mock-run-001",
      state: "complete",
      queue_position: null,
      eta_band: null,
      message: "Grading complete.",
    };
    return makeMockResponse(statusPayload) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^/]+\/result$/) && method === "GET") {
    return makeMockResponse(MOCK_SANDBOX_RUN_RESULT) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^/]+\/ai-feedback$/) && method === "POST") {
    return makeMockResponse(MOCK_SANDBOX_AI_FEEDBACK) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/sandbox\/runs\/[^/]+\/cancel$/) && method === "POST") {
    return makeMockResponse({ run_id: "mock-run-001", state: "cancelled", message: "Run cancelled." }) as {
      data: T;
      response: Response;
    };
  }

  // 3. Staff authentication
  if (normalizedPath === "/auth/mock-login" && method === "POST") {
    let email = "dev.staff@uvu.edu";
    let displayName: string | null = "Lead Instructor";
    if (init?.body) {
      try {
        const bodyObj = typeof init.body === "string" ? JSON.parse(init.body) : init.body;
        if (bodyObj && typeof bodyObj.email === "string" && bodyObj.email.trim()) {
          email = bodyObj.email.trim().toLowerCase();
        }
        if (bodyObj && typeof bodyObj.display_name === "string" && bodyObj.display_name.trim()) {
          displayName = bodyObj.display_name.trim();
        } else if (email !== "dev.staff@uvu.edu") {
          const prefix = email.split("@")[0];
          displayName = prefix
            .split(/[._-]/)
            .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
            .join(" ");
        }
      } catch {
        // preserve defaults on unparseable body
      }
    }
    const loginPayload = {
      access_token: "mock-jwt-token-lead-staff",
      token_type: "bearer",
      email,
      display_name: displayName,
      roles: ["admin", "instructor"],
    };
    return makeMockResponse(loginPayload) as { data: T; response: Response };
  }

  if (normalizedPath === "/auth/me" && method === "GET") {
    let email = "dev.staff@uvu.edu";
    let displayName: string | null = "Lead Instructor";
    let roles = ["admin", "instructor"];
    if (typeof window !== "undefined") {
      try {
        const storedEmail = localStorage.getItem("email");
        if (storedEmail) email = storedEmail;
        const storedName = localStorage.getItem("displayName");
        if (storedName) displayName = storedName;
        const storedRoles = localStorage.getItem("roles");
        if (storedRoles) {
          const parsed = JSON.parse(storedRoles);
          if (Array.isArray(parsed) && parsed.length > 0) roles = parsed;
        }
      } catch {
        // Fall back to defaults
      }
    }
    const mePayload = {
      email,
      display_name: displayName,
      roles,
    };
    return makeMockResponse(mePayload) as { data: T; response: Response };
  }

  // 4. Staff courses & concepts
  if (normalizedPath === "/staff/courses" && method === "GET") {
    return makeMockResponse(MOCK_STAFF_COURSES) as { data: T; response: Response };
  }

  const courseConceptsMatch = normalizedPath.match(/^\/staff\/courses\/([^/]+)\/concepts$/);
  if (courseConceptsMatch) {
    const conceptsPayload = {
      status: "updated",
      course_id: courseConceptsMatch[1],
      default_concepts: ["variables", "conditionals", "functions"],
      effective_allowed_concepts: ["variables", "conditionals", "functions", "classes", "inheritance"],
      modules: [
        { id: 1, name: "Module 1", concepts: ["variables", "conditionals", "functions"] },
        { id: 2, name: "Module 2", concepts: ["classes", "inheritance"] },
      ],
    };
    return makeMockResponse(conceptsPayload) as { data: T; response: Response };
  }

  // 5. Staff assignment CRUD, setup & artifacts
  const createAssignmentMatch = normalizedPath.match(/^\/staff\/courses\/([^/]+)\/assignments$/);
  if (createAssignmentMatch && method === "POST") {
    let slug = "new-assignment";
    let title = "New Assignment";
    if (init?.body) {
      try {
        const bodyObj = typeof init.body === "string" ? JSON.parse(init.body) : init.body;
        if (bodyObj?.slug) slug = String(bodyObj.slug);
        if (bodyObj?.title) title = String(bodyObj.title);
      } catch {
        // ignore unparseable body
      }
    }
    const createdSetup = {
      ...currentAssignmentSetup,
      course_id: createAssignmentMatch[1],
      assignment_id: slug,
      title,
    };
    return makeMockResponse(createdSetup) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+$/) && method === "DELETE") {
    return makeMockResponse(undefined, 204) as { data: T; response: Response };
  }

  const setupMatch = normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/([^/]+)\/setup$/);
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

  if (normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/artifacts\/[^/]+$/) && method === "GET") {
    const sampleCode = `# Mock instructor test artifact
import pytest

def test_invert():
    """Verifies that invert_pixels flips RGB values accurately."""
    assert True
`;
    return makeMockResponse(sampleCode, 200, "text/plain") as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/artifacts\/[^/]+$/) && method === "DELETE") {
    return makeMockResponse({ status: "deleted" }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/artifacts$/) && method === "POST") {
    return makeMockResponse({ status: "uploaded" }) as { data: T; response: Response };
  }

  if (
    normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/model-solution\/validate$/) ||
    normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/validate-model-solution$/)
  ) {
    return makeMockResponse({ status: "queued", run_id: "val:mock" }) as { data: T; response: Response };
  }

  if (
    normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/model-solution\/status$/) ||
    normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/validation-status$/)
  ) {
    return makeMockResponse({ status: "success", errors: [], score: 100, max_score: 100 }) as {
      data: T;
      response: Response;
    };
  }

  if (
    normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/ai-generate-tests$/) &&
    method === "POST"
  ) {
    const generated = `import pytest
import main


@pytest.mark.ag_edge_cases
def test_edge_cases_boundary():
    """Verifies boundary and empty-input behavior."""
    assert hasattr(main, "__name__"), "Expected main module to load cleanly on boundary inputs."
`;
    return makeMockResponse({
      generated_code: generated,
      explanation:
        "Generated boundary and edge-case pytest checks annotated with `@pytest.mark.ag_edge_cases`.",
    }) as { data: T; response: Response };
  }

  // 6. Staff official runs & review
  const courseSectionsMatch = normalizedPath.match(/^\/staff\/courses\/([^/]+)\/sections$/);
  if ((courseSectionsMatch || normalizedPath.match(/\/assignments\/[^/]+\/sections$/)) && method === "GET") {
    return makeMockResponse({
      course_id: courseSectionsMatch?.[1] || "cs1410",
      sections: [
        {
          id: 1,
          crn: "12345",
          is_active: true,
          name: "Section 001",
          section_number: "001",
          term: "Fall 2026",
          instructor_name: "Staff Dev",
        },
        {
          id: 2,
          crn: "12346",
          is_active: true,
          name: "Section 002",
          section_number: "002",
          term: "Fall 2026",
          instructor_name: "Staff Dev",
        },
      ],
    }) as { data: T; response: Response };
  }

  if (
    (normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/validate$/) ||
      normalizedPath.match(/\/assignments\/[^/]+\/preflight$/)) &&
    method === "POST"
  ) {
    return makeMockResponse({ passed: true, errors: [], ready: true, issues: [] }) as {
      data: T;
      response: Response;
    };
  }

  if (
    (normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/submissions\/ingest$/) ||
      normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/runs$/)) &&
    method === "POST"
  ) {
    return makeMockResponse({
      run_id: "101",
      status: "complete",
      workflow_type: "official",
      total_submission_count: 24,
      created_at: new Date().toISOString(),
      message: "Canvas archive ingested into mock run 101.",
    }) as { data: T; response: Response };
  }

  if (
    (normalizedPath.match(/\/runs\/[^/]+\/summary$/) ||
      normalizedPath.match(/^\/staff\/courses\/[^/]+\/assignments\/[^/]+\/runs\/[^/]+$/)) &&
    method === "GET"
  ) {
    return makeMockResponse(MOCK_RUN_SUMMARY) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/[^/]+\/cleanup$/) && method === "POST") {
    return makeMockResponse({ status: "cleaned" }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/[^/]+\/details$/) && method === "GET") {
    return makeMockResponse(MOCK_RUN_DETAILS) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/[^/]+\/students\/[^/]+\/files$/) && method === "GET") {
    return makeMockResponse({ files: MOCK_STUDENT_FILES }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/[^/]+\/students\/[^/]+\/files\/content$/) && method === "GET") {
    const studentCode = `# Student submission code (Mock)
def invert_pixels(pixels):
    return [[255 - val for val in row] for row in pixels]
`;
    return makeMockResponse({
      kind: "text",
      content: studentCode,
    }) as { data: T; response: Response };
  }

  if (normalizedPath.match(/\/runs\/[^/]+\/students\/[^/]+\/files\/[^/]+$/) && method === "GET") {
    const studentCode = `# Student submission code (Mock)
def invert_pixels(pixels):
    return [[255 - val for val in row] for row in pixels]
`;
    return makeMockResponse(studentCode, 200, "text/plain") as { data: T; response: Response };
  }

  const manualGradesMatch = normalizedPath.match(/\/runs\/[^/]+\/students\/([^/]+)\/manual-grades$/);
  if (manualGradesMatch && method === "POST") {
    const canvasId = manualGradesMatch[1];
    const targetStudent =
      MOCK_RUN_DETAILS.students.find((s) => s.canvas_id === canvasId) || MOCK_RUN_DETAILS.students[0];
    return makeMockResponse(targetStudent) as { data: T; response: Response };
  }

  // 7. Staff Admin API
  if (normalizedPath === "/staff/admin/courses" && method === "GET") {
    return makeMockResponse(MOCK_ADMIN_COURSES) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/courses" && method === "POST") {
    return makeMockResponse(MOCK_ADMIN_COURSES[0]) as { data: T; response: Response };
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

  if (normalizedPath.match(/^\/staff\/admin\/courses\/\d+\/sections$/) && method === "POST") {
    return makeMockResponse(MOCK_SECTIONS[0]) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/admin\/sections\/\d+$/) && method === "PUT") {
    return makeMockResponse(MOCK_SECTIONS[0]) as { data: T; response: Response };
  }

  if (normalizedPath.match(/^\/staff\/admin\/sections\/\d+$/) && method === "DELETE") {
    return makeMockResponse(undefined, 204) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/monitoring" && method === "GET") {
    return makeMockResponse(MOCK_MONITORING) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/logs" && method === "GET") {
    const url = new URL(`http://localhost${normalizedWithQuery}`);
    const search = url.searchParams.get("search")?.toLowerCase();
    const event = url.searchParams.get("event");
    const workflow = url.searchParams.get("workflow_type");
    const page = parseInt(url.searchParams.get("page") || "1", 10);
    const pageSize = parseInt(url.searchParams.get("page_size") || "25", 10);

    let filtered = [...MOCK_AUDIT_RECORDS];
    if (search) {
      filtered = filtered.filter(
        (r) =>
          r.event.toLowerCase().includes(search) ||
          r.workflow_type?.toLowerCase().includes(search) ||
          r.course_id?.toLowerCase().includes(search)
      );
    }
    if (event) {
      filtered = filtered.filter((r) => r.event === event);
    }
    if (workflow) {
      filtered = filtered.filter((r) => r.workflow_type === workflow);
    }

    const total = filtered.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const offset = (page - 1) * pageSize;
    const items = filtered.slice(offset, offset + pageSize);

    return makeMockResponse({
      items,
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    }) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/logs/stats" && method === "GET") {
    return makeMockResponse(MOCK_AUDIT_STATS) as { data: T; response: Response };
  }

  if (normalizedPath === "/staff/admin/logs/verify" && method === "POST") {
    return makeMockResponse(MOCK_AUDIT_VERIFICATION) as { data: T; response: Response };
  }

  // Fallback for unhandled mock paths: return null
  return null;
}

export async function handleMockDownload(path: string): Promise<Blob | null> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (normalizedPath.includes("/export/grades.csv") || normalizedPath.includes("/export/csv")) {
    const csvContent = "Student,Canvas ID,Score,Max Score,Status\nJohn Doe,1001,100,100,success\nJane Smith,1002,80,100,warning\n";
    return new Blob([csvContent], { type: "text/csv" });
  }

  if (normalizedPath.includes("/export/feedback.zip") || normalizedPath.includes("/export/feedback")) {
    // Return dummy zip blob
    return new Blob(["PK\x05\x06" + "\x00".repeat(18)], { type: "application/zip" });
  }

  return new Blob(["Mock download file content"], { type: "text/plain" });
}
