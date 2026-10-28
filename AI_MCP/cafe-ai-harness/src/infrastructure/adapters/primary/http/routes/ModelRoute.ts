import type { Request, Response } from "express";
import { GetModelsUseCase } from "@application/use-cases/model/GetModelsUseCase.js";
import type { Logger } from "@domain/ports/Logger.js";
import { getCorrelationId } from "@infrastructure/adapters/primary/http/middlewares/AuthMiddleware.js";
import { CorrelationId } from "@domain/value-objects/CorrelationId.js";

export function createModelRoute(getModelsUseCase: GetModelsUseCase, logger: Logger) {
  return async (req: Request, res: Response): Promise<void> => {
    const correlationId = CorrelationId.fromString(getCorrelationId(req));

    try {
      const result = await getModelsUseCase.execute();
      res.json(result);
    } catch (error) {
      logger.error("Model route error", {
        correlationId: correlationId.toString(),
        error: error instanceof Error ? error.message : String(error),
      });
      res.status(500).json({ error: "Internal server error" });
    }
  };
}