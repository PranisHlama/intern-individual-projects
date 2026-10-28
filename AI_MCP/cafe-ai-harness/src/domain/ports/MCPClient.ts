import type { MCPTool } from "../../shared/types/mcp.js";

export type { MCPTool };

export interface MCPClient {
  listTools(userId: string): Promise<MCPTool[]>;
  callTool(name: string, args: Record<string, unknown>, userId: string): Promise<MCPToolCallResult>;
}

export interface MCPToolCallResult {
  content: Array<{ type: "text"; text: string }>;
  isError: boolean;
}