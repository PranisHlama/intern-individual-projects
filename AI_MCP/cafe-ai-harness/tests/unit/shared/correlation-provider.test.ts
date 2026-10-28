import { describe, it, expect } from "vitest";
import { UuidCorrelationProviderAdapter } from "@infrastructure/adapters/secondary/correlation/UuidCorrelationProviderAdapter.js";
import type { CorrelationProvider } from "@domain/ports/CorrelationProvider.js";

describe("CorrelationProvider interface compliance", () => {
  let provider: CorrelationProvider;

  beforeEach(() => {
    provider = new UuidCorrelationProviderAdapter();
  });

  it("should implement generate() method", () => {
    expect(typeof provider.generate).toBe("function");
    const id = provider.generate();
    expect(typeof id.toString()).toBe("string");
    expect(id.toString().length).toBeGreaterThan(0);
  });

  it("should implement extract() method", () => {
    expect(typeof provider.extract).toBe("function");
    const validUuid = "550e8400-e29b-41d4-a716-446655440000";
    const id = provider.extract({ "x-correlation-id": validUuid });
    expect(typeof id?.toString()).toBe("string");
    expect(id?.toString()).toBe(validUuid);
  });

  it("should generate unique IDs on each call", () => {
    const ids = new Set<string>();
    for (let i = 0; i < 100; i++) {
      ids.add(provider.generate().toString());
    }
    expect(ids.size).toBe(100);
  });

  it("should extract from various header casing", () => {
    const validUuid = "550e8400-e29b-41d4-a716-446655440000";
    const headers1 = { "X-Correlation-ID": validUuid };
    const headers2 = { "x-correlation-id": validUuid };
    const headers3 = { "X-CORRELATION-ID": validUuid };

    expect(provider.extract(headers1)?.toString()).toBe(validUuid);
    expect(provider.extract(headers2)?.toString()).toBe(validUuid);
    expect(provider.extract(headers3)?.toString()).toBe(validUuid);
  });

  it("should return null for invalid UUID", () => {
    const id = provider.extract({ "x-correlation-id": "not-a-uuid" });
    expect(id).toBeNull();
  });

  it("should return null when no header present", () => {
    const id = provider.extract({});
    expect(id).toBeNull();
  });

  it("should return null for undefined headers", () => {
    const id = provider.extract(undefined as unknown as Record<string, string | undefined>);
    expect(id).toBeNull();
  });
});