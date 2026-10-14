import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { apiClient, isMockApiEnabled } from "../api-client";
import { streamSandboxAiFeedback } from "../../features/assignments/api";
import {
  MOCK_ASSIGNMENT_DETAILS_LAB1,
  MOCK_ASSIGNMENTS_CS1400,
  MOCK_ASSIGNMENTS_CS1410,
  MOCK_AUDIT_STATS,
  MOCK_AUDIT_VERIFICATION,
  MOCK_SANDBOX_COURSES,
  MOCK_STAFF_COURSES,
} from "../mock-data";

describe("Frontend Mock API & Interception Layer", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
    localStorage.clear();
    process.env = { ...originalEnv };
  });

  function setNodeEnv(val: string) {
    Object.defineProperty(process.env, "NODE_ENV", {
      value: val,
      configurable: true,
      writable: true,
    });
  }

  afterEach(() => {
    process.env = originalEnv;
  });

  describe("isMockApiEnabled", () => {
    it("returns true by default in development mode", () => {
      setNodeEnv("development");
      delete process.env.NEXT_PUBLIC_MOCK_API;
      expect(isMockApiEnabled()).toBe(true);
    });

    it("returns false if NEXT_PUBLIC_MOCK_API is 'false'", () => {
      setNodeEnv("development");
      process.env.NEXT_PUBLIC_MOCK_API = "false";
      expect(isMockApiEnabled()).toBe(false);
    });

    it("strictly returns false in production regardless of other flags", () => {
      setNodeEnv("production");
      process.env.NEXT_PUBLIC_MOCK_API = "true";
      localStorage.setItem("mock_api", "true");
      expect(isMockApiEnabled()).toBe(false);
    });

    it("respects sessionStorage and localStorage overrides in development", () => {
      setNodeEnv("development");
      process.env.NEXT_PUBLIC_MOCK_API = "true";

      sessionStorage.setItem("mock_api", "false");
      expect(isMockApiEnabled()).toBe(false);

      sessionStorage.clear();
      localStorage.setItem("mock_api", "false");
      expect(isMockApiEnabled()).toBe(false);

      localStorage.setItem("mock_api", "true");
      process.env.NEXT_PUBLIC_MOCK_API = "false";
      expect(isMockApiEnabled()).toBe(true);
    });
  });

  describe("apiClient routing in mock mode", () => {
    beforeEach(() => {
      setNodeEnv("development");
      delete process.env.NEXT_PUBLIC_MOCK_API;
    });

    it("fetches sandbox courses correctly", async () => {
      const result = await apiClient.get<typeof MOCK_SANDBOX_COURSES>("/sandbox/courses");
      expect(result).toEqual(MOCK_SANDBOX_COURSES);
    });

    it("fetches course assignments correctly", async () => {
      const result = await apiClient.get<typeof MOCK_ASSIGNMENTS_CS1410>("/sandbox/courses/cs1410/assignments");
      expect(result).toEqual(MOCK_ASSIGNMENTS_CS1410);

      const legacyResult = await apiClient.get<typeof MOCK_ASSIGNMENTS_CS1410>("/sandbox/courses/1/assignments");
      expect(legacyResult).toEqual(MOCK_ASSIGNMENTS_CS1410);
    });

    it("fetches single assignment details with full rubric and description", async () => {
      const result = await apiClient.get<typeof MOCK_ASSIGNMENT_DETAILS_LAB1>(
        "/sandbox/courses/cs1410/assignments/lab1"
      );
      expect(result.id).toBe("lab1");
      expect(result.rubric.length).toBeGreaterThan(0);
      expect(result.description).toContain("Lab 1: Image Processing");
    });

    it("creates a sandbox run and polls status/result", async () => {
      const createRes = await apiClient.post<{ run_id: string; status_url: string; result_url: string }>(
        "/sandbox/runs",
        {}
      );
      expect(createRes.run_id).toBe("mock-run-001");

      const statusRes = await apiClient.get<{ state: string }>(createRes.status_url);
      expect(statusRes.state).toBe("complete");

      const resultRes = await apiClient.get<{ projected_score: number; max_score: number; test_summaries: unknown[] }>(
        createRes.result_url
      );
      expect(resultRes.projected_score).toBe(100);
      expect(resultRes.test_summaries.length).toBeGreaterThan(0);
    });

    it("requests AI feedback in sandbox", async () => {
      const feedback = await apiClient.post<{ ai_feedback: string; model: string }>(
        "/sandbox/runs/mock-run-001/ai-feedback",
        {}
      );
      expect(feedback.ai_feedback).toBeTruthy();
      expect(feedback.model).toContain("vllm");
    });

    it("performs staff mock login and stores token", async () => {
      const loginRes = await apiClient.post<{ access_token: string; email: string; display_name: string; roles: string[] }>("/auth/mock-login", {
        email: "custom.staff@uvu.edu",
        display_name: "Custom Staff",
      });
      expect(loginRes.access_token).toBeTruthy();
      expect(loginRes.email).toBe("custom.staff@uvu.edu");
      expect(loginRes.display_name).toBe("Custom Staff");
      expect(loginRes.roles).toContain("instructor");
    });

    it("fetches authenticated staff profile via /auth/me in mock mode", async () => {
      localStorage.setItem("email", "custom.staff@uvu.edu");
      localStorage.setItem("displayName", "Custom Staff");
      localStorage.setItem("roles", JSON.stringify(["admin", "instructor"]));

      const meRes = await apiClient.get<{ email: string; display_name: string | null; roles: string[] }>("/auth/me");
      expect(meRes.email).toBe("custom.staff@uvu.edu");
      expect(meRes.display_name).toBe("Custom Staff");
      expect(meRes.roles).toEqual(["admin", "instructor"]);
    });

    it("fetches staff courses and concepts", async () => {
      const courses = await apiClient.get<typeof MOCK_STAFF_COURSES>("/staff/courses");
      expect(courses).toEqual(MOCK_STAFF_COURSES);

      const concepts = await apiClient.get<{ effective_allowed_concepts: string[] }>("/staff/courses/1/concepts");
      expect(concepts.effective_allowed_concepts.length).toBeGreaterThan(0);
    });

    it("retrieves plain text artifact content via getText", async () => {
      const text = await apiClient.getText("/staff/courses/1/assignments/lab1/artifacts/test_solution");
      expect(text).toContain("def test_invert");
    });

    it("allows updating assignment setup and returns mutated state", async () => {
      const updated = await apiClient.put<{ title: string }>(
        "/staff/courses/1/assignments/lab1/setup",
        { title: "Lab 1 - Modified Title" }
      );
      expect(updated.title).toBe("Lab 1 - Modified Title");

      // Verify persistence in subsequent GET
      const fetched = await apiClient.get<{ title: string }>(
        "/staff/courses/1/assignments/lab1/setup"
      );
      expect(fetched.title).toBe("Lab 1 - Modified Title");
    });

    it("handles mock file download without throwing", async () => {
      const revokeMock = vi.fn();
      const createObjectURLMock = vi.fn().mockReturnValue("blob:mock-url");
      global.URL.createObjectURL = createObjectURLMock;
      global.URL.revokeObjectURL = revokeMock;

      await expect(
        apiClient.download("/staff/courses/1/assignments/lab1/runs/101/export/grades.csv", "grades.csv")
      ).resolves.not.toThrow();

      expect(createObjectURLMock).toHaveBeenCalled();
    });

    it("streams mock AI feedback through onChunk callback without network failure", async () => {
      const chunks: string[] = [];
      const result = await streamSandboxAiFeedback("mock-run-001", "mock-session-123", (chunk) => {
        chunks.push(chunk);
      });

      expect(chunks.length).toBeGreaterThan(0);
      expect(result).toContain("PPM pixel invert");
      expect(chunks.join("")).toBe(result);
    });

    it("handles Grade Now / official runs endpoints without falling through to network", async () => {
      const sectionsRes = await apiClient.get<{ course_id: string; sections: Array<{ id: number; crn: string; is_active: boolean }> }>(
        "/staff/courses/cs1410/sections"
      );
      expect(sectionsRes.course_id).toBe("cs1410");
      expect(sectionsRes.sections.length).toBeGreaterThan(0);
      expect(sectionsRes.sections[0].crn).toBeTruthy();

      const preflightRes = await apiClient.post<{ passed: boolean; errors: string[] }>(
        "/staff/courses/cs1410/assignments/lab1/validate",
        {}
      );
      expect(preflightRes.passed).toBe(true);
      expect(preflightRes.errors).toEqual([]);

      const formData = new FormData();
      const ingestRes = await apiClient.postForm<{ run_id: string; status: string }>(
        "/staff/courses/cs1410/assignments/lab1/submissions/ingest",
        formData
      );
      expect(ingestRes.data.run_id).toBe("101");

      const summaryRes = await apiClient.get<{ id: number; status: string }>(
        "/staff/courses/cs1410/assignments/lab1/runs/101"
      );
      expect(summaryRes.id).toBe(101);
      expect(summaryRes.status).toBe("complete");

      const fileContentRes = await apiClient.get<{ kind: string; content: string }>(
        "/staff/courses/cs1410/assignments/lab1/runs/101/students/1001/files/content?filepath=image_processor.py"
      );
      expect(fileContentRes.kind).toBe("text");
      expect(fileContentRes.content).toContain("def invert_pixels");
    });

    it("fetches CS 1400 and CS 1410 real course assignments in sandbox and staff modes", async () => {
      const cs1400Sandbox = await apiClient.get<typeof MOCK_ASSIGNMENTS_CS1400>("/sandbox/courses/cs1400/assignments");
      expect(cs1400Sandbox.course_id).toBe("cs1400");
      expect(cs1400Sandbox.assignments.length).toBe(44);
      expect(cs1400Sandbox.assignments[0].id).toBe("m1-lab1");

      const cs1400Staff = await apiClient.get<typeof MOCK_ASSIGNMENTS_CS1400>("/staff/courses/cs1400/assignments");
      expect(cs1400Staff.course_id).toBe("cs1400");
      expect(cs1400Staff.assignments.length).toBe(44);

      const cs1410Staff = await apiClient.get<typeof MOCK_ASSIGNMENTS_CS1410>("/staff/courses/cs1410/assignments");
      expect(cs1410Staff.course_id).toBe("cs1410");
      expect(cs1410Staff.assignments.length).toBe(17);
    });

    it("fetches dynamic assignment details across both courses using real catalogs", async () => {
      const cs1400Assignment = await apiClient.get<{ id: string; title: string; description: string }>(
        "/sandbox/courses/cs1400/assignments/m1-lab1"
      );
      expect(cs1400Assignment.id).toBe("m1-lab1");
      expect(cs1400Assignment.title).toBe("Lab 1: Sum of Two Numbers");
      expect(cs1400Assignment.description).toContain("Sum of Two Numbers");

      const cs1410Assignment = await apiClient.get<{ id: string; title: string; description: string }>(
        "/sandbox/courses/cs1410/assignments/ds1"
      );
      expect(cs1410Assignment.id).toBe("ds1");
      expect(cs1410Assignment.title).toBe("Dessert Shop 1: Inheritance Superclass");
      expect(cs1410Assignment.description).toContain("Dessert Shop");
    });

    it("reads and updates staff assignment setup for dynamic assignments", async () => {
      const setup = await apiClient.get<{ course_id: string; assignment_id: string; title: string; base_points: number }>(
        "/staff/courses/cs1400/assignments/m1-lab1/setup"
      );
      expect(setup.course_id).toBe("cs1400");
      expect(setup.assignment_id).toBe("m1-lab1");
      expect(setup.base_points).toBe(100);

      const updated = await apiClient.put<{ base_points: number }>(
        "/staff/courses/cs1400/assignments/m1-lab1/setup",
        { base_points: 150 }
      );
      expect(updated.base_points).toBe(150);

      const refreshed = await apiClient.get<{ base_points: number }>(
        "/staff/courses/cs1400/assignments/m1-lab1/setup"
      );
      expect(refreshed.base_points).toBe(150);
    });

    it("returns course-specific concepts and sections", async () => {
      const cs1400Concepts = await apiClient.get<{ course_id: string; modules: Array<{ id: number; name: string }> }>(
        "/staff/courses/cs1400/concepts"
      );
      expect(cs1400Concepts.course_id).toBe("cs1400");
      expect(cs1400Concepts.modules.length).toBe(14);

      const cs1410Concepts = await apiClient.get<{ course_id: string; modules: Array<{ id: number; name: string }> }>(
        "/staff/courses/cs1410/concepts"
      );
      expect(cs1410Concepts.course_id).toBe("cs1410");
      expect(cs1410Concepts.modules.length).toBe(12);

      const cs1400Sections = await apiClient.get<{ course_id: string; sections: Array<{ crn: string }> }>(
        "/staff/courses/cs1400/sections"
      );
      expect(cs1400Sections.sections).toHaveLength(1);
      expect(cs1400Sections.sections[0].crn).toBe("12345");

      const cs1410Sections = await apiClient.get<{ course_id: string; sections: Array<{ crn: string }> }>(
        "/staff/courses/cs1410/sections"
      );
      expect(cs1410Sections.sections).toHaveLength(2);
    });

    it("handles audit log dashboard endpoints correctly", async () => {
      const logs = await apiClient.get<{ items: unknown[]; total: number }>(
        "/staff/admin/logs?page=1&page_size=10"
      );
      expect(logs.items.length).toBeGreaterThan(0);
      expect(logs.total).toBeGreaterThan(0);

      const stats = await apiClient.get<typeof MOCK_AUDIT_STATS>(
        "/staff/admin/logs/stats"
      );
      expect(stats.total_events).toBe(MOCK_AUDIT_STATS.total_events);
      expect(stats.events_24h).toBe(4);

      const verification = await apiClient.post<typeof MOCK_AUDIT_VERIFICATION>(
        "/staff/admin/logs/verify",
        {}
      );
      expect(verification.compliant).toBe(true);
      expect(verification.records_scanned).toBe(4);
    });

    it("throws 404 ApiError for unimplemented mock routes without wiping stored auth token", async () => {
      localStorage.setItem("token", "mock-jwt-token-lead-staff");
      const fetchSpy = vi.spyOn(global, "fetch");

      await expect(apiClient.get("/staff/nonexistent-endpoint")).rejects.toThrow(
        "Mock endpoint not implemented: GET /staff/nonexistent-endpoint"
      );

      expect(fetchSpy).not.toHaveBeenCalled();
      expect(localStorage.getItem("token")).toBe("mock-jwt-token-lead-staff");
    });
  });
});
