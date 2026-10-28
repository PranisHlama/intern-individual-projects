import type { ModelPreferenceStore } from "@domain/ports/ModelPreferenceStore.js";

export interface GetModelPreferenceOutput {
  modelId: string | null;
}

export class GetModelPreferenceUseCase {
  private readonly modelPreferenceStore: ModelPreferenceStore;

  constructor(deps: { modelPreferenceStore: ModelPreferenceStore }) {
    this.modelPreferenceStore = deps.modelPreferenceStore;
  }

  async execute(userId: string): Promise<GetModelPreferenceOutput> {
    if (!userId || userId.trim() === "") {
      throw new Error("userId is required");
    }
    const selection = await this.modelPreferenceStore.get(userId.trim());
    return { modelId: selection?.getModelId() ?? null };
  }
}