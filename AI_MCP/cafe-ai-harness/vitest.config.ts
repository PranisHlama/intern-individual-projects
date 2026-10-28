import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
  resolve: {
    alias: {
      "@domain": path.resolve(__dirname, "src/domain"),
      "@application": path.resolve(__dirname, "src/application"),
      "@infrastructure": path.resolve(__dirname, "src/infrastructure"),
      "@container": path.resolve(__dirname, "src/container"),
      "@shared": path.resolve(__dirname, "src/shared"),
    },
  },
});