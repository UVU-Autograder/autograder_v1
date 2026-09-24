import { test, expect } from "@playwright/test";

test.describe("Staff Authentication Acceptance Suite", () => {
  test("unauthenticated visitor to /staff/courses is redirected to /staff/login", async ({ page }) => {
    await page.goto("/staff/courses");
    await expect(page).toHaveURL(/\/staff\/login/);
    await expect(page.getByText("Staff Portal Sign In")).toBeVisible();
  });

  test("session expiration timeout display shows informational warning", async ({ page }) => {
    await page.goto("/staff/login?reason=timeout");
    await expect(page.getByText("Your session has expired. Please sign in again.")).toBeVisible();
  });

  test("enforces UVU institutional email domain check", async ({ page }) => {
    await page.goto("/staff/login");

    const emailInput = page.locator("input#email");
    await emailInput.fill("external.guest@gmail.com");

    const submitBtn = page.getByRole("button", { name: "Dev Mock Sign In" });
    await submitBtn.click();

    await expect(page.getByText("Only @uvu.edu email addresses are allowed.")).toBeVisible();
  });

  test("successful mock login stores session and navigates to staff portal", async ({ page }) => {
    await page.goto("/staff/login");
    const emailInput = page.locator("input#email");
    await emailInput.fill("dev.staff@uvu.edu");

    const submitBtn = page.getByRole("button", { name: "Dev Mock Sign In" });
    await submitBtn.click();

    await expect(page).toHaveURL(/\/staff\/courses/, { timeout: 15000 });

    const token = await page.evaluate(() => localStorage.getItem("token"));
    expect(token).toBeTruthy();
    expect(typeof token).toBe("string");
  });

  test("auth_handoff cookie from Microsoft callback safely provisions session and clears cookie", async ({ context, page }) => {
    // Intercept backend calls on port 8000 so the session is not invalidated by 401
    await page.route(
      (url) => url.port === "8000",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([]),
        });
      }
    );

    const handoffData = {
      token: "entra-id-secure-jwt",
      email: "faculty@uvu.edu",
      displayName: "Faculty Member",
      roles: ["instructor"],
    };

    await context.addCookies([
      {
        name: "auth_handoff",
        value: encodeURIComponent(JSON.stringify(handoffData)),
        url: "http://127.0.0.1:3000",
      },
    ]);

    await page.goto("/staff/login");

    await expect(page).toHaveURL(/\/staff\/courses/, { timeout: 15000 });

    const token = await page.evaluate(() => localStorage.getItem("token"));
    expect(token).toBe("entra-id-secure-jwt");

    const cookies = await context.cookies();
    const handoffCookie = cookies.find((c) => c.name === "auth_handoff");
    expect(handoffCookie).toBeUndefined();
  });
});
