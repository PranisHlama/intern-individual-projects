import { vi } from "vitest";

vi.stubEnv("MCP_INTERNAL_KEY", "test-mcp-key");
vi.stubEnv("MCP_URL", "http://localhost:8069/ai_chat/mcp");
vi.stubEnv("LLM_API_KEY", "test-llm-key");
vi.stubEnv("LLM_BASE_URL", "https://api.test.com/v1");
vi.stubEnv("LLM_MODEL", "test-model");
vi.stubEnv("LOG_LEVEL", "debug");
vi.stubEnv("LOG_PRETTY", "false");
vi.stubEnv("NODE_ENV", "test");
vi.stubEnv("CONVERSATION_TTL_HOURS", "24");
vi.stubEnv("CONVERSATION_MAX_MESSAGES", "100");
vi.stubEnv("MCP_TOOLS_CACHE_TTL_MS", "300000");
vi.stubEnv("LLM_MAX_TOKENS", "4096");
vi.stubEnv("LLM_TEMPERATURE", "0.7");
vi.stubEnv("LLM_TIMEOUT_MS", "30000");
vi.stubEnv("MCP_CALL_TIMEOUT_MS", "10000");
vi.stubEnv("PORT", "8080");