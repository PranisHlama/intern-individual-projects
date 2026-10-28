import type { Request, Response, NextFunction } from "express";
import type { Logger } from "@domain/ports/Logger.js";

export function createLoggingMiddleware(logger: Logger) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const start = Date.now();
    const correlationId = (req as Request & { correlationId: string }).correlationId;

    logger.info("Request received", {
      correlationId,
      method: req.method,
      path: req.path,
      userId: (req as Request & { userId?: string }).userId,
    });

    res.on("finish", () => {
      const duration = Date.now() - start;
      logger.info("Response sent", {
        correlationId,
        method: req.method,
        path: req.path,
        statusCode: res.statusCode,
        durationMs: duration,
      });
    });

    next();
  };
}