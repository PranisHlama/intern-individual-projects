import { describe, it, expect } from "vitest";
import { newChatResponseSchema } from "../../src/shared/utils/validation.js";

describe("New Chat Response Contract", () => {
  it("validates successful new chat response", () => {
    const response = { success: true };
    const result = newChatResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
  });

  it("rejects response without success field", () => {
    const response = {};
    const result = newChatResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });

  it("rejects response with success: false", () => {
    const response = { success: false };
    const result = newChatResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });

  it("rejects response with extra fields", () => {
    const response = { success: true, extra: "field" };
    const result = newChatResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });

  it("rejects response with non-boolean success", () => {
    const response = { success: "true" };
    const result = newChatResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });
});