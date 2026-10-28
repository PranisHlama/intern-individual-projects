import type { Request, Response, NextFunction } from "express";
import { createErrorResponse, HTTP_STATUS_BY_ERROR_CODE } from "@shared/types/api.js";

export function createAuthMiddleware() {
  return (req: Request, res: Response, next: NextFunction): void => {
    const apiKey = req.headers["x-api-key"] as string | undefined;
    const userIdHeader = req.headers["x-user-id"] as string | undefined;

    if (!apiKey || apiKey !== process.env.MCP_INTERNAL_KEY) {
      const error = createErrorResponse(
        "Invalid or missing API key",
        "UNAUTHENTICATED",
        undefined,
        getCorrelationId(req)
      );
      res.status(HTTP_STATUS_BY_ERROR_CODE.UNAUTHENTICATED).json(error);
      return;
    }

    if (!userIdHeader) {
      const error = createErrorResponse(
        "Missing X-User-Id header",
        "INVALID_REQUEST",
        undefined,
        getCorrelationId(req)
      );
      res.status(HTTP_STATUS_BY_ERROR_CODE.INVALID_REQUEST).json(error);
      return;
    }

    const userId = parseInt(userIdHeader, 10);
    if (isNaN(userId) || userId <= 0) {
      const error = createErrorResponse(
        "X-User-Id must be a positive integer",
        "INVALID_REQUEST",
        undefined,
        getCorrelationId(req)
      );
      res.status(HTTP_STATUS_BY_ERROR_CODE.INVALID_REQUEST).json(error);
      return;
    }

    (req as Request & { userId: string }).userId = userIdHeader;
    next();
  };
}

export function getUserId(req: Request): string {
  return (req as Request & { userId: string }).userId;
}

export function getCorrelationId(req: Request): string {
  return (req as Request & { correlationId: string }).correlationId;
}