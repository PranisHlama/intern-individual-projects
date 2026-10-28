import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { HttpMcpClient } from "@infrastructure/adapters/secondary/mcp/HttpMcpClient.js";
import type { Logger } from "@domain/ports/Logger.js";

vi.mock("@infrastructure/config/EnvConfig.js", () => ({
  getConfig: () => ({
    MCP_URL: "http://test-mcp:8069/ai_chat/mcp",
    MCP_INTERNAL_KEY: "test-key",
    MCP_CALL_TIMEOUT_MS: 100,
    MCP_PROTOCOL_VERSION: "2025-11-25",
    MCP_TOOLS_CACHE_TTL_MS: 300000,
    LOG_LEVEL: "debug",
    LOG_PRETTY: "false",
    NODE_ENV: "test",
  }),
}));

const mockLogger: Logger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

describe("HttpMcpClient", () => {
  let client: HttpMcpClient;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock = vi.fn();
    global.fetch = fetchMock;

    client = new HttpMcpClient(mockLogger);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should list tools from cache on second call", async () => {
    const initResponse = {
      jsonrpc: "2.0",
      id: "1",
      result: { protocolVersion: "2025-11-25", capabilities: { tools: { listChanged: false } }, serverInfo: { name: "test", version: "1.0" } },
    };
    const initializedResponse = { jsonrpc: "2.0", method: "notifications/initialized", params: {} };
    const toolsResponse = {
      jsonrpc: "2.0",
      id: "2",
      result: { tools: [{ name: "tool1", description: "Tool 1", inputSchema: { type: "object", properties: {} } }] },
    };

    const createMockResponse = (data: unknown) => ({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(data)),
      json: () => Promise.resolve(data),
    });

    fetchMock
      .mockResolvedValueOnce(createMockResponse(initResponse))
      .mockResolvedValueOnce(createMockResponse(initializedResponse))
      .mockResolvedValueOnce(createMockResponse(toolsResponse));

    const tools1 = await client.listTools();
    expect(tools1).toHaveLength(1);
    expect(tools1[0].name).toBe("tool1");

    // Second call should use cache
    const tools2 = await client.listTools();
    expect(tools2).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("should call tool and return result", async () => {
    const callResponse = {
      jsonrpc: "2.0",
      id: "1",
      result: { content: [{ type: "text", text: "Success" }], isError: false },
    };

    const createMockResponse = (data: unknown) => ({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(data)),
      json: () => Promise.resolve(data),
    });

    fetchMock.mockResolvedValue(createMockResponse(callResponse));

    const result = await client.callTool("test-tool", { arg: "value" });
    expect(result.isError).toBe(false);
    expect(result.content[0].text).toBe("Success");
  });

  it("should handle tool error response", async () => {
    const createMockResponse = (data: unknown) => ({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(data)),
      json: () => Promise.resolve(data),
    });
    fetchMock.mockResolvedValue(createMockResponse({
      jsonrpc: "2.0",
      id: "1",
      result: { content: [{ type: "text", text: "Tool failed" }], isError: true },
    }));

    const result = await client.callTool("failing-tool", {});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe("Tool failed");
  });

  it("should handle MCP protocol error", async () => {
    const createMockResponse = (data: unknown) => ({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(data)),
      json: () => Promise.resolve(data),
    });
    fetchMock.mockResolvedValue(createMockResponse({
      jsonrpc: "2.0",
      id: "1",
      error: { code: -32602, message: "Invalid params" },
    }));

    const result = await client.callTool("test-tool", {});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toBe("Invalid params");
  });

  it("should handle HTTP error", async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 500, statusText: "Internal Server Error" });

    await expect(client.callTool("test-tool", {})).rejects.toThrow("MCP server returned 500: Internal Server Error");
  });

  it("should handle timeout", async () => {
    fetchMock.mockRejectedValue(new DOMException("Aborted", "AbortError"));

    await expect(client.callTool("test-tool", "user1")).rejects.toThrow("MCP request timeout after 100ms");
  });

  it("should invalidate cache", async () => {
    client.invalidateCache();
    expect(client["toolsCache"]).toBeNull();
    expect(client["cacheTimestamp"]).toBe(0);
  });
});