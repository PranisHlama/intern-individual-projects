import type { ModelSelection } from "../entities/ModelSelection.js";

export interface ModelPreferenceStore {
  get(userId: string): Promise<ModelSelection | null>;
  set(selection: ModelSelection): Promise<void>;
  delete(userId: string): Promise<void>;
}