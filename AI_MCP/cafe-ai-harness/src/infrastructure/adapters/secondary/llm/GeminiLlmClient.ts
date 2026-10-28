import type { LLMClient, LLMCompletion, LLMMessage, LLMTool, LLMStreamChunk, LLMToolCall } from "@domain/ports/LLMClient.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import type { Logger } from "@domain/ports/Logger.js";

export class GeminiLlmClient implements LLMClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly maxTokens: number;
  private readonly temperature: number;
  private readonly timeout: number;
  private readonly logger: Logger;

  constructor(logger: Logger) {
    const config = getConfig();
    const geminiProvider = config.modelsConfig.providers.find(p => p.id === "gemini" || p.id === "google");
    if (!geminiProvider) {
      throw new Error("Gemini provider configuration not found");
    }
    this.apiKey = geminiProvider.apiKey;
    this.baseUrl = geminiProvider.baseUrl.replace(/\/$/, "");
    this.maxTokens = geminiProvider.defaultMaxTokens ?? config.LLM_MAX_TOKENS;
    this.temperature = geminiProvider.defaultTemperature ?? config.LLM_TEMPERATURE;
    this.timeout = geminiProvider.defaultTimeoutMs ?? config.LLM_TIMEOUT_MS;
    this.logger = logger;
  }

  private getModelUrl(modelId: string, streaming: boolean): string {
    const action = streaming ? "streamGenerateContent" : "generateContent";
    return `${this.baseUrl}/models/${modelId}:${action}?key=${this.apiKey}`;
  }

  async complete(messages: LLMMessage[], tools: LLMTool[], modelId: string): Promise<LLMCompletion> {
    this.logger.info("LLM request", { provider: "gemini", model: modelId, streaming: false });
    const requestBody = this.buildRequestBody(messages, tools);
    const response = await this.post(requestBody, modelId);
    return this.parseCompletion(response);
  }

  async *stream(messages: LLMMessage[], tools: LLMTool[], modelId: string): AsyncIterable<LLMStreamChunk> {
    this.logger.info("LLM request", { provider: "gemini", model: modelId, streaming: true });
    const requestBody = this.buildRequestBody(messages, tools);
    const response = await this.postStream(requestBody, modelId);

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body for streaming");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const result = await reader.read();
        const { done, value } = result;
        if (done) { break; }

        buffer += decoder.decode(value as Uint8Array, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const chunk = this.parseStreamLine(line);
          if (chunk) {
            yield chunk;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  private cleanSchemaForGemini(schema: unknown): unknown {
    if (typeof schema !== "object" || schema === null) {
      return schema;
    }
    if (Array.isArray(schema)) {
      return schema.map(item => this.cleanSchemaForGemini(item));
    }
    const cleaned: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(schema)) {
      if (key === "additionalProperties") {
        continue;
      }
      cleaned[key] = this.cleanSchemaForGemini(value);
    }
    return cleaned;
  }

  private buildRequestBody(messages: LLMMessage[], tools: LLMTool[]): Record<string, unknown> {
    const systemMessage = messages.find(m => m.role === "system");
    const nonSystemMessages = messages.filter(m => m.role !== "system");

    const geminiTools = tools.length > 0 ? tools.map(t => ({
      function_declarations: [{
        name: t.function.name,
        description: t.function.description,
        parameters: this.cleanSchemaForGemini(t.function.parameters),
      }],
    })) : undefined;

    return {
      contents: nonSystemMessages.map(m => ({
        role: m.role === "assistant" ? "model" : m.role,
        parts: [{ text: m.content }],
      })),
      systemInstruction: systemMessage ? { parts: [{ text: systemMessage.content }] } : undefined,
      tools: geminiTools,
      toolConfig: tools.length > 0 ? { functionCallingConfig: { mode: "AUTO" } } : undefined,
      generationConfig: {
        temperature: this.temperature,
        maxOutputTokens: this.maxTokens,
      },
    };
  }

  private async post(body: Record<string, unknown>, modelId: string): Promise<Record<string, unknown>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => { controller.abort(); }, this.timeout);

    try {
      const response = await fetch(this.getModelUrl(modelId, false), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`LLM API error ${String(response.status)}: ${errorText}`);
      }

      return (await response.json()) as Record<string, unknown>;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(`LLM request timeout after ${String(this.timeout)}ms`);
      }
      throw error;
    }
  }

  private async postStream(body: Record<string, unknown>, modelId: string): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => { controller.abort(); }, this.timeout);

    try {
      const response = await fetch(this.getModelUrl(modelId, true), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`LLM API error ${String(response.status)}: ${errorText}`);
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(`LLM request timeout after ${String(this.timeout)}ms`);
      }
      throw error;
    }
  }

  private parseCompletion(response: Record<string, unknown>): LLMCompletion {
    const candidates = response.candidates as Array<Record<string, unknown>> | undefined;
    if (!candidates || candidates.length === 0) {
      throw new Error("Gemini response has no candidates");
    }

    const candidate = candidates[0]!;
    const content = candidate.content as Record<string, unknown> | undefined;
    if (!content) {
      throw new Error("Gemini response candidate has no content");
    }

    const parts = content.parts as Array<Record<string, unknown>> | undefined;
    if (!parts || parts.length === 0) {
      throw new Error("Gemini response has no parts");
    }

    let textContent = "";
    const toolCalls: LLMToolCall[] = [];

    for (const part of parts) {
      if (part.text) {
        textContent += (part.text as string);
      } else if (part.functionCall) {
        const funcCall = part.functionCall as Record<string, unknown>;
        toolCalls.push({
          id: crypto.randomUUID(),
          type: "function",
          function: {
            name: (funcCall.name as string) || "",
            arguments: JSON.stringify(funcCall.args ?? {}),
          },
        });
      }
    }

    return {
      content: textContent,
      toolCalls,
      usage: response.usageMetadata ? this.parseUsage(response.usageMetadata as Record<string, unknown>) : undefined,
    };
  }

  private parseUsage(usage: Record<string, unknown>): NonNullable<LLMCompletion["usage"]> {
    return {
      promptTokens: (usage.promptTokenCount as number) || 0,
      completionTokens: (usage.candidatesTokenCount as number) || 0,
      totalTokens: (usage.totalTokenCount as number) || 0,
    };
  }

  private parseStreamLine(line: string): LLMStreamChunk | null {
    if (!line.startsWith("data: ")) {
      return null;
    }

    const data = line.slice(6).trim();
    if (data === "[DONE]") {
      return { toolCalls: [], finishReason: "stop" };
    }

    try {
      const parsed = JSON.parse(data) as Record<string, unknown>;
      const candidates = parsed.candidates as Array<Record<string, unknown>> | undefined;
      if (!candidates || candidates.length === 0) {
        return null;
      }

      const candidate = candidates[0]!;
      const content = candidate.content as Record<string, unknown> | undefined;
      if (!content) {
        return null;
      }

      const parts = content.parts as Array<Record<string, unknown>> | undefined;
      if (!parts || parts.length === 0) {
        return null;
      }

      let textContent = "";
      const toolCalls: LLMToolCall[] = [];

      for (const part of parts) {
        if (part.text) {
          textContent += (part.text as string);
        } else if (part.functionCall) {
          const funcCall = part.functionCall as Record<string, unknown>;
          toolCalls.push({
            id: crypto.randomUUID(),
            type: "function",
            function: {
              name: (funcCall.name as string) || "",
              arguments: JSON.stringify(funcCall.args ?? {}),
            },
          });
        }
      }

      return {
        content: textContent,
        toolCalls,
        finishReason: "stop",
      };
    } catch {
      return null;
    }
  }
}