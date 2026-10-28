import type { MCPClient } from "@domain/ports/MCPClient.js";
import type { Logger } from "@domain/ports/Logger.js";

export interface ExecuteToolInput {
  toolName: string;
  arguments: Record<string, unknown>;
  userId: string;
  correlationId: string;
}

export interface ExecuteToolOutput {
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
  error: string | null;
  durationMs: number;
}

export class ExecuteToolUseCase {
  private readonly mcpClient: MCPClient;
  private readonly logger: Logger;

  constructor(deps: { mcpClient: MCPClient; logger: Logger }) {
    this.mcpClient = deps.mcpClient;
    this.logger = deps.logger;
  }

  async execute(input: ExecuteToolInput): Promise<ExecuteToolOutput> {
    this.logger.debug("Executing MCP tool", { correlationId: input.correlationId, tool: input.toolName });

    const startTime = Date.now();
    try {
      const result = await this.mcpClient.callTool(input.toolName, input.arguments, input.userId);
      const duration = Date.now() - startTime;

      if (result.isError) {
        const errorMsg = result.content[0]?.text ?? "Tool execution failed";
        this.logger.warn("MCP tool returned error", { correlationId: input.correlationId, tool: input.toolName, error: errorMsg });
        return { name: input.toolName, arguments: input.arguments, result: null, error: errorMsg, durationMs: duration };
      }

      this.logger.debug("MCP tool executed successfully", { correlationId: input.correlationId, tool: input.toolName, duration });
      return { name: input.toolName, arguments: input.arguments, result: result.content[0]?.text ?? null, error: null, durationMs: duration };
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      this.logger.error("MCP tool execution failed", { correlationId: input.correlationId, tool: input.toolName, error: errorMsg });
      return { name: input.toolName, arguments: input.arguments, result: null, error: errorMsg, durationMs: duration };
    }
  }
}