import type { ModelRegistry } from "@domain/ports/ModelRegistry.js";
import type { LLMClient } from "@domain/ports/LLMClient.js";
import { Model } from "@domain/entities/Model.js";
import { getConfig } from "@infrastructure/config/EnvConfig.js";
import { NvidiaLlmClient } from "./NvidiaLlmClient.js";
import { GeminiLlmClient } from "./GeminiLlmClient.js";
import { ModelId } from "@domain/value-objects/ModelId.js";

export class LlmClientRegistry implements ModelRegistry {
  private readonly models: Model[] = [];
  private readonly clients = new Map<string, LLMClient>();
  private defaultModel: Model | null = null;

  constructor(
    private readonly nvidiaClient: NvidiaLlmClient,
    private readonly geminiClient: GeminiLlmClient,
  ) {
    this.initialize();
  }

  private initialize(): void {
    const config = getConfig();
    for (const modelConfig of config.modelsConfig.models) {
      let client: LLMClient;
      switch (modelConfig.providerId) {
        case "nvidia":
          client = this.nvidiaClient;
          break;
        case "gemini":
        case "google":
          client = this.geminiClient;
          break;
        default:
          console.warn(`Unknown provider: ${modelConfig.providerId}, skipping model ${modelConfig.modelId}`);
          continue;
      }

      const providerConfig = config.modelsConfig.providers.find(p => p.id === modelConfig.providerId);
      const capabilities = modelConfig.capabilities ?? providerConfig?.defaultCapabilities ?? {
        streaming: true,
        tools: true,
        contextWindow: 4096,
      };

      const model = Model.create({
        provider: modelConfig.providerId,
        modelId: modelConfig.modelId,
        displayName: modelConfig.displayName,
        capabilities,
        baseUrl: providerConfig?.baseUrl ?? "",
        apiKey: providerConfig?.apiKey ?? "",
        isDefault: modelConfig.isDefault,
      });

      const modelId = ModelId.fromString(modelConfig.modelId).toString();
      this.models.push(model);
      this.clients.set(modelId, client);

      if (modelConfig.isDefault && !this.defaultModel) {
        this.defaultModel = model;
      }
    }

    if (!this.defaultModel && this.models.length > 0) {
      this.defaultModel = this.models[0] ?? null;
    }
  }

  async getAll(): Promise<Model[]> {
    return [...this.models];
  }

  async getById(modelId: string): Promise<Model | null> {
    const normalized = ModelId.fromString(modelId).toString();
    return this.models.find(m => m.getModelId() === normalized) ?? null;
  }

  async getDefault(): Promise<Model | null> {
    return this.defaultModel;
  }

  async getClient(modelId: string): Promise<LLMClient | null> {
    const normalized = ModelId.fromString(modelId).toString();
    return this.clients.get(normalized) ?? null;
  }

  getDefaultClient(): LLMClient {
    if (this.defaultModel) {
      const client = this.clients.get(this.defaultModel.getModelId());
      if (client) return client;
    }
    return this.nvidiaClient;
  }
}