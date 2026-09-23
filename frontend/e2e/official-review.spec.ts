import { test, expect } from "@playwright/test";

test.describe("Official Review Acceptance Suite", () => {
  const runPath = "/staff/courses/cs1400/assignments/simple-python-functions/runs/1";

  test.beforeEach(async ({ page }) => {
    // Authenticate as staff member via mock login flow to establish a valid session
    await page.goto("/staff/login");
    const emailInput = page.locator("input#email");
    await emailInput.fill("dev.staff@uvu.edu");
    const submitBtn = page.getByRole("button", { name: "Dev Mock Sign In" });
    await submitBtn.click();
    await expect(page).toHaveURL(/\/staff\/courses/, { timeout: 15000 });

    // Mock API run details on backend port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes("/runs/1/details"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            run_id: 1,
            status: "done",
            requires_manual_grading: true,
            completed_students: 1,
            total_students: 2,
            exports_ready: true,
            students: [
              {
                student_name: "Alice Smith",
                canvas_id: "1001",
                bundle_files: ["student_functions.py"],
                bundle_file_count: 1,
                score: 20,
                max_score: 25,
                status: "success",
                feedback_preview: "Automated tests passed",
                feedback_html: "<p>Automated tests passed</p>",
                manual_results: {
                  code_style: {
                    label: "Code Style & Comments",
                    points: 5,
                    score: null,
                    comments: "",
                  },
                },
                overall_comment: "",
                automated_results: [
                  {
                    key: "add_numbers",
                    label: "add_numbers",
                    outcome: "passed",
                    passed: true,
                    points_awarded: 10,
                    points: 10,
                  },
                  {
                    key: "reverse_words",
                    label: "reverse_words",
                    outcome: "passed",
                    passed: true,
                    points_awarded: 10,
                    points: 10,
                  },
                ],
                automated_score: 20,
                automated_max_score: 20,
              },
              {
                student_name: "Bob Jones",
                canvas_id: "1002",
                bundle_files: ["student_functions.py"],
                bundle_file_count: 1,
                score: 25,
                max_score: 25,
                status: "success",
                feedback_preview: "All tests passed",
                feedback_html: "<p>All tests passed</p>",
                manual_results: {
                  code_style: {
                    label: "Code Style & Comments",
                    points: 5,
                    score: 5,
                    comments: "PEP8 compliant",
                  },
                },
                overall_comment: "Great work",
                automated_results: [
                  {
                    key: "add_numbers",
                    label: "add_numbers",
                    outcome: "passed",
                    passed: true,
                    points_awarded: 10,
                    points: 10,
                  },
                  {
                    key: "reverse_words",
                    label: "reverse_words",
                    outcome: "passed",
                    passed: true,
                    points_awarded: 10,
                    points: 10,
                  },
                ],
                automated_score: 20,
                automated_max_score: 20,
              },
            ],
          }),
        });
      }
    );

    // Mock API run summary strictly on backend port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.endsWith("/runs/1"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            status: "done",
            total_submission_count: 2,
            success_count: 2,
            warning_count: 0,
            failure_count: 0,
            timeout_count: 0,
            created_at: new Date().toISOString(),
            review_expires_at: new Date(Date.now() + 86400000).toISOString(),
            retention_state: "available",
          }),
        });
      }
    );

    // Mock status endpoint on backend port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes("/runs/1/status"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            run_id: "1",
            state: "complete",
            queue_position: null,
            eta_band: null,
            message: null,
          }),
        });
      }
    );

    // Mock student files listing on backend port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes("/runs/1/students/") && url.pathname.endsWith("/files"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            files: [
              {
                filepath: "student_functions.py",
                size_bytes: 120,
                previewable: true,
                preview_kind: "text",
              },
            ],
          }),
        });
      }
    );

    // Mock student file content on backend port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes("/runs/1/students/") && url.pathname.includes("/files/content"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            kind: "text",
            content: "def add_numbers(a, b):\n    return a + b\n\ndef reverse_words(s):\n    return ' '.join(w[::-1] for w in s.split())\n",
          }),
        });
      }
    );
  });

  test("displays official run submissions, student cards, and grade metrics", async ({ page }) => {
    await page.goto(runPath);

    // Verify heading and student names
    await expect(page.getByText("Run #1 Details")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Alice Smith")).toBeVisible();
    await expect(page.getByText("Bob Jones")).toBeVisible();

    // Verify score summaries
    await expect(page.getByText("20 / 25 pts")).toBeVisible();
    await expect(page.getByText("25 / 25 pts")).toBeVisible();
  });

  test("filtering by Needs Grading isolates students with pending manual rubrics", async ({ page }) => {
    await page.goto(runPath);

    await expect(page.getByText("Alice Smith")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Bob Jones")).toBeVisible();

    // Click on Needs Grading filter button
    const needsGradingBtn = page.locator('[data-testid="filter-ungraded"]');
    await expect(needsGradingBtn).toBeVisible();
    await needsGradingBtn.click();

    await expect(page.getByText("Alice Smith")).toBeVisible();
    await expect(page.getByText("Bob Jones")).not.toBeVisible();
  });

  test("inspecting student opens dialog and saves manual grades", async ({ page }) => {
    // Mock save manual grades endpoint on port 8000
    await page.route(
      (url) => url.port === "8000" && url.pathname.includes("/manual-grades"),
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            student_name: "Alice Smith",
            canvas_id: "1001",
            bundle_files: ["student_functions.py"],
            bundle_file_count: 1,
            score: 25,
            max_score: 25,
            status: "success",
            feedback_preview: "All passed",
            feedback_html: "<p>All passed</p>",
            manual_results: {
              code_style: {
                label: "Code Style & Comments",
                points: 5,
                score: 5,
                comments: "Clean implementation",
              },
            },
            overall_comment: "Good job",
            automated_results: [],
            automated_score: 20,
            automated_max_score: 20,
            manual_progress: {
              requires_manual_grading: true,
              completed_students: 2,
              total_students: 2,
              exports_ready: true,
            },
          }),
        });
      }
    );

    await page.goto(runPath);

    // Click on inspect button for Alice Smith
    const inspectBtn = page.locator('[data-testid="inspect-1001"]');
    await expect(inspectBtn).toBeVisible({ timeout: 10000 });
    await inspectBtn.click();

    // Verify inspect dialog is visible
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(page.getByText("Manual Rubric Grading")).toBeVisible();

    // Enter manual score and comment
    const scoreInput = dialog.locator('input[type="number"]');
    await expect(scoreInput).toBeVisible();
    await scoreInput.fill("5");

    const saveBtn = dialog.getByRole("button", { name: "Save", exact: true });
    await expect(saveBtn).toBeVisible();
    await saveBtn.click();
  });

  test("export buttons are available for grades CSV and feedback ZIP", async ({ page }) => {
    await page.goto(runPath);

    const exportCsvBtn = page.getByRole("button", { name: /Export Grades CSV/i });
    await expect(exportCsvBtn).toBeVisible({ timeout: 10000 });

    const exportFeedbackBtn = page.getByRole("button", { name: /Export Feedback ZIP/i });
    await expect(exportFeedbackBtn).toBeVisible();
  });
});
