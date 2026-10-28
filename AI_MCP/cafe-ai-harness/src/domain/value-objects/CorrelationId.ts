export class CorrelationId {
  private readonly value: string;

  private constructor(value: string) {
    this.value = value;
  }

  static generate(): CorrelationId {
    return new CorrelationId(crypto.randomUUID());
  }

  static fromString(value: string): CorrelationId {
    if (!value || value.trim() === "") {
      throw new Error("CorrelationId cannot be empty");
    }
    const trimmed = value.trim();
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(trimmed)) {
      throw new Error("Invalid CorrelationId format");
    }
    return new CorrelationId(trimmed);
  }

  toString(): string {
    return this.value;
  }

  equals(other: CorrelationId): boolean {
    return this.value === other.value;
  }
}