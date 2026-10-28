import type { Request, Response } from "express";
import { DeleteConversationUseCase } from "@application/use-cases/conversation/DeleteConversationUseCase.js";
import type { Logger } from "@domain/ports/Logger.js";
import { getUserId, getCorrelationId } from "@infrastructure/adapters/primary/http/middlewares/AuthMiddleware.js";
import { CorrelationId } from "@domain/value-objects/CorrelationId.js";

export function createNewChatRoute(deleteConversationUseCase: DeleteConversationUseCase, logger: Logger) {
  return async (req: Request, res: Response): Promise<void> => {
    const correlationId = CorrelationId.fromString(getCorrelationId(req));
    const userId = getUserId(req);

    try {
      const result = await deleteConversationUseCase.execute({ userId });
      res.json({ success: result.success });
    } catch (error) {
      logger.error("New chat route error", { correlationId: correlationId.toString(), error: error instanceof Error ? error.message : String(error) });
      res.status(500).json({ error: "Internal server error" });
    }
  };
}