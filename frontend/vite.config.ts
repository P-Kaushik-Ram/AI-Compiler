import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    include: ["../tests/frontend/**/*.test.{ts,tsx}"],
    setupFiles: ["../tests/frontend/setup.ts"],
  },
});
