import { z } from "zod";
import { ModelsConfigSchema, type ModelsConfig } from "@infrastructure/config/ModelConfig.js";

const envSchema = z.object({
  PORT: z.coerce.number().default(8080),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  MCP_URL: z.string().url().default("http://localhost:8069/ai_chat/mcp"),
  MCP_INTERNAL_KEY: z.string().min(1),
  MCP_TOOLS_CACHE_TTL_MS: z.coerce.number().default(300000),
  MODELS_CONFIG: z.string().optional(),
  LLM_API_KEY: z.string().optional(),
  LLM_BASE_URL: z.string().url().default("https://api.openai.com/v1"),
  LLM_MODEL: z.string().default("gpt-4o-mini"),
  LLM_MAX_TOKENS: z.coerce.number().default(100000),
  LLM_TEMPERATURE: z.coerce.number().default(0.7),
  LLM_TIMEOUT_MS: z.coerce.number().default(45000),
  MCP_CALL_TIMEOUT_MS: z.coerce.number().default(30000),
  MCP_ODOO_USER_ID: z.string().default("1"),
  LOG_LEVEL: z.enum(["trace", "debug", "info", "warn", "error", "fatal"]).default("info"),
  LOG_PRETTY: z.string().optional().transform(v => v === "true").default("true"),
  CONVERSATION_TTL_HOURS: z.coerce.number().default(48),
  CONVERSATION_MAX_MESSAGES: z.coerce.number().default(50000),
  REDIS_HOST: z.string().default("localhost"),
  REDIS_PORT: z.coerce.number().default(6379),
  REDIS_USERNAME: z.string().optional(),
  REDIS_PASSWORD: z.string().optional(),
  REDIS_TLS: z.string().optional().transform(v => v === "true").default("false"),
  REDIS_DB: z.coerce.number().default(0),
  REDIS_CONNECTION_TIMEOUT_MS: z.coerce.number().default(5000),
  REDIS_MAX_RETRIES: z.coerce.number().default(3),
  MAX_CONTEXT_TOKENS: z.coerce.number().default(1000000),
  CONTEXT_WINDOW_SIZE: z.coerce.number().default(100),
});

export type EnvConfig = z.infer<typeof envSchema> & {
  modelsConfig: ModelsConfig;
};

let cachedConfig: EnvConfig | null = null;

export function loadConfig(): EnvConfig {
  if (cachedConfig) {
    return cachedConfig;
  }
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    throw new Error(`Invalid environment configuration: ${result.error.message}`);
  }
  const baseConfig = result.data;
  const modelsConfig = parseModelsConfig(baseConfig);
  cachedConfig = { ...baseConfig, modelsConfig };
  return cachedConfig;
}

function parseModelsConfig(baseConfig: z.infer<typeof envSchema>): ModelsConfig {
  if (baseConfig.MODELS_CONFIG) {
    try {
      const parsed = JSON.parse(baseConfig.MODELS_CONFIG);
      const validated = ModelsConfigSchema.parse(parsed);
      return validated;
    } catch (error) {
      throw new Error(`Invalid MODELS_CONFIG JSON: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  if (baseConfig.LLM_API_KEY) {
    const legacyProvider = {
      id: "legacy",
      baseUrl: baseConfig.LLM_BASE_URL,
      apiKey: baseConfig.LLM_API_KEY,
      defaultCapabilities: {
        streaming: true,
        tools: true,
        contextWindow: baseConfig.MAX_CONTEXT_TOKENS,
      },
      defaultMaxTokens: baseConfig.LLM_MAX_TOKENS,
      defaultTemperature: baseConfig.LLM_TEMPERATURE,
      defaultTimeoutMs: baseConfig.LLM_TIMEOUT_MS,
    };
    const legacyModel = {
      providerId: "legacy",
      modelId: baseConfig.LLM_MODEL,
      displayName: baseConfig.LLM_MODEL,
      capabilities: {
        streaming: true,
        tools: true,
        contextWindow: baseConfig.MAX_CONTEXT_TOKENS,
      },
      isDefault: true,
    };
    return {
      providers: [legacyProvider],
      models: [legacyModel],
    };
  }
  throw new Error("No model configuration found. Set MODELS_CONFIG or LLM_API_KEY.");
}

export function getConfig(): EnvConfig {
  if (!cachedConfig) {
    return loadConfig();
  }
  return cachedConfig;
}