import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    pool: "threads",
    setupFiles: [],
    exclude: ["**/node_modules/**", "**/e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["features/**", "lib/**", "components/**"],
      exclude: [
        "**/__tests__/**",
        "**/*.d.ts",
        "**/mock-data.ts",
        "**/mock-handlers.ts",
      ],
    },
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
