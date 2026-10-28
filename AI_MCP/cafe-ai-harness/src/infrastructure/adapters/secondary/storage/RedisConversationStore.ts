import Redis from "ioredis";
import { Conversation } from "@domain/entities/Conversation.js";
import { Message } from "@domain/entities/Message.js";
import type { ConversationStore } from "@domain/ports/ConversationStore.js";
import type { Message as MessageType } from "@domain/entities/Message.js";
import type { ModelRegistry } from "@domain/ports/ModelRegistry.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import { buildTokenWindow } from "@shared/utils/token-counter.js";

const SESSION_KEY_PREFIX = "chat:session:";
const MESSAGES_KEY_SUFFIX = ":messages";

export class RedisConversationStore implements ConversationStore {
  private readonly redis: Redis;
  private readonly ttlSeconds: number;
  private readonly maxMessages: number;
  private readonly maxContextTokens: number;
  private readonly model: string;

  private modelRegistry: ModelRegistry | undefined;

  constructor(modelRegistry?: ModelRegistry) {
    const config = getConfig();
    this.ttlSeconds = config.CONVERSATION_TTL_HOURS * 60 * 60;
    this.maxMessages = config.CONVERSATION_MAX_MESSAGES;
    this.maxContextTokens = config.MAX_CONTEXT_TOKENS;
    this.model = config.LLM_MODEL;
    this.modelRegistry = modelRegistry;

    this.redis = new Redis({
      host: config.REDIS_HOST,
      port: config.REDIS_PORT,
      username: config.REDIS_USERNAME || undefined,
      password: config.REDIS_PASSWORD || undefined,
      tls: config.REDIS_TLS ? {} : undefined,
      db: config.REDIS_DB,
      connectTimeout: config.REDIS_CONNECTION_TIMEOUT_MS,
      maxRetriesPerRequest: config.REDIS_MAX_RETRIES,
      retryStrategy: (times) => {
        if (times > config.REDIS_MAX_RETRIES) {
          return null;
        }
        return Math.min(times * 100, 3000);
      },
      lazyConnect: true,
      family: 4,
    });
  }

  async connect(): Promise<void> {
    await this.redis.connect();
  }

  async disconnect(): Promise<void> {
    await this.redis.quit();
  }

  private getSessionKey(userId: string): string {
    return `${SESSION_KEY_PREFIX}${userId}`;
  }

  private getMessagesKey(userId: string): string {
    return `${this.getSessionKey(userId)}${MESSAGES_KEY_SUFFIX}`;
  }

  async get(userId: string): Promise<Conversation | null> {
    const sessionKey = this.getSessionKey(userId);
    const messagesKey = this.getMessagesKey(userId);

    const exists = await this.redis.exists(sessionKey);
    if (!exists) {
      return null;
    }

    const messageData = await this.redis.lrange(messagesKey, 0, -1);
    if (!messageData.length) {
      return Conversation.create(userId);
    }

    const messages: MessageType[] = messageData
      .map((json) => {
        try {
          const parsed = JSON.parse(json);
          return Message.reconstitute(parsed);
        } catch {
          return null;
        }
      })
      .filter((m): m is MessageType => m !== null);

    const conversation = Conversation.create(userId);
    for (const msg of messages) {
      conversation.addMessage(msg);
    }

    return conversation;
  }

  async set(conversation: Conversation): Promise<void> {
    const userId = conversation.getUserId();
    const sessionKey = this.getSessionKey(userId);
    const messagesKey = this.getMessagesKey(userId);

    const messages = conversation.getMessages();

    if (messages.length > this.maxMessages) {
      throw new Error(
        `Conversation exceeds maximum message count of ${String(this.maxMessages)}`
      );
    }

    const pipeline = this.redis.pipeline();

    pipeline.set(sessionKey, JSON.stringify({
      userId: conversation.getUserId(),
      createdAt: conversation.getCreatedAt().toISOString(),
      updatedAt: conversation.getUpdatedAt().toISOString(),
    }), "EX", this.ttlSeconds);

    pipeline.del(messagesKey);

    if (messages.length > 0) {
      const messageJsons = messages.map((m) => JSON.stringify(m.toSnapshot()));
      pipeline.rpush(messagesKey, ...messageJsons);
      pipeline.expire(messagesKey, this.ttlSeconds);
    }

    await pipeline.exec();
  }

  async delete(userId: string): Promise<void> {
    const sessionKey = this.getSessionKey(userId);
    const messagesKey = this.getMessagesKey(userId);

    await this.redis.del(sessionKey, messagesKey);
  }

  async getContextWindow(userId: string, modelId?: string): Promise<MessageType[]> {
    const messagesKey = this.getMessagesKey(userId);

    const messageData = await this.redis.lrange(messagesKey, 0, -1);

    const messages: MessageType[] = messageData
      .map((json) => {
        try {
          const parsed = JSON.parse(json);
          return Message.reconstitute(parsed);
        } catch {
          return null;
        }
      })
      .filter((m): m is MessageType => m !== null);

    // Convert to format for token counting
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

    // Build token-aware window from most recent backwards
    const contextTokens = await this.resolveContextTokens(modelId);
    const modelName = this.resolveModelName(modelId);
    const windowMessages = buildTokenWindow(forTokenCount, contextTokens, modelName);

    // Map back to Message objects (preserve order)
    const windowSet = new Set(windowMessages.map((m) => m.content));
    return messages.filter((m) => windowSet.has(m.getContent()));
  }

  private async resolveContextTokens(modelId?: string): Promise<number> {
    if (!modelId || !this.modelRegistry) {
      return this.maxContextTokens;
    }
    const model = await this.modelRegistry.getById(modelId);
    if (model) {
      return model.getCapabilities().contextWindow;
    }
    return this.maxContextTokens;
  }

  private resolveModelName(modelId?: string): string {
    return modelId ?? this.model;
  }

  isHealthy(): boolean {
    return this.redis.status === "ready";
  }
}