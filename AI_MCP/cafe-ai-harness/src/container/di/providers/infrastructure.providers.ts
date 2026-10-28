import { container } from "@container/di/Container.js";
import { TOKENS } from "@container/di/tokens.js";
import { HttpMcpClient } from "@infrastructure/adapters/secondary/mcp/HttpMcpClient.js";
import { McpClientAdapter } from "@infrastructure/adapters/secondary/mcp/McpClientAdapter.js";
import { NvidiaLlmClient } from "@infrastructure/adapters/secondary/llm/NvidiaLlmClient.js";
import { GeminiLlmClient } from "@infrastructure/adapters/secondary/llm/GeminiLlmClient.js";
import { LlmClientRegistry } from "@infrastructure/adapters/secondary/llm/LlmClientRegistry.js";
import { RedisConversationStore } from "@infrastructure/adapters/secondary/storage/RedisConversationStore.js";
import { InMemoryConversationStore } from "@infrastructure/adapters/secondary/storage/InMemoryConversationStore.js";
import { ConversationStoreAdapter } from "@infrastructure/adapters/secondary/storage/ConversationStoreAdapter.js";
import { RedisModelPreferenceStore } from "@infrastructure/adapters/secondary/storage/RedisModelPreferenceStore.js";
import { InMemoryModelPreferenceStore } from "@infrastructure/adapters/secondary/storage/InMemoryModelPreferenceStore.js";
import { PinoLoggerAdapter } from "@infrastructure/adapters/secondary/logging/PinoLoggerAdapter.js";
import { UuidCorrelationProviderAdapter } from "@infrastructure/adapters/secondary/correlation/UuidCorrelationProviderAdapter.js";

export function registerInfrastructureProviders(): void {
  container.registerSingleton(TOKENS.Logger, new PinoLoggerAdapter());
  container.registerSingleton(TOKENS.CorrelationProvider, new UuidCorrelationProviderAdapter());

  container.registerSingleton(TOKENS.HttpMcpClient, new HttpMcpClient(container.resolve(TOKENS.Logger)));
  container.registerFactory(TOKENS.MCPClient, () => new McpClientAdapter(container.resolve(TOKENS.HttpMcpClient)));

  container.registerSingleton(TOKENS.NvidiaLlmClient, new NvidiaLlmClient(container.resolve(TOKENS.Logger)));
  container.registerSingleton(TOKENS.GeminiLlmClient, new GeminiLlmClient(container.resolve(TOKENS.Logger)));
  container.registerSingleton(TOKENS.LlmClientRegistry, new LlmClientRegistry(
    container.resolve(TOKENS.NvidiaLlmClient),
    container.resolve(TOKENS.GeminiLlmClient),
  ));
  container.registerFactory(TOKENS.ModelRegistry, () => container.resolve(TOKENS.LlmClientRegistry));
  container.registerFactory(TOKENS.LLMClient, () => container.resolve(TOKENS.LlmClientRegistry).getDefaultClient());

  container.registerSingleton(TOKENS.RedisConversationStore, new RedisConversationStore(
    container.resolve(TOKENS.ModelRegistry)
  ));
  container.registerSingleton(TOKENS.InMemoryConversationStore, new InMemoryConversationStore());
  container.registerFactory(TOKENS.ConversationStore, () => new ConversationStoreAdapter(
    container.resolve(TOKENS.RedisConversationStore),
    container.resolve(TOKENS.InMemoryConversationStore)
  ));

  container.registerSingleton(TOKENS.RedisModelPreferenceStore, new RedisModelPreferenceStore());
  container.registerSingleton(TOKENS.InMemoryModelPreferenceStore, new InMemoryModelPreferenceStore());
  container.registerFactory(TOKENS.ModelPreferenceStore, () => container.resolve(TOKENS.RedisModelPreferenceStore));
}