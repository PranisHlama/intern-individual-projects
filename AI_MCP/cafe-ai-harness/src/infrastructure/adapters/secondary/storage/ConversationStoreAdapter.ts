import type { ConversationStore } from "@domain/ports/ConversationStore.js";
import type { Conversation } from "@domain/entities/Conversation.js";
import type { Message } from "@domain/entities/Message.js";
import { RedisConversationStore } from "./RedisConversationStore.js";
import { InMemoryConversationStore } from "./InMemoryConversationStore.js";

export class ConversationStoreAdapter implements ConversationStore {
  private readonly redisStore: RedisConversationStore;
  private readonly inMemoryStore: InMemoryConversationStore;
  private useRedis: boolean = true;

  constructor(redisStore: RedisConversationStore, inMemoryStore: InMemoryConversationStore) {
    this.redisStore = redisStore;
    this.inMemoryStore = inMemoryStore;
  }

  setUseRedis(useRedis: boolean): void {
    this.useRedis = useRedis;
  }

  private getStore(): ConversationStore {
    return this.useRedis ? this.redisStore : this.inMemoryStore;
  }

  async get(userId: string): Promise<Conversation | null> {
    return this.getStore().get(userId);
  }

  async set(conversation: Conversation): Promise<void> {
    return this.getStore().set(conversation);
  }

  async delete(userId: string): Promise<void> {
    return this.getStore().delete(userId);
  }

  async getContextWindow(userId: string): Promise<Message[]> {
    return this.getStore().getContextWindow(userId);
  }
}