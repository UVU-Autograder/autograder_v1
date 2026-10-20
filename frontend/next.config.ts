import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, ".."),
  poweredByHeader: false,
  compress: true,
  experimental: {
    optimizePackageImports: ["lucide-react", "radix-ui"],
  },
  webpack: (config, { dev }) => {
    if (dev) {
      const usePolling = process.env.WATCHPACK_POLLING === "true" || process.env.WATCHPACK_POLLING === "1";
      config.watchOptions = {
        ...(usePolling ? { poll: 1000, aggregateTimeout: 300 } : {}),
        ignored: [
          "**/.git/**",
          "**/.venv/**",
          "**/.mypy_cache/**",
          "**/.pytest_cache/**",
          "**/.ruff_cache/**",
          "**/backend/**",
          "**/.next/**",
          "**/node_modules/**",
          "**/public/monaco/**",
        ],
      };
    }
    return config;
  },
};

export default nextConfig;
