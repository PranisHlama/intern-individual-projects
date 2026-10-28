import { NvidiaLlmClient } from "./NvidiaLlmClient.js";
import type { LLMClient } from "@domain/ports/LLMClient.js";

export class LlmClientAdapter implements LLMClient {
  private readonly nvidiaLlmClient: NvidiaLlmClient;

  constructor(nvidiaLlmClient: NvidiaLlmClient) {
    this.nvidiaLlmClient = nvidiaLlmClient;
  }

  async complete(messages: import("@domain/ports/LLMClient.js").LLMMessage[], tools: import("@domain/ports/LLMClient.js").LLMTool[], modelId: string): Promise<import("@domain/ports/LLMClient.js").LLMCompletion> {
    return this.nvidiaLlmClient.complete(messages, tools, modelId);
  }

  async *stream(messages: import("@domain/ports/LLMClient.js").LLMMessage[], tools: import("@domain/ports/LLMClient.js").LLMTool[], modelId: string): AsyncIterable<import("@domain/ports/LLMClient.js").LLMStreamChunk> {
    yield* this.nvidiaLlmClient.stream(messages, tools, modelId);
  }
}