import type { Request, Response } from "express";
import { GetConversationUseCase } from "@application/use-cases/conversation/GetConversationUseCase.js";
import type { Logger } from "@domain/ports/Logger.js";
import { getUserId, getCorrelationId } from "@infrastructure/adapters/primary/http/middlewares/AuthMiddleware.js";
import { CorrelationId } from "@domain/value-objects/CorrelationId.js";

export function createHistoryRoute(getConversationUseCase: GetConversationUseCase, logger: Logger) {
  return async (req: Request, res: Response): Promise<void> => {
    const correlationId = CorrelationId.fromString(getCorrelationId(req));
    const userId = getUserId(req);

    try {
      const result = await getConversationUseCase.execute({ userId });
      res.json({ messages: result.messages });
    } catch (error) {
      logger.error("History route error", { correlationId: correlationId.toString(), error: error instanceof Error ? error.message : String(error) });
      res.status(500).json({ error: "Internal server error" });
    }
  };
}