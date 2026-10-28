export type ChatRequest = {
  message: string;
};

export type ChatResponse = {
  reply: string;
  toolCalls?: Array<{
    name: string;
    arguments: Record<string, unknown>;
    result: unknown;
    error?: string;
    durationMs: number;
  }>;
};

export type HistoryResponse = Array<{
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  toolCalls?: Array<{
    name: string;
    arguments: Record<string, unknown>;
    result: unknown;
    error?: string;
    durationMs: number;
  }>;
}>;

export type NewChatResponse = {
  success: true;
};

export type ErrorResponse = {
  error: string;
  code: "UNAUTHENTICATED" | "INVALID_REQUEST" | "MCP_UNAVAILABLE" | "LLM_TIMEOUT" | "LLM_ERROR" | "TOOL_ERROR" | "INTERNAL_ERROR" | "NOT_FOUND";
  details?: Record<string, unknown> | undefined;
  correlationId: string;
};

export const HTTP_STATUS_BY_ERROR_CODE = {
  UNAUTHENTICATED: 401,
  INVALID_REQUEST: 400,
  MCP_UNAVAILABLE: 503,
  LLM_TIMEOUT: 504,
  LLM_ERROR: 502,
  TOOL_ERROR: 500,
  INTERNAL_ERROR: 500,
  NOT_FOUND: 404,
} as const;

export function createErrorResponse(
  error: string,
  code: keyof typeof HTTP_STATUS_BY_ERROR_CODE,
  details: Record<string, unknown> | undefined,
  correlationId: string
): ErrorResponse {
  return { error, code, details, correlationId };
}