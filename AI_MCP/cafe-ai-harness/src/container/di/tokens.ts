export const TOKENS = {
  // Domain ports
  Logger: "Logger",
  CorrelationProvider: "CorrelationProvider",
  MCPClient: "MCPClient",
  LLMClient: "LLMClient",
  ConversationStore: "ConversationStore",
  ModelRegistry: "ModelRegistry",
  ModelPreferenceStore: "ModelPreferenceStore",

  // Application use cases
  SendMessageUseCase: "SendMessageUseCase",
  GetConversationUseCase: "GetConversationUseCase",
  DeleteConversationUseCase: "DeleteConversationUseCase",
  ExecuteToolUseCase: "ExecuteToolUseCase",
  GetModelsUseCase: "GetModelsUseCase",
  GetModelUseCase: "GetModelUseCase",
  SetModelPreferenceUseCase: "SetModelPreferenceUseCase",
  GetModelPreferenceUseCase: "GetModelPreferenceUseCase",

  // Infrastructure adapters
  HttpMcpClient: "HttpMcpClient",
  McpClientAdapter: "McpClientAdapter",
  NvidiaLlmClient: "NvidiaLlmClient",
  GeminiLlmClient: "GeminiLlmClient",
  LlmClientRegistry: "LlmClientRegistry",
  RedisConversationStore: "RedisConversationStore",
  InMemoryConversationStore: "InMemoryConversationStore",
  ConversationStoreAdapter: "ConversationStoreAdapter",
  RedisModelPreferenceStore: "RedisModelPreferenceStore",
  InMemoryModelPreferenceStore: "InMemoryModelPreferenceStore",
  PinoLoggerAdapter: "PinoLoggerAdapter",
  UuidCorrelationProviderAdapter: "UuidCorrelationProviderAdapter",
  EnvConfig: "EnvConfig",
} as const;

export type Token = keyof typeof TOKENS;

export type ServiceMap = {
  Logger: import("@domain/ports/Logger.js").Logger;
  CorrelationProvider: import("@domain/ports/CorrelationProvider.js").CorrelationProvider;
  MCPClient: import("@domain/ports/MCPClient.js").MCPClient;
  LLMClient: import("@domain/ports/LLMClient.js").LLMClient;
  ConversationStore: import("@domain/ports/ConversationStore.js").ConversationStore;
  ModelRegistry: import("@domain/ports/ModelRegistry.js").ModelRegistry;
  ModelPreferenceStore: import("@domain/ports/ModelPreferenceStore.js").ModelPreferenceStore;
  SendMessageUseCase: import("@application/use-cases/chat/SendMessageUseCase.js").SendMessageUseCase;
  GetConversationUseCase: import("@application/use-cases/conversation/GetConversationUseCase.js").GetConversationUseCase;
  DeleteConversationUseCase: import("@application/use-cases/conversation/DeleteConversationUseCase.js").DeleteConversationUseCase;
  ExecuteToolUseCase: import("@application/use-cases/tool/ExecuteToolUseCase.js").ExecuteToolUseCase;
  GetModelsUseCase: import("@application/use-cases/model/GetModelsUseCase.js").GetModelsUseCase;
  GetModelUseCase: import("@application/use-cases/model/GetModelUseCase.js").GetModelUseCase;
  SetModelPreferenceUseCase: import("@application/use-cases/model/SetModelPreferenceUseCase.js").SetModelPreferenceUseCase;
  GetModelPreferenceUseCase: import("@application/use-cases/model/GetModelPreferenceUseCase.js").GetModelPreferenceUseCase;
  HttpMcpClient: import("@infrastructure/adapters/secondary/mcp/HttpMcpClient.js").HttpMcpClient;
  McpClientAdapter: import("@infrastructure/adapters/secondary/mcp/McpClientAdapter.js").McpClientAdapter;
  NvidiaLlmClient: import("@infrastructure/adapters/secondary/llm/NvidiaLlmClient.js").NvidiaLlmClient;
  GeminiLlmClient: import("@infrastructure/adapters/secondary/llm/GeminiLlmClient.js").GeminiLlmClient;
  LlmClientRegistry: import("@infrastructure/adapters/secondary/llm/LlmClientRegistry.js").LlmClientRegistry;
  RedisConversationStore: import("@infrastructure/adapters/secondary/storage/RedisConversationStore.js").RedisConversationStore;
  InMemoryConversationStore: import("@infrastructure/adapters/secondary/storage/InMemoryConversationStore.js").InMemoryConversationStore;
  ConversationStoreAdapter: import("@infrastructure/adapters/secondary/storage/ConversationStoreAdapter.js").ConversationStoreAdapter;
  RedisModelPreferenceStore: import("@infrastructure/adapters/secondary/storage/RedisModelPreferenceStore.js").RedisModelPreferenceStore;
  InMemoryModelPreferenceStore: import("@infrastructure/adapters/secondary/storage/InMemoryModelPreferenceStore.js").InMemoryModelPreferenceStore;
  PinoLoggerAdapter: import("@infrastructure/adapters/secondary/logging/PinoLoggerAdapter.js").PinoLoggerAdapter;
  UuidCorrelationProviderAdapter: import("@infrastructure/adapters/secondary/correlation/UuidCorrelationProviderAdapter.js").UuidCorrelationProviderAdapter;
  EnvConfig: import("@infrastructure/config/EnvConfig.js").EnvConfig;
};