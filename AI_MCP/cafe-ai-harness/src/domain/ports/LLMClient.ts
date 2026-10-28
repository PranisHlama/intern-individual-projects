import type { LLMMessage, LLMTool, LLMStreamChunk, LLMToolCall, LLMCompletion } from "../../shared/types/llm.js";

export type { LLMMessage, LLMTool, LLMStreamChunk, LLMToolCall, LLMCompletion };

export interface LLMClient {
  complete(messages: LLMMessage[], tools: LLMTool[], modelId: string): Promise<LLMCompletion>;
  stream(messages: LLMMessage[], tools: LLMTool[], modelId: string): AsyncIterable<LLMStreamChunk>;
}