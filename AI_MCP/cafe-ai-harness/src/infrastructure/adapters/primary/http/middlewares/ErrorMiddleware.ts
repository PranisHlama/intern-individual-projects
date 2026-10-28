import type { Request, Response, NextFunction } from "express";
import type { Logger } from "@domain/ports/Logger.js";
import { createErrorResponse, HTTP_STATUS_BY_ERROR_CODE } from "@shared/types/api.js";

export function createErrorMiddleware(logger: Logger) {
  return (err: Error, req: Request, res: Response, _next: NextFunction): void => {
    const correlationId = (req as Request & { correlationId: string }).correlationId;

    logger.error("Unhandled error", {
      correlationId,
      error: err.message,
      stack: err.stack,
    });

    const error = createErrorResponse(
      "Internal server error",
      "INTERNAL_ERROR",
      undefined,
      correlationId
    );

    res.status(HTTP_STATUS_BY_ERROR_CODE.INTERNAL_ERROR).json(error);
  };
}

export function createNotFoundMiddleware(logger: Logger) {
  return (req: Request, res: Response): void => {
    const correlationId = (req as Request & { correlationId: string }).correlationId;

    logger.warn("Route not found", { correlationId, method: req.method, path: req.path });

    const error = createErrorResponse(
      "Not found",
      "NOT_FOUND",
      undefined,
      correlationId
    );

    res.status(HTTP_STATUS_BY_ERROR_CODE.NOT_FOUND).json(error);
  };
}