import type { LLMClient, LLMCompletion, LLMMessage, LLMTool, LLMStreamChunk, LLMToolCall } from "@domain/ports/LLMClient.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import type { Logger } from "@domain/ports/Logger.js";

export class NvidiaLlmClient implements LLMClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly maxTokens: number;
  private readonly temperature: number;
  private readonly timeout: number;
  private readonly logger: Logger;

  constructor(logger: Logger) {
    const config = getConfig();
    const nvidiaProvider = config.modelsConfig.providers.find(p => p.id === "nvidia");
    if (!nvidiaProvider) {
      throw new Error("NVIDIA provider configuration not found");
    }
    this.apiKey = nvidiaProvider.apiKey;
    this.baseUrl = nvidiaProvider.baseUrl.replace(/\/$/, "");
    this.maxTokens = nvidiaProvider.defaultMaxTokens ?? config.LLM_MAX_TOKENS;
    this.temperature = nvidiaProvider.defaultTemperature ?? config.LLM_TEMPERATURE;
    this.timeout = nvidiaProvider.defaultTimeoutMs ?? config.LLM_TIMEOUT_MS;
    this.logger = logger;
  }

  async complete(messages: LLMMessage[], tools: LLMTool[], modelId: string): Promise<LLMCompletion> {
    this.logger.info("LLM request", { provider: "nvidia", model: modelId, streaming: false });
    const requestBody = this.buildRequestBody(messages, tools, modelId, false);
    const response = await this.post(requestBody);
    return this.parseCompletion(response);
  }

  async *stream(messages: LLMMessage[], tools: LLMTool[], modelId: string): AsyncIterable<LLMStreamChunk> {
    this.logger.info("LLM request", { provider: "nvidia", model: modelId, streaming: true });
    const requestBody = this.buildRequestBody(messages, tools, modelId, true);
    const response = await this.postStream(requestBody);

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

  private buildRequestBody(messages: LLMMessage[], tools: LLMTool[], modelId: string, stream: boolean): Record<string, unknown> {
    return {
      model: modelId,
      messages,
      tools: tools.length > 0 ? tools : undefined,
      tool_choice: tools.length > 0 ? "auto" : undefined,
      temperature: this.temperature,
      max_tokens: this.maxTokens,
      stream,
    };
  }

  private async post(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => { controller.abort(); }, this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
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

  private async postStream(body: Record<string, unknown>): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => { controller.abort(); }, this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
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
    const choices = response.choices as Array<Record<string, unknown>> | undefined;
    if (!choices || choices.length === 0) {
      throw new Error("LLM response has no choices");
    }

    const choice = choices[0];
    if (!choice) {
      throw new Error("LLM response choice is undefined");
    }
    const message = choice.message as Record<string, unknown> | undefined;
    if (!message) {
      throw new Error("LLM response choice has no message");
    }

    const content = (message.content as string) || "";
    const toolCalls = (message.tool_calls as Array<Record<string, unknown>>) || [];

    return {
      content,
      toolCalls: toolCalls.map((tc) => this.parseToolCall(tc)),
      usage: response.usage ? this.parseUsage(response.usage as Record<string, unknown>) : undefined,
    };
  }

  private parseUsage(usage: Record<string, unknown>): NonNullable<LLMCompletion["usage"]> {
    return {
      promptTokens: (usage.prompt_tokens as number) || 0,
      completionTokens: (usage.completion_tokens as number) || 0,
      totalTokens: (usage.total_tokens as number) || 0,
    };
  }

  private parseToolCall(tc: Record<string, unknown>): LLMToolCall {
    const func = tc.function as Record<string, unknown> | undefined;
    return {
      id: (tc.id as string) || crypto.randomUUID(),
      type: "function",
      function: {
        name: (func?.name as string) || "",
        arguments: (func?.arguments as string) || "{}",
      },
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
      const choices = parsed.choices as Array<Record<string, unknown>> | undefined;
      if (!choices || choices.length === 0) {
        return null;
      }

      const choice = choices[0];
      if (!choice) {
        return null;
      }
      const delta = choice.delta as Record<string, unknown> | undefined;
      const finishReason = choice.finish_reason as LLMStreamChunk["finishReason"] | undefined;

      if (!delta) {
        return { toolCalls: [], finishReason: finishReason || "stop" };
      }

      const content = delta.content as string | undefined;
      const toolCalls = delta.tool_calls as Array<Record<string, unknown>> | undefined;

      return {
        content: content || "",
        toolCalls: toolCalls ? toolCalls.map((tc) => this.parseToolCall(tc)) : [],
        finishReason: finishReason || "stop",
      };
    } catch {
      return null;
    }
  }
}