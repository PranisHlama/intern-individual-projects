import type { ModelRegistry } from "@domain/ports/ModelRegistry.js";

export interface GetModelsOutput {
  models: Array<{
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
  }>;
}

export class GetModelsUseCase {
  private readonly modelRegistry: ModelRegistry;

  constructor(deps: { modelRegistry: ModelRegistry }) {
    this.modelRegistry = deps.modelRegistry;
  }

  async execute(): Promise<GetModelsOutput> {
    const models = await this.modelRegistry.getAll();
    return {
      models: models.map((model) => ({
        id: model.getId(),
        provider: model.getProvider(),
        modelId: model.getModelId(),
        displayName: model.getDisplayName(),
        capabilities: model.getCapabilities(),
        isDefault: model.isDefault(),
      })),
    };
  }
}