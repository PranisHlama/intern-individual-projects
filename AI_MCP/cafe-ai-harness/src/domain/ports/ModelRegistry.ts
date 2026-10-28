import type { Model } from "../entities/Model.js";
import type { LLMClient } from "./LLMClient.js";

export interface ModelRegistry {
  getAll(): Promise<Model[]>;
  getById(modelId: string): Promise<Model | null>;
  getDefault(): Promise<Model | null>;
  getClient(modelId: string): Promise<LLMClient | null>;
}