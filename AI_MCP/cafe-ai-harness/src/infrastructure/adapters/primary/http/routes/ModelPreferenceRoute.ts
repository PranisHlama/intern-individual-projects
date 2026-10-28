import type { Request, Response } from "express";
import { SetModelPreferenceUseCase } from "@application/use-cases/model/SetModelPreferenceUseCase.js";
import { GetModelPreferenceUseCase } from "@application/use-cases/model/GetModelPreferenceUseCase.js";
import type { Logger } from "@domain/ports/Logger.js";
import { getUserId, getCorrelationId } from "@infrastructure/adapters/primary/http/middlewares/AuthMiddleware.js";
import { CorrelationId } from "@domain/value-objects/CorrelationId.js";

export function createModelPreferenceRoute(
  setModelPreferenceUseCase: SetModelPreferenceUseCase,
  getModelPreferenceUseCase: GetModelPreferenceUseCase,
  logger: Logger
) {
  return {
    get: async (req: Request, res: Response): Promise<void> => {
      const correlationId = CorrelationId.fromString(getCorrelationId(req));
      const userId = getUserId(req);

      try {
        const result = await getModelPreferenceUseCase.execute(userId);
        res.json(result);
      } catch (error) {
        logger.error("Get model preference route error", {
          correlationId: correlationId.toString(),
          error: error instanceof Error ? error.message : String(error),
        });
        res.status(500).json({ error: "Internal server error" });
      }
    },

    post: async (req: Request, res: Response): Promise<void> => {
      const correlationId = CorrelationId.fromString(getCorrelationId(req));
      const userId = getUserId(req);

      const { modelId } = req.body as { modelId?: string };

      if (!modelId || modelId.trim() === "") {
        res.status(400).json({ error: "modelId is required" });
        return;
      }

      try {
        await setModelPreferenceUseCase.execute(userId, modelId.trim());
        res.json({ success: true });
      } catch (error) {
        logger.error("Set model preference route error", {
          correlationId: correlationId.toString(),
          error: error instanceof Error ? error.message : String(error),
        });
        res.status(500).json({ error: "Internal server error" });
      }
    },
  };
}