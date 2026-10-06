import { spawn } from "node:child_process";

process.env.NEXT_PUBLIC_MOCK_API = "false";
const nextProcess = spawn("npx", ["next", "dev", "-H", "127.0.0.1", "--webpack"], {
  stdio: "inherit",
  shell: true,
  env: process.env,
});

nextProcess.on("exit", (code) => {
  process.exit(code ?? 0);
});
