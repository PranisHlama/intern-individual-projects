import { container } from "@container/di/Container.js";
import { registerDomainProviders } from "@container/di/providers/domain.providers.js";
import { registerApplicationProviders } from "@container/di/providers/application.providers.js";
import { registerInfrastructureProviders } from "@container/di/providers/infrastructure.providers.js";
import { TOKENS } from "@container/di/tokens.js";
import { createExpressApp } from "@infrastructure/adapters/primary/http/ExpressAdapter.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";

async function main(): Promise<void> {
  registerDomainProviders();
  registerInfrastructureProviders();
  registerApplicationProviders();

  const config = getConfig();

  const logger = container.resolve(TOKENS.Logger);
  const correlationProvider = container.resolve(TOKENS.CorrelationProvider);
  const redisStore = container.resolve(TOKENS.RedisConversationStore);

  await redisStore.connect();

  const sendMessageUseCase = container.resolve(TOKENS.SendMessageUseCase);
  const getConversationUseCase = container.resolve(TOKENS.GetConversationUseCase);
  const deleteConversationUseCase = container.resolve(TOKENS.DeleteConversationUseCase);
  const getModelsUseCase = container.resolve(TOKENS.GetModelsUseCase);
  const setModelPreferenceUseCase = container.resolve(TOKENS.SetModelPreferenceUseCase);
  const getModelPreferenceUseCase = container.resolve(TOKENS.GetModelPreferenceUseCase);

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