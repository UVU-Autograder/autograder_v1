import { defineConfig, devices } from "@playwright/test";
import path from "path";
import fs from "fs";

const repoRoot = path.resolve(__dirname, "..");
const isWin = process.platform === "win32";
const pythonVenv = isWin
  ? path.join(repoRoot, "backend", "venv", "Scripts", "python.exe")
  : path.join(repoRoot, "backend", "venv", "bin", "python");
const pythonCmd = fs.existsSync(pythonVenv) ? `"${pythonVenv}"` : (isWin ? "python" : "python3");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `${pythonCmd} -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`,
      cwd: repoRoot,
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30 * 1000,
    },
    {
      command: "npm run dev",
      cwd: __dirname,
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
  ],
});
