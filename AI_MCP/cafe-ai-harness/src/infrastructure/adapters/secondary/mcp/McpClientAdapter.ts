import { HttpMcpClient } from "./HttpMcpClient.js";
import type { MCPClient } from "@domain/ports/MCPClient.js";
import type { MCPTool } from "@shared/types/mcp.js";
import type { MCPToolCallResult } from "./HttpMcpClient.js";

export class McpClientAdapter implements MCPClient {
  private readonly httpMcpClient: HttpMcpClient;

  constructor(httpMcpClient: HttpMcpClient) {
    this.httpMcpClient = httpMcpClient;
  }

  async listTools(userId: string): Promise<MCPTool[]> {
    return this.httpMcpClient.listTools(userId);
  }

  async callTool(name: string, args: Record<string, unknown>, userId: string): Promise<MCPToolCallResult> {
    return this.httpMcpClient.callTool(name, args, userId);
  }
}