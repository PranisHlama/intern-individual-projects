import { describe, it, expect, beforeEach, vi } from "vitest";
import { InMemoryConversationStore } from "@infrastructure/adapters/secondary/storage/InMemoryConversationStore.js";
import { Conversation } from "@domain/entities/Conversation.js";
import { Message } from "@domain/entities/Message.js";

const testModelsConfig = JSON.stringify({
  providers: [
    { id: "test", baseUrl: "http://test", apiKey: "test" }
  ],
  models: [
    { providerId: "test", modelId: "test-model", displayName: "Test Model", capabilities: { streaming: true, tools: true, contextWindow: 4096 }, maxTokens: 1000, temperature: 0.7, timeoutMs: 5000, isDefault: true }
  ]
});

describe("InMemoryConversationStore", () => {
  let store: InMemoryConversationStore;

  beforeEach(() => {
    vi.useFakeTimers();
    process.env.MODELS_CONFIG = testModelsConfig;
    process.env.CONVERSATION_TTL_HOURS = "24";
    process.env.CONVERSATION_MAX_MESSAGES = "100";
    process.env.MAX_CONTEXT_TOKENS = "1000000";
    store = new InMemoryConversationStore();
  });

  afterEach(() => {
    vi.useRealTimers();
    store.stopCleanupInterval();
  });

  it("should return null for non-existent user", async () => {
    const result = await store.get("user-123");
    expect(result).toBeNull();
  });

  it("should store and retrieve conversation", async () => {
    const conversation = Conversation.create("user-123");
    await store.set(conversation);

    const result = await store.get("user-123");
    expect(result).not.toBeNull();
    expect(result?.getUserId()).toBe("user-123");
  });

  it("should delete conversation", async () => {
    const conversation = Conversation.create("user-123");
    await store.set(conversation);

    await store.delete("user-123");
    const result = await store.get("user-123");
    expect(result).toBeNull();
  });

  it("should enforce max message limit", async () => {
    const conversation = Conversation.create("user-123");
    // Manually set message count to exceed limit
    const messages = Array.from({ length: 101 }, (_, i) => Message.createUserMessage(`Message ${i}`));
    // @ts-expect-force - accessing private for test
    conversation["props"].messages = messages;

    await expect(store.set(conversation)).rejects.toThrow("exceeds maximum message count of 100");
  });

  it("should expire conversations after TTL", async () => {
    const conversation = Conversation.create("user-123");
    await store.set(conversation);

    vi.advanceTimersByTime(25 * 60 * 60 * 1000);

    const result = await store.get("user-123");
    expect(result).toBeNull();
  });

  it("should update timestamp on message add", async () => {
    const conversation = Conversation.create("user-123");
    await store.set(conversation);

    const updatedConversation = await store.get("user-123");
    expect(updatedConversation).not.toBeNull();

    const originalUpdatedAt = updatedConversation?.getUpdatedAt();

    vi.advanceTimersByTime(1000);
    updatedConversation?.addMessage(Message.createUserMessage("New message"));
    await store.set(updatedConversation!);

    const result = await store.get("user-123");
    expect(result?.getUpdatedAt().getTime()).toBeGreaterThan(originalUpdatedAt?.getTime() ?? 0);
  });
});