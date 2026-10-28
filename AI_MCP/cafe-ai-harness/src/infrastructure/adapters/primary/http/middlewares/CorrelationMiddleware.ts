import type { Request, Response, NextFunction } from "express";
import type { CorrelationProvider } from "@domain/ports/CorrelationProvider.js";
import { CorrelationId } from "@domain/value-objects/CorrelationId.js";

export function createCorrelationMiddleware(correlationProvider: CorrelationProvider) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const headerId = req.headers["x-correlation-id"] as string | undefined;
    const correlationId = headerId
      ? CorrelationId.fromString(headerId)
      : correlationProvider.generate();

    (req as Request & { correlationId: string }).correlationId = correlationId.toString();
    res.setHeader("X-Correlation-ID", correlationId.toString());
    next();
  };
}