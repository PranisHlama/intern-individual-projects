export interface ModelCapabilities {
  streaming: boolean;
  tools: boolean;
  contextWindow: number;
}

export interface ModelProps {
  provider: string;
  modelId: string;
  displayName: string;
  capabilities: ModelCapabilities;
  baseUrl: string;
  apiKey: string;
  isDefault: boolean;
}

export class Model {
  private readonly id: string;
  private props: ModelProps;

  private constructor(props: ModelProps, id?: string) {
    this.id = id ?? crypto.randomUUID();
    this.props = props;
  }

  static create(props: ModelProps): Model {
    if (!props.provider || props.provider.trim() === "") {
      throw new Error("provider is required and cannot be empty");
    }
    if (!props.modelId || props.modelId.trim() === "") {
      throw new Error("modelId is required and cannot be empty");
    }
    if (!props.displayName || props.displayName.trim() === "") {
      throw new Error("displayName is required and cannot be empty");
    }
    if (!props.baseUrl || props.baseUrl.trim() === "") {
      throw new Error("baseUrl is required and cannot be empty");
    }
    if (!props.apiKey || props.apiKey.trim() === "") {
      throw new Error("apiKey is required and cannot be empty");
    }
    if (!props.capabilities) {
      throw new Error("capabilities is required");
    }
    if (typeof props.capabilities.streaming !== "boolean") {
      throw new Error("capabilities.streaming must be boolean");
    }
    if (typeof props.capabilities.tools !== "boolean") {
      throw new Error("capabilities.tools must be boolean");
    }
    if (typeof props.capabilities.contextWindow !== "number" || props.capabilities.contextWindow <= 0) {
      throw new Error("capabilities.contextWindow must be positive number");
    }

    return new Model({
      provider: props.provider.trim(),
      modelId: props.modelId.trim(),
      displayName: props.displayName.trim(),
      capabilities: props.capabilities,
      baseUrl: props.baseUrl.trim(),
      apiKey: props.apiKey.trim(),
      isDefault: props.isDefault ?? false,
    });
  }

  static reconstitute(props: ModelProps & { id: string }): Model {
    return new Model(
      {
        provider: props.provider,
        modelId: props.modelId,
        displayName: props.displayName,
        capabilities: props.capabilities,
        baseUrl: props.baseUrl,
        apiKey: props.apiKey,
        isDefault: props.isDefault,
      },
      props.id
    );
  }

  getId(): string {
    return this.id;
  }

  getProvider(): string {
    return this.props.provider;
  }

  getModelId(): string {
    return this.props.modelId;
  }

  getDisplayName(): string {
    return this.props.displayName;
  }

  getCapabilities(): ModelCapabilities {
    return { ...this.props.capabilities };
  }

  getBaseUrl(): string {
    return this.props.baseUrl;
  }

  getApiKey(): string {
    return this.props.apiKey;
  }

  isDefault(): boolean {
    return this.props.isDefault;
  }

  toSnapshot(): ModelProps & { id: string } {
    return {
      id: this.id,
      provider: this.props.provider,
      modelId: this.props.modelId,
      displayName: this.props.displayName,
      capabilities: { ...this.props.capabilities },
      baseUrl: this.props.baseUrl,
      apiKey: this.props.apiKey,
      isDefault: this.props.isDefault,
    };
  }

  toPublicSnapshot(): Omit<ModelProps & { id: string }, "apiKey"> {
    return {
      id: this.id,
      provider: this.props.provider,
      modelId: this.props.modelId,
      displayName: this.props.displayName,
      capabilities: { ...this.props.capabilities },
      baseUrl: this.props.baseUrl,
      isDefault: this.props.isDefault,
    };
  }
}