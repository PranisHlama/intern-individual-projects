export interface ModelSelectionProps {
  userId: string;
  modelId: string;
  updatedAt: Date;
}

export class ModelSelection {
  private readonly id: string;
  private props: ModelSelectionProps;

  private constructor(props: ModelSelectionProps, id?: string) {
    this.id = id ?? crypto.randomUUID();
    this.props = props;
  }

  static create(userId: string, modelId: string): ModelSelection {
    if (!userId || userId.trim() === "") {
      throw new Error("userId is required and cannot be empty");
    }
    if (!modelId || modelId.trim() === "") {
      throw new Error("modelId is required and cannot be empty");
    }
    const now = new Date();
    return new ModelSelection(
      {
        userId: userId.trim(),
        modelId: modelId.trim(),
        updatedAt: now,
      },
      crypto.randomUUID()
    );
  }

  static reconstitute(props: ModelSelectionProps & { id: string }): ModelSelection {
    return new ModelSelection(
      {
        userId: props.userId,
        modelId: props.modelId,
        updatedAt: props.updatedAt,
      },
      props.id
    );
  }

  getId(): string {
    return this.id;
  }

  getUserId(): string {
    return this.props.userId;
  }

  getModelId(): string {
    return this.props.modelId;
  }

  getUpdatedAt(): Date {
    return this.props.updatedAt;
  }

  updateModelId(modelId: string): void {
    if (!modelId || modelId.trim() === "") {
      throw new Error("modelId is required and cannot be empty");
    }
    this.props.modelId = modelId.trim();
    this.props.updatedAt = new Date();
  }

  toSnapshot(): ModelSelectionProps & { id: string } {
    return {
      id: this.id,
      userId: this.props.userId,
      modelId: this.props.modelId,
      updatedAt: this.props.updatedAt,
    };
  }
}