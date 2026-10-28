import { getConfig } from "@infrastructure/config/EnvConfig.js";
import type { Logger } from "@domain/ports/Logger.js";
import { MCP_PROTOCOL_VERSION } from "@shared/types/mcp.js";

export class HttpMcpClient {
  private readonly logger: Logger;
  private toolsCache: MCPTool[] | null = null;
  private cacheTimestamp: number = 0;
  private readonly cacheTtl: number;

  constructor(logger: Logger) {
    const config = getConfig();
    this.logger = logger;
    this.cacheTtl = config.MCP_TOOLS_CACHE_TTL_MS;
  }

  async listTools(userId: string): Promise<MCPTool[]> {
    const now = Date.now();
    if (this.toolsCache && now - this.cacheTimestamp < this.cacheTtl) {
      this.logger.debug("Returning cached MCP tools", { toolCount: this.toolsCache.length });
      return this.toolsCache;
    }

    this.logger.info("Fetching MCP tools from server", { userId });
    await this.initialize(userId);
    const tools = await this.fetchTools(userId);
    this.toolsCache = tools;
    this.cacheTimestamp = now;
    this.logger.info("MCP tools cached", { toolCount: tools.length, userId });
    return tools;
  }

  async callTool(name: string, args: Record<string, unknown>, userId: string): Promise<MCPToolCallResult> {
    this.logger.debug("Calling MCP tool", { tool: name, userId });

    const request = {
      jsonrpc: "2.0" as const,
      id: crypto.randomUUID(),
      method: "tools/call",
      params: { name, arguments: args },
    };

    const response = await this.post<MCPToolCallResult>(request, userId);

    if (response.error) {
      this.logger.warn("MCP tool call returned error", {
        tool: name,
        userId,
        code: response.error.code,
        message: response.error.message,
      });
      return {
        content: [{ type: "text", text: response.error.message }],
        isError: true,
      };
    }

    if (!response.result) {
      throw new Error("MCP tool call returned no result");
    }

    return response.result;
  }

  private async initialize(userId: string): Promise<void> {
    const initParams = {
      protocolVersion: "2025-11-25",
      capabilities: {},
      clientInfo: {
        name: "cafe-ai-harness",
        version: "1.0.0",
      },
    };

    const request = {
      jsonrpc: "2.0" as const,
      id: crypto.randomUUID(),
      method: "initialize",
      params: initParams,
    };

    const response = await this.post(request, userId);

    if (response.error) {
      throw new Error(`MCP initialization failed: ${response.error.message}`);
    }

    const initializedRequest = {
      jsonrpc: "2.0" as const,
      id: crypto.randomUUID(),
      method: "notifications/initialized",
      params: {},
    };

    await this.post(initializedRequest, userId);
  }

  private async fetchTools(userId: string): Promise<MCPTool[]> {
    const request = {
      jsonrpc: "2.0" as const,
      id: crypto.randomUUID(),
      method: "tools/list",
    };

    const response = await this.post<{ tools: MCPTool[] }>(request, userId);

    if (response.error) {
      throw new Error(`MCP tools/list failed: ${response.error.message}`);
    }

    if (!response.result) {
      throw new Error("MCP tools/list returned no result");
    }

    return response.result.tools;
  }

  private async post<T>(request: { jsonrpc: string; id: string; method: string; params?: unknown }, userId: string): Promise<{ jsonrpc: string; id: string; result: T | undefined; error?: { code: number; message: string } }> {
    const config = getConfig();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => { controller.abort(); }, config.MCP_CALL_TIMEOUT_MS);

    try {
      const response = await fetch(config.MCP_URL.replace(/\/$/, ""), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-MCP-Internal-Key": config.MCP_INTERNAL_KEY,
          "X-Odoo-User-Id": userId,
          "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`MCP server returned ${String(response.status)}: ${response.statusText}`);
      }

      const text = await response.text();
      if (!text) {
        return { jsonrpc: "2.0", id: "", result: undefined };
      }

      return JSON.parse(text);
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(`MCP request timeout after ${String(config.MCP_CALL_TIMEOUT_MS)}ms`);
      }
      throw error;
    }
  }

  invalidateCache(): void {
    this.toolsCache = null;
    this.cacheTimestamp = 0;
  }
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
    additionalProperties?: boolean;
  };
}

export interface MCPToolCallResult {
  content: Array<{ type: "text"; text: string }>;
  isError: boolean;
}
