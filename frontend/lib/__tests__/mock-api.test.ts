import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { apiClient, isMockApiEnabled } from "../api-client";
import { streamSandboxAiFeedback } from "../../features/assignments/api";
import {
  MOCK_ASSIGNMENT_DETAILS_LAB1,
  MOCK_ASSIGNMENTS_CS1410,
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
      const result = await apiClient.get<typeof MOCK_ASSIGNMENTS_CS1410>("/sandbox/courses/1/assignments");
      expect(result).toEqual(MOCK_ASSIGNMENTS_CS1410);
    });

    it("fetches single assignment details with full rubric and description", async () => {
      const result = await apiClient.get<typeof MOCK_ASSIGNMENT_DETAILS_LAB1>(
        "/sandbox/courses/1/assignments/lab1"
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
      const loginRes = await apiClient.post<{ access_token: string; roles: string[] }>("/auth/mock-login", {
        email: "dev.staff@uvu.edu",
      });
      expect(loginRes.access_token).toBeTruthy();
      expect(loginRes.roles).toContain("instructor");
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
  });
});
