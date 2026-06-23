import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// tests/frontend lives outside this project's root, so bare imports in test files (e.g.
// "@testing-library/react") can't walk up to frontend/node_modules via normal Node resolution.
// Alias the packages those test files import directly back into this root's node_modules.
const TEST_FILE_DEPENDENCIES = ["@testing-library/react", "@testing-library/jest-dom", "react-router-dom", "lucide-react"];

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: Object.fromEntries(
      TEST_FILE_DEPENDENCIES.map((pkg) => [pkg, path.resolve(__dirname, "node_modules", pkg)])
    ),
  },
  server: {
    fs: {
      allow: [path.resolve(__dirname, "..")],
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["../tests/frontend/**/*.test.{ts,tsx}"],
    setupFiles: ["../tests/frontend/setup.ts"],
  },
});
