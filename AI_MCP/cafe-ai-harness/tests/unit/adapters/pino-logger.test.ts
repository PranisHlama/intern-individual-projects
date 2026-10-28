import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { PinoLoggerAdapter } from "@infrastructure/adapters/secondary/logging/PinoLoggerAdapter.js";

let logger: PinoLoggerAdapter;

describe("PinoLoggerAdapter", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    process.env.LOG_LEVEL = "debug";
    process.env.LOG_PRETTY = "false";
    process.env.NODE_ENV = "test";
    logger = new PinoLoggerAdapter();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should have debug method", () => {
    expect(typeof logger.debug).toBe("function");
  });

  it("should have info method", () => {
    expect(typeof logger.info).toBe("function");
  });

  it("should have warn method", () => {
    expect(typeof logger.warn).toBe("function");
  });

  it("should have error method", () => {
    expect(typeof logger.error).toBe("function");
  });

  it("should implement Logger interface", () => {
    expect(logger).toHaveProperty("debug");
    expect(logger).toHaveProperty("info");
    expect(logger).toHaveProperty("warn");
    expect(logger).toHaveProperty("error");
  });
});