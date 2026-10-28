import type { ConversationStore } from "@domain/ports/ConversationStore.js";
import type { Conversation } from "@domain/entities/Conversation.js";
import type { Message } from "@domain/entities/Message.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import { buildTokenWindow } from "@shared/utils/token-counter.js";

export class InMemoryConversationStore implements ConversationStore {
  private readonly store = new Map<string, Conversation>();
  private readonly ttlMs: number;
  private readonly maxMessages: number;
  private readonly maxContextTokens: number;
  private readonly model: string;
  private cleanupInterval: ReturnType<typeof setInterval> | null = null;

  constructor() {
    const config = getConfig();
    this.ttlMs = config.CONVERSATION_TTL_HOURS * 60 * 60 * 1000;
    this.maxMessages = config.CONVERSATION_MAX_MESSAGES;
    this.maxContextTokens = config.MAX_CONTEXT_TOKENS;
    this.model = config.LLM_MODEL;
    this.startCleanupInterval();
  }

  async get(userId: string): Promise<Conversation | null> {
    await Promise.resolve();
    const conversation = this.store.get(userId);
    if (!conversation) {
      return null;
    }
    if (this.isExpired(conversation)) {
      this.store.delete(userId);
      return null;
    }
    return conversation;
  }

  async set(conversation: Conversation): Promise<void> {
    await Promise.resolve();
    if (conversation.getMessageCount() > this.maxMessages) {
      throw new Error(`Conversation exceeds maximum message count of ${String(this.maxMessages)}`);
    }
    this.store.set(conversation.getUserId(), conversation);
  }

  async delete(userId: string): Promise<void> {
    await Promise.resolve();
    this.store.delete(userId);
  }

  async getContextWindow(userId: string, modelId?: string): Promise<Message[]> {
    const conversation = this.store.get(userId);
    if (!conversation) {
      return [];
    }
    if (this.isExpired(conversation)) {
      this.store.delete(userId);
      return [];
    }

    const messages = conversation.getMessages();

    const forTokenCount = messages.map((m) => ({
      role: m.getRole(),
      content: m.getContent(),
      toolCalls: m.getToolCalls().map((tc) => ({
        function: {
          name: tc.getName(),
          arguments: JSON.stringify(tc.getArguments()),
        },
      })),
    }));

    const contextTokens = this.resolveContextTokens(modelId);
    const modelName = this.resolveModelName(modelId);

    const windowMessages = buildTokenWindow(forTokenCount, contextTokens, modelName);

    const windowSet = new Set(windowMessages.map((m) => m.content));
    return messages.filter((m) => windowSet.has(m.getContent()));
  }

  private resolveContextTokens(modelId?: string): number {
    if (!modelId) {
      return this.maxContextTokens;
    }
    return this.maxContextTokens;
  }

  private resolveModelName(modelId?: string): string {
    return modelId ?? this.model;
  }

  private isExpired(conversation: Conversation): boolean {
    return Date.now() - conversation.getUpdatedAt().getTime() > this.ttlMs;
  }

  private startCleanupInterval(): void {
    this.cleanupInterval = setInterval(() => {
      for (const [userId, conversation] of this.store.entries()) {
        if (this.isExpired(conversation)) {
          this.store.delete(userId);
        }
      }
    }, 60 * 60 * 1000);
  }

  stopCleanupInterval(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }
}