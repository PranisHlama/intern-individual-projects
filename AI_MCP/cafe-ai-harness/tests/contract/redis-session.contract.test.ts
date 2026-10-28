import { describe, it, expect } from "vitest";
import { redisSessionSchema } from "../../src/shared/utils/validation.js";

describe("Redis Session Contract", () => {
  it("validates session with messages", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "hello",
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
        {
          role: "assistant",
          content: "Hello!",
          timestamp: "2026-10-09T17:20:58.682Z",
          toolCalls: [
            {
              name: "search_knowledge",
              arguments: { query: "test", limit: 5 },
              result: { query: "test", result_count: 0, results: [] },
              error: null,
              durationMs: 28,
            },
          ],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(true);
  });

  it("rejects invalid role", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "invalid",
          content: "hello",
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(false);
  });

  it("rejects empty content", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "",
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(false);
  });

  it("rejects content exceeding max length", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "x".repeat(50001),
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(false);
  });

  it("validates tool calls structure", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "assistant",
          content: "Result",
          timestamp: "2026-10-09T17:20:58.682Z",
          toolCalls: [
            {
              name: "get_manufacturing_orders",
              arguments: { limit: 50 },
              result: { orders: [] },
              error: "Access denied",
              durationMs: 27,
            },
          ],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(true);
  });

  it("rejects missing required fields", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "hello",
          timestamp: "2026-10-09T17:20:53.630Z",
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(false);
  });
});