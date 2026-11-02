import { z } from "zod";

export const ModelCapabilitiesSchema = z.object({
  streaming: z.boolean(),
  tools: z.boolean(),
  contextWindow: z.number().positive(),
});

export const ProviderConfigSchema = z.object({
  id: z.string().min(1),
  baseUrl: z.string().url(),
  apiKey: z.string().min(1),
});

export const ModelConfigSchema = z.object({
  providerId: z.string().min(1),
  modelId: z.string().min(1),
  displayName: z.string().min(1),
  capabilities: ModelCapabilitiesSchema,
  maxTokens: z.number().positive(),
  temperature: z.number().min(0).max(2),
  timeoutMs: z.number().positive(),
  isDefault: z.boolean().default(false),
});

export const ModelsConfigSchema = z.object({
  providers: z.array(ProviderConfigSchema).min(1),
  models: z.array(ModelConfigSchema).min(1),
});

export type ModelCapabilities = z.infer<typeof ModelCapabilitiesSchema>;
export type ProviderConfig = z.infer<typeof ProviderConfigSchema>;
export type ModelConfig = z.infer<typeof ModelConfigSchema>;
export type ModelsConfig = z.infer<typeof ModelsConfigSchema>;