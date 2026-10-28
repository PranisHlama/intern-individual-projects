import { z } from "zod";

export const chatRequestSchema = z.object({
  message: z.string().min(1).max(50000),
});

export const historyResponseSchema = z.array(
  z.object({
    role: z.enum(["user", "assistant"]),
    content: z.string().min(1).max(50000),
    timestamp: z.string(),
    toolCalls: z
      .array(
        z.object({
          name: z.string(),
          arguments: z.record(z.unknown()),
          result: z.unknown(),
          error: z.string().optional(),
          durationMs: z.number().min(0),
        })
      )
      .optional(),
  })
);

export const newChatResponseSchema = z.object({
  success: z.literal(true),
}).strict();

export const errorResponseSchema = z.object({
  error: z.string(),
  code: z.enum([
    "UNAUTHENTICATED",
    "INVALID_REQUEST",
    "MCP_UNAVAILABLE",
    "LLM_TIMEOUT",
    "LLM_ERROR",
    "TOOL_ERROR",
    "INTERNAL_ERROR",
    "NOT_FOUND",
  ]),
  details: z.record(z.unknown()).optional(),
  correlationId: z.string().uuid(),
});

export const mcpToolSchema = z.object({
  name: z.string(),
  description: z.string(),
  inputSchema: z.object({
    type: z.literal("object"),
    properties: z.record(z.unknown()),
    required: z.array(z.string()).optional(),
    additionalProperties: z.boolean().optional(),
  }),
});

export const mcpToolsListResponseSchema = z.object({
  tools: z.array(mcpToolSchema),
});

export const mcpToolCallRequestSchema = z.object({
  name: z.string(),
  arguments: z.record(z.unknown()),
});

export const mcpToolCallResponseSchema = z.object({
  content: z.array(z.object({ type: z.literal("text"), text: z.string() })),
  isError: z.boolean(),
});

export const chatResponseSchema = z.object({
  reply: z.string(),
  toolCalls: z
    .array(
      z.object({
        name: z.string(),
        arguments: z.record(z.unknown()),
        result: z.unknown(),
        error: z.string().optional(),
        durationMs: z.number().min(0),
      })
    )
    .optional(),
});

export type ChatRequest = z.infer<typeof chatRequestSchema>;
export type ChatResponse = z.infer<typeof chatResponseSchema>;
export type HistoryResponse = z.infer<typeof historyResponseSchema>;
export type NewChatResponse = z.infer<typeof newChatResponseSchema>;
export type ErrorResponse = z.infer<typeof errorResponseSchema>;
export type MCPTool = z.infer<typeof mcpToolSchema>;
export type MCPToolsListResponse = z.infer<typeof mcpToolsListResponseSchema>;
export type MCPToolCallRequest = z.infer<typeof mcpToolCallRequestSchema>;
export type MCPToolCallResponse = z.infer<typeof mcpToolCallResponseSchema>;

export const redisSessionSchema = z.object({
  userId: z.string(),
  messages: z.array(
    z.object({
      role: z.enum(["user", "assistant"]),
      content: z.string().min(1).max(50000),
      timestamp: z.string().datetime(),
      toolCalls: z
        .array(
          z.object({
            name: z.string(),
            arguments: z.record(z.unknown()),
            result: z.unknown(),
            error: z.string().nullable(),
            durationMs: z.number().min(0),
          })
        )
        .optional(),
    })
  ),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const contextWindowSchema = z.object({
  maxSize: z.number().int().min(0).max(100).default(10),
  includeToolCalls: z.boolean().default(true),
});