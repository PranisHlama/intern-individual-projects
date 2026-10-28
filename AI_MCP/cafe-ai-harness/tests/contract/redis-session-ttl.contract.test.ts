import { describe, it, expect } from "vitest";
import { redisSessionSchema } from "../../src/shared/utils/validation.js";

describe("Redis Session TTL Contract", () => {
  it("validates session with createdAt and updatedAt timestamps", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "hello",
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(true);
  });

  it("validates session with empty messages array", () => {
    const session = {
      userId: "1",
      messages: [],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(true);
  });

  it("rejects invalid datetime format for createdAt", () => {
    const session = {
      userId: "1",
      messages: [],
      createdAt: "invalid-date",
      updatedAt: "2026-10-09T17:20:58.682Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(false);
  });

  it("rejects invalid datetime format for updatedAt", () => {
    const session = {
      userId: "1",
      messages: [],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "not-a-date",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(false);
  });

  it("validates session with multiple messages and TTL refresh", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "first message",
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
        {
          role: "assistant",
          content: "response",
          timestamp: "2026-10-09T17:20:58.682Z",
          toolCalls: [],
        },
        {
          role: "user",
          content: "second message",
          timestamp: "2026-10-09T17:25:10.123Z",
          toolCalls: [],
        },
      ],
      createdAt: "2026-10-09T17:20:53.614Z",
      updatedAt: "2026-10-09T17:25:10.123Z",
    };

    const result = redisSessionSchema.safeParse(session);
    expect(result.success).toBe(true);
  });

  it("validates session with tool calls having error", () => {
    const session = {
      userId: "1",
      messages: [
        {
          role: "user",
          content: "list orders",
          timestamp: "2026-10-09T17:20:53.630Z",
          toolCalls: [],
        },
        {
          role: "assistant",
          content: "Error occurred",
          timestamp: "2026-10-09T17:20:58.682Z",
          toolCalls: [
            {
              name: "get_manufacturing_orders",
              arguments: { limit: 50 },
              result: null,
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
});