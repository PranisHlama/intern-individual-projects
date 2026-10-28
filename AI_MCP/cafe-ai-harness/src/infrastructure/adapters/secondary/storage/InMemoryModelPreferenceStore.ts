import type { ModelPreferenceStore } from "@domain/ports/ModelPreferenceStore.js";
import type { ModelSelection } from "@domain/entities/ModelSelection.js";

export class InMemoryModelPreferenceStore implements ModelPreferenceStore {
  private readonly store = new Map<string, ModelSelection>();

  async get(userId: string): Promise<ModelSelection | null> {
    return this.store.get(userId) ?? null;
  }

  async set(selection: ModelSelection): Promise<void> {
    this.store.set(selection.getUserId(), selection);
  }

  async delete(userId: string): Promise<void> {
    this.store.delete(userId);
  }
}