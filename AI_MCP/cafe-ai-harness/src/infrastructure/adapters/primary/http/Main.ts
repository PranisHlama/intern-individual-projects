import { createExpressApp } from "@infrastructure/adapters/primary/http/ExpressAdapter.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import { PinoLoggerAdapter } from "@infrastructure/adapters/secondary/logging/PinoLoggerAdapter.js";
import { UuidCorrelationProviderAdapter } from "@infrastructure/adapters/secondary/correlation/UuidCorrelationProviderAdapter.js";
import { HttpMcpClient } from "@infrastructure/adapters/secondary/mcp/HttpMcpClient.js";
import { McpClientAdapter } from "@infrastructure/adapters/secondary/mcp/McpClientAdapter.js";
import { NvidiaLlmClient } from "@infrastructure/adapters/secondary/llm/NvidiaLlmClient.js";
import { LlmClientAdapter } from "@infrastructure/adapters/secondary/llm/LlmClientAdapter.js";
import { RedisConversationStore } from "@infrastructure/adapters/secondary/storage/RedisConversationStore.js";
import { InMemoryConversationStore } from "@infrastructure/adapters/secondary/storage/InMemoryConversationStore.js";
import { ConversationStoreAdapter } from "@infrastructure/adapters/secondary/storage/ConversationStoreAdapter.js";
import { SendMessageUseCase } from "@application/use-cases/chat/SendMessageUseCase.js";
import { GetConversationUseCase } from "@application/use-cases/conversation/GetConversationUseCase.js";
import { DeleteConversationUseCase } from "@application/use-cases/conversation/DeleteConversationUseCase.js";
import { GetModelsUseCase } from "@application/use-cases/model/GetModelsUseCase.js";
import { SetModelPreferenceUseCase } from "@application/use-cases/model/SetModelPreferenceUseCase.js";
import { GetModelPreferenceUseCase } from "@application/use-cases/model/GetModelPreferenceUseCase.js";

async function main(): Promise<void> {
  const config = getConfig();

  const logger = new PinoLoggerAdapter();
  const correlationProvider = new UuidCorrelationProviderAdapter();

  const httpMcpClient = new HttpMcpClient(logger);
  const mcpClient = new McpClientAdapter(httpMcpClient);

  const nvidiaLlmClient = new NvidiaLlmClient(logger);
  const llmClient = new LlmClientAdapter(nvidiaLlmClient);

  const redisStore = new RedisConversationStore();
  await redisStore.connect();

  const inMemoryStore = new InMemoryConversationStore();
  const conversationStore = new ConversationStoreAdapter(redisStore, inMemoryStore);

  const sendMessageUseCase = new SendMessageUseCase({
    mcpClient,
    llmClient,
    conversationStore,
    logger,
  });

  const getConversationUseCase = new GetConversationUseCase({
    conversationStore,
  });

  const deleteConversationUseCase = new DeleteConversationUseCase({
    conversationStore,
  });

  const getModelsUseCase = new GetModelsUseCase({
    modelRegistry: null as any, // This is just for type compatibility, not actually used in manual wiring
  });

  const setModelPreferenceUseCase = new SetModelPreferenceUseCase({
    modelPreferenceStore: null as any,
  });
  const getModelPreferenceUseCase = new GetModelPreferenceUseCase({
    modelPreferenceStore: null as any,
  });

  const app = createExpressApp({
    sendMessageUseCase,
    getConversationUseCase,
    deleteConversationUseCase,
    getModelsUseCase,
    setModelPreferenceUseCase,
    getModelPreferenceUseCase,
    logger,
    correlationProvider,
  });

  const server = app.listen(config.PORT, () => {
    logger.info("Server started", { port: config.PORT, env: config.NODE_ENV });

    mcpClient.listTools("1").then(
      (tools) => { logger.info("MCP tools discovered", { count: tools.length }); },
      (error) => { logger.error("Failed to discover MCP tools", { error: error instanceof Error ? error.message : String(error) }); }
    );
  });

  async function shutdown(signal: string): Promise<void> {
    logger.info(`Received ${signal}, shutting down`);
    await redisStore.disconnect();
    server.close(() => {
      logger.info("HTTP server closed");
      process.exit(0);
    });

    setTimeout(() => {
      logger.error("Forced shutdown after timeout");
      process.exit(1);
    }, 10000);
  }

  process.on("SIGTERM", () => { shutdown("SIGTERM"); });
  process.on("SIGINT", () => { shutdown("SIGINT"); });
}

main();