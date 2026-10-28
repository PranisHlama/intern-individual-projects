import type { Request, Response } from "express";
import { SendMessageUseCase } from "@application/use-cases/chat/SendMessageUseCase.js";
import type { Logger } from "@domain/ports/Logger.js";
import type { LLMClient } from "@domain/ports/LLMClient.js";
import { getUserId, getCorrelationId } from "@infrastructure/adapters/primary/http/middlewares/AuthMiddleware.js";
import { CorrelationId } from "@domain/value-objects/CorrelationId.js";

export function createChatRoute(sendMessageUseCase: SendMessageUseCase, logger: Logger) {
  return async (req: Request, res: Response): Promise<void> => {
    const correlationId = CorrelationId.fromString(getCorrelationId(req));
    const userId = getUserId(req);

    const { message } = req.body as { message: string; modelId?: string };

    if (!message || message.trim() === "") {
      res.status(400).json({ error: "Message is required" });
      return;
    }

    const resolvedModel = (req as Request & { resolvedModel?: { model: unknown; client: LLMClient } }).resolvedModel;
    const resolvedLlmClient = resolvedModel?.client;
    const resolvedModelId = resolvedModel?.model ? (resolvedModel.model as { getModelId: () => string }).getModelId() : undefined;

    const input = {
      userId,
      message: message.trim(),
      correlationId,
      ...(resolvedModelId ? { modelId: resolvedModelId } : {}),
      ...(resolvedLlmClient ? { llmClient: resolvedLlmClient } : {}),
    };

    try {
      const result = await sendMessageUseCase.execute(input as typeof input & { modelId?: string; llmClient?: LLMClient });
      res.json({ reply: result.reply, toolCalls: result.toolCalls });
    } catch (error) {
      logger.error("Chat route error", { correlationId: correlationId.toString(), error: error instanceof Error ? error.message : String(error) });
      res.status(500).json({ error: "Internal server error" });
    }
  };
}