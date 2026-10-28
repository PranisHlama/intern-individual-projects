import { describe, it, expect } from "vitest";
import { UuidCorrelationProviderAdapter } from "@infrastructure/adapters/secondary/correlation/UuidCorrelationProviderAdapter.js";

describe("UuidCorrelationProviderAdapter", () => {
  let provider: UuidCorrelationProviderAdapter;

  beforeEach(() => {
    provider = new UuidCorrelationProviderAdapter();
  });

  it("should generate valid UUID v4", () => {
    const id1 = provider.generate();
    const id2 = provider.generate();

    expect(id1.toString()).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
    expect(id1.toString()).not.toBe(id2.toString());
  });

  it("should extract correlation ID from x-correlation-id header", () => {
    const headers = { "x-correlation-id": "550e8400-e29b-41d4-a716-446655440000" };
    const result = provider.extract(headers);
    expect(result?.toString()).toBe("550e8400-e29b-41d4-a716-446655440000");
  });

  it("should extract correlation ID from x-request-id header", () => {
    const headers = { "x-request-id": "550e8400-e29b-41d4-a716-446655440000" };
    const result = provider.extract(headers);
    expect(result?.toString()).toBe("550e8400-e29b-41d4-a716-446655440000");
  });

  it("should prefer x-correlation-id over x-request-id", () => {
    const headers = {
      "x-correlation-id": "550e8400-e29b-41d4-a716-446655440000",
      "x-request-id": "660e8400-e29b-41d4-a716-446655440000",
    };
    const result = provider.extract(headers);
    expect(result?.toString()).toBe("550e8400-e29b-41d4-a716-446655440000");
  });

  it("should return null for invalid UUID", () => {
    const headers = { "x-correlation-id": "not-a-uuid" };
    const result = provider.extract(headers);
    expect(result).toBeNull();
  });

  it("should return null when no header present", () => {
    const result = provider.extract({});
    expect(result).toBeNull();
  });

  it("should return null for undefined headers", () => {
    const result = provider.extract(undefined as unknown as Record<string, string | undefined>);
    expect(result).toBeNull();
  });
});