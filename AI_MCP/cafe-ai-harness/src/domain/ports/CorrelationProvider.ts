import { CorrelationId } from "../value-objects/CorrelationId.js";

export interface CorrelationProvider {
  generate(): CorrelationId;
  extract(headers: Record<string, string | undefined>): CorrelationId | null;
}