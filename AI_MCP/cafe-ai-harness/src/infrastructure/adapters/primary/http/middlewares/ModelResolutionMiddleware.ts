import type { Request, Response, NextFunction } from "express";
import { container } from "@container/di/Container.js";
import { TOKENS } from "@container/di/tokens.js";
import type { LLMClient } from "@domain/ports/LLMClient.js";

declare global {
  namespace Express {
    interface Request {
      resolvedModel?: { model: unknown; client: LLMClient };
    }
  }
}

export async function modelResolutionMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const modelId = req.body?.modelId as string | undefined;

  try {
    const modelRegistry = container.resolve(TOKENS.ModelRegistry);

    let model;
    let client;

    if (modelId) {
      model = await modelRegistry.getById(modelId);
      if (!model) {
        res.status(400).json({ error: `Model not found: ${modelId}` });
        return;
      }
      client = await modelRegistry.getClient(modelId);
    } else {
      model = await modelRegistry.getDefault();
      if (!model) {
        res.status(500).json({ error: "No default model configured" });
        return;
      }
      client = await modelRegistry.getClient(model.getModelId());
    }

    if (!client) {
      res.status(500).json({ error: "No client available for model" });
      return;
    }

    req.resolvedModel = { model, client };
    next();
  } catch (error) {
    res.status(500).json({ error: "Model resolution failed" });
  }
}