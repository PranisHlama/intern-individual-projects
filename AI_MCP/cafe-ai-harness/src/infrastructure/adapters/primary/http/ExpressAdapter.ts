import express, { type Express, type Request, type Response, type NextFunction } from "express";
import { createCorrelationMiddleware } from "@infrastructure/adapters/primary/http/middlewares/CorrelationMiddleware.js";
import { createAuthMiddleware } from "@infrastructure/adapters/primary/http/middlewares/AuthMiddleware.js";
import { createLoggingMiddleware } from "@infrastructure/adapters/primary/http/middlewares/LoggingMiddleware.js";
import { createErrorMiddleware, createNotFoundMiddleware } from "@infrastructure/adapters/primary/http/middlewares/ErrorMiddleware.js";
import { modelResolutionMiddleware } from "@infrastructure/adapters/primary/http/middlewares/ModelResolutionMiddleware.js";
import { createChatRoute } from "@infrastructure/adapters/primary/http/routes/ChatRoute.js";
import { createHistoryRoute } from "@infrastructure/adapters/primary/http/routes/HistoryRoute.js";
import { createNewChatRoute } from "@infrastructure/adapters/primary/http/routes/NewChatRoute.js";
import { createModelRoute } from "@infrastructure/adapters/primary/http/routes/ModelRoute.js";
import { createModelPreferenceRoute } from "@infrastructure/adapters/primary/http/routes/ModelPreferenceRoute.js";
import { SendMessageUseCase } from "@application/use-cases/chat/SendMessageUseCase.js";
import { GetConversationUseCase } from "@application/use-cases/conversation/GetConversationUseCase.js";
import { DeleteConversationUseCase } from "@application/use-cases/conversation/DeleteConversationUseCase.js";
import { GetModelsUseCase } from "@application/use-cases/model/GetModelsUseCase.js";
import { SetModelPreferenceUseCase } from "@application/use-cases/model/SetModelPreferenceUseCase.js";
import { GetModelPreferenceUseCase } from "@application/use-cases/model/GetModelPreferenceUseCase.js";
import type { Logger } from "@domain/ports/Logger.js";
import type { CorrelationProvider } from "@domain/ports/CorrelationProvider.js";

function asyncHandler(fn: (req: Request, res: Response, next: NextFunction) => Promise<void>) {
  return (req: Request, res: Response, next: NextFunction): void => {
    Promise.resolve(fn(req, res, next)).catch((err: unknown) => { next(err); });
  };
}

export function createExpressApp(deps: {
  sendMessageUseCase: SendMessageUseCase;
  getConversationUseCase: GetConversationUseCase;
  deleteConversationUseCase: DeleteConversationUseCase;
  getModelsUseCase: GetModelsUseCase;
  setModelPreferenceUseCase: SetModelPreferenceUseCase;
  getModelPreferenceUseCase: GetModelPreferenceUseCase;
  logger: Logger;
  correlationProvider: CorrelationProvider;
}): Express {
  const app = express();
  app.use(express.json({ limit: "1mb" }));

  const correlationMiddleware = createCorrelationMiddleware(deps.correlationProvider);
  const authMiddleware = createAuthMiddleware();
  const loggingMiddleware = createLoggingMiddleware(deps.logger);
  const errorMiddleware = createErrorMiddleware(deps.logger);
  const notFoundMiddleware = createNotFoundMiddleware(deps.logger);

  app.use(correlationMiddleware);
  app.use(loggingMiddleware);
  app.use(authMiddleware);

  app.get("/health", (_req: Request, res: Response) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  app.post("/v1/chat", modelResolutionMiddleware, asyncHandler(createChatRoute(deps.sendMessageUseCase, deps.logger)));
  app.get("/v1/chat/current", asyncHandler(createHistoryRoute(deps.getConversationUseCase, deps.logger)));
  app.delete("/v1/chat/current", asyncHandler(createNewChatRoute(deps.deleteConversationUseCase, deps.logger)));
  app.get("/v1/models", asyncHandler(createModelRoute(deps.getModelsUseCase, deps.logger)));

  const modelPreferenceRoute = createModelPreferenceRoute(deps.setModelPreferenceUseCase, deps.getModelPreferenceUseCase, deps.logger);
  app.get("/v1/model/preference", asyncHandler(modelPreferenceRoute.get));
  app.post("/v1/model/preference", asyncHandler(modelPreferenceRoute.post));

  app.use(notFoundMiddleware);
  app.use(errorMiddleware);

  return app;
}