import type { ModelRegistry } from "@domain/ports/ModelRegistry.js";

export interface GetModelOutput {
  model: {
    id: string;
    provider: string;
    modelId: string;
    displayName: string;
    capabilities: {
      streaming: boolean;
      tools: boolean;
      contextWindow: number;
    };
    isDefault: boolean;
  } | null;
}

export class GetModelUseCase {
  private readonly modelRegistry: ModelRegistry;

  constructor(deps: { modelRegistry: ModelRegistry }) {
    this.modelRegistry = deps.modelRegistry;
  }

  async execute(modelId: string): Promise<GetModelOutput> {
    const model = await this.modelRegistry.getById(modelId);
    if (!model) {
      return { model: null };
    }
    return {
      model: {
        id: model.getId(),
        provider: model.getProvider(),
        modelId: model.getModelId(),
        displayName: model.getDisplayName(),
        capabilities: model.getCapabilities(),
        isDefault: model.isDefault(),
      },
    };
  }
}