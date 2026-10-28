import { describe, it, expect } from "vitest";
import { countTokens, countMessageTokens, buildTokenWindow } from "../../../src/shared/utils/token-counter.js";

describe("Token Counter", () => {
  describe("countTokens", () => {
    it("counts tokens for simple text", () => {
      const tokens = countTokens("hello world");
      expect(tokens).toBeGreaterThan(0);
      expect(tokens).toBeLessThan(10);
    });

    it("returns 0 for empty string", () => {
      const tokens = countTokens("");
      expect(tokens).toBe(0);
    });

    it("counts tokens for longer text", () => {
      const text = "This is a longer piece of text that should have more tokens than a simple greeting.";
      const tokens = countTokens(text);
      expect(tokens).toBeGreaterThan(10);
    });
  });

  describe("countMessageTokens", () => {
    it("counts tokens for user message", () => {
      const message = {
        role: "user",
        content: "hello world",
        toolCalls: [],
      };
      const tokens = countMessageTokens(message);
      expect(tokens).toBeGreaterThan(0);
    });

    it("counts tokens for assistant message with tool calls", () => {
      const message = {
        role: "assistant",
        content: "Here are the results",
        toolCalls: [
          {
            function: {
              name: "search_knowledge",
              arguments: JSON.stringify({ query: "test", limit: 5 }),
            },
          },
        ],
      };
      const tokens = countMessageTokens(message);
      expect(tokens).toBeGreaterThan(0);
    });

    it("returns base overhead for empty message", () => {
      const message = {
        role: "user",
        content: "",
        toolCalls: [],
      };
      const tokens = countMessageTokens(message);
      expect(tokens).toBeGreaterThanOrEqual(4);
    });
  });

  describe("buildTokenWindow", () => {
    it("returns all messages when under token budget", () => {
      const messages = [
        { role: "user", content: "hi", toolCalls: [] },
        { role: "assistant", content: "hello", toolCalls: [] },
        { role: "user", content: "how are you", toolCalls: [] },
      ];

      const window = buildTokenWindow(messages, 10000, "gpt-4o");
      expect(window.length).toBe(3);
      expect(window[0].content).toBe("hi");
      expect(window[2].content).toBe("how are you");
    });

    it("truncates when over token budget", () => {
      const messages = [
        { role: "user", content: "hi", toolCalls: [] },
        { role: "assistant", content: "hello", toolCalls: [] },
        { role: "user", content: "how are you", toolCalls: [] },
      ];

      const window = buildTokenWindow(messages, 10, "gpt-4o");
      expect(window.length).toBeLessThan(3);
      expect(window.length).toBeGreaterThan(0);
    });

    it("returns empty array for empty input", () => {
      const window = buildTokenWindow([], 1000, "gpt-4o");
      expect(window).toEqual([]);
    });

    it("includes tool calls in token count", () => {
      const messages = [
        { role: "user", content: "search", toolCalls: [] },
        {
          role: "assistant",
          content: "results",
          toolCalls: [
            {
              function: {
                name: "search_knowledge",
                arguments: JSON.stringify({ query: "test", limit: 5 }),
              },
            },
          ],
        },
      ];

      const window = buildTokenWindow(messages, 1000, "gpt-4o");
      expect(window.length).toBe(2);
    });

    it("preserves order (most recent last in input, first in output)", () => {
      const messages = [
        { role: "user", content: "first", toolCalls: [] },
        { role: "assistant", content: "second", toolCalls: [] },
        { role: "user", content: "third", toolCalls: [] },
      ];

      const window = buildTokenWindow(messages, 1000, "gpt-4o");
      expect(window[0].content).toBe("first");
      expect(window[2].content).toBe("third");
    });

    it("handles very large single message", () => {
      const messages = [
        { role: "user", content: "x".repeat(100000), toolCalls: [] },
      ];

      const window = buildTokenWindow(messages, 1000, "gpt-4o");
      // Should include at least the most recent message even if it exceeds budget
      expect(window.length).toBe(1);
    });
  });
});