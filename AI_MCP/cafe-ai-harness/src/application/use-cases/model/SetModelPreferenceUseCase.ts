import type { ModelPreferenceStore } from "@domain/ports/ModelPreferenceStore.js";
import { ModelSelection } from "@domain/entities/ModelSelection.js";

export class SetModelPreferenceUseCase {
  private readonly modelPreferenceStore: ModelPreferenceStore;

  constructor(deps: { modelPreferenceStore: ModelPreferenceStore }) {
    this.modelPreferenceStore = deps.modelPreferenceStore;
  }

  async execute(userId: string, modelId: string): Promise<void> {
    if (!userId || userId.trim() === "") {
      throw new Error("userId is required");
    }
    if (!modelId || modelId.trim() === "") {
      throw new Error("modelId is required");
    }
    const selection = ModelSelection.create(userId.trim(), modelId.trim());
    await this.modelPreferenceStore.set(selection);
  }
}