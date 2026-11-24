import { test, expect } from "@playwright/test";

test.describe("Sandbox Student Acceptance Suite", () => {
  test("catalog displays available sandbox courses", async ({ page }) => {
    await page.goto("/sandbox");
    await expect(page.getByText("Fundamentals of Programming")).toBeVisible();
    await expect(page.getByText("Object-Oriented Programming")).toBeVisible();
  });

  test("navigating into course displays assignments list", async ({ page }) => {
    await page.goto("/sandbox/cs1400/assignments");
    await expect(page.getByText("Lab 1: Sum of Two Numbers")).toBeVisible();
    await expect(page.getByText(/\d+\s*pts/i).first()).toBeVisible();
  });

  test("assignment workspace loads rubric, constraints, and test runner", async ({ page }) => {
    await page.goto("/sandbox/cs1400/assignments/m1-lab1");

    // Verify back navigation link
    await expect(page.getByRole("link", { name: "Back to assignments" })).toBeVisible({ timeout: 10000 });

    // Verify files sidebar controls
    await expect(page.getByText("Files", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "New" })).toBeVisible();

    // Verify code runner controls
    const runBtn = page.getByRole("button", { name: "Run Code" });
    await expect(runBtn).toBeVisible();
    await expect(page.getByText("sum_two_numbers.py", { exact: true }).first()).toBeVisible();
  });

  test("executing sandbox run displays test results and rubric scoring", async ({ page }) => {
    const mockRunId = "sbx-test-run-12345";

    // Intercept backend run submission strictly on port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes("/runs") && !url.pathname.includes("/status") && !url.pathname.includes("/result"),
      async (route) => {
        if (route.request().method() === "POST") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            headers: {
              "X-Sandbox-Session": "mock-sbx-session-uuid",
            },
            body: JSON.stringify({
              run_id: mockRunId,
              sandbox_session: "mock-sbx-session-uuid",
              status_url: `/sandbox/runs/${mockRunId}/status`,
              result_url: `/sandbox/runs/${mockRunId}/result`,
              upload_quota: {
                limit: 999999,
                window_seconds: 3600,
                remaining: 999998,
                reset_at: "2026-09-24T00:00:00Z",
              },
              initial_status: {
                run_id: mockRunId,
                state: "complete",
                queue_position: null,
                eta_band: null,
                message: null,
              },
            }),
          });
          return;
        }
        await route.continue();
      }
    );

    // Intercept status polling on port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes(`/sandbox/runs/${mockRunId}/status`),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            run_id: mockRunId,
            state: "complete",
            queue_position: null,
            eta_band: null,
            message: null,
          }),
        });
      }
    );

    // Intercept backend result fetching on port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes(`/sandbox/runs/${mockRunId}/result`),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            run_id: mockRunId,
            state: "complete",
            projected_score: 25,
            max_score: 25,
            completion_objectives: [
              { key: "core", label: "Pass one core test", passed_count: 1, minimum_passed: 1, met: true },
            ],
            warnings: [],
            test_summaries: [
              {
                label: "add_numbers(a, b) calculates sum",
                status: "passed",
                points_awarded: 5,
                points_possible: 5,
                message: "Passed",
              },
              {
                label: "reverse_words(sentence) reverses characters",
                status: "passed",
                points_awarded: 10,
                points_possible: 10,
                message: "Passed",
              },
              {
                label: "count_vowels(text) counts vowels",
                status: "passed",
                points_awarded: 10,
                points_possible: 10,
                message: "Passed",
              },
            ],
            rubric_groups: [],
          }),
        });
      }
    );

    await page.goto("/sandbox/cs1400/assignments/m1-lab1");

    const runBtn = page.getByRole("button", { name: "Run Code" });
    await expect(runBtn).toBeVisible({ timeout: 10000 });
    await page.locator("#workspace-file-upload-input").setInputFiles({
      name: "sum_two_numbers.py",
      mimeType: "text/x-python",
      buffer: Buffer.from("print(1 + 2)\n"),
    });
    // Load the synthetic catalog first, then route grading through the HTTP fixtures.
    await page.evaluate(() => window.sessionStorage.setItem("mock_api", "false"));
    await runBtn.click();

    await expect(page.getByText("25 / 25", { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Pass one core test · Met/)).toBeVisible();
  });
});
