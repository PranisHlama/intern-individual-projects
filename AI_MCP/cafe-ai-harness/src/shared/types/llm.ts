export type LLMMessage = {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  tool_calls?: Array<{
    id: string;
    type: "function";
    function: {
      name: string;
      arguments: string;
    };
  }>;
  tool_call_id?: string;
};

export type LLMTool = {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: {
      type: "object";
      properties: Record<string, unknown>;
      required?: string[];
      additionalProperties?: boolean;
    };
  };
};

export type LLMToolCall = {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
};

export type LLMCompletion = {
  content: string;
  toolCalls: LLMToolCall[];
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  } | undefined;
};

export type LLMStreamChunk = {
  content?: string;
  toolCalls?: LLMToolCall[];
  finishReason?: "stop" | "length" | "tool_calls" | "content_filter";
};