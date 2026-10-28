import { describe, it, expect } from "vitest";
import { contextWindowSchema } from "../../src/shared/utils/validation.js";

describe("Context Window Contract", () => {
  it("validates context window config", () => {
    const config = {
      maxSize: 10,
      includeToolCalls: true,
    };

    const result = contextWindowSchema.safeParse(config);
    expect(result.success).toBe(true);
  });

  it("rejects maxSize above 100", () => {
    const config = {
      maxSize: 101,
      includeToolCalls: true,
    };

    const result = contextWindowSchema.safeParse(config);
    expect(result.success).toBe(false);
  });

  it("rejects maxSize below 0", () => {
    const config = {
      maxSize: -1,
      includeToolCalls: true,
    };

    const result = contextWindowSchema.safeParse(config);
    expect(result.success).toBe(false);
  });

  it("rejects non-boolean includeToolCalls", () => {
    const config = {
      maxSize: 10,
      includeToolCalls: "true",
    };

    const result = contextWindowSchema.safeParse(config);
    expect(result.success).toBe(false);
  });

  it("defaults includeToolCalls to true when omitted", () => {
    const config = {
      maxSize: 10,
    };

    const result = contextWindowSchema.safeParse(config);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.includeToolCalls).toBe(true);
    }
  });
});