import { CorrelationId } from "@domain/value-objects/CorrelationId.js";
import type { CorrelationProvider } from "@domain/ports/CorrelationProvider.js";

export class UuidCorrelationProviderAdapter implements CorrelationProvider {
  generate(): CorrelationId {
    return CorrelationId.generate();
  }

  extract(headers: Record<string, string | undefined> | undefined): CorrelationId | null {
    if (!headers) {
      return null;
    }
    const keys = Object.keys(headers);
    const lowerHeaders: Record<string, string | undefined> = {};
    for (const key of keys) {
      lowerHeaders[key.toLowerCase()] = headers[key];
    }
    const headerId = lowerHeaders["x-correlation-id"] ?? lowerHeaders["x-request-id"];
    if (!headerId) {
      return null;
    }
    try {
      return CorrelationId.fromString(headerId);
    } catch {
      return null;
    }
  }
}