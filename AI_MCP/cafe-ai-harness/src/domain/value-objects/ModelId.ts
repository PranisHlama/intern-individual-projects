export class ModelId {
  private readonly value: string;

  private constructor(value: string) {
    this.value = value;
  }

  static generate(): ModelId {
    return new ModelId(crypto.randomUUID());
  }

  static fromString(value: string): ModelId {
    if (!value || value.trim() === "") {
      throw new Error("ModelId cannot be empty");
    }
    return new ModelId(value.trim());
  }

  toString(): string {
    return this.value;
  }

  equals(other: ModelId): boolean {
    return this.value === other.value;
  }
}