export type MCPTool = {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
    additionalProperties?: boolean;
  };
};

export type MCPToolsListResponse = {
  tools: MCPTool[];
};

export type MCPToolCallRequest = {
  name: string;
  arguments: Record<string, unknown>;
};

export type MCPToolCallResponse = {
  content: Array<{ type: "text"; text: string }>;
  isError: boolean;
};

export type MCPInitializeParams = {
  protocolVersion: string;
  capabilities: Record<string, unknown>;
  clientInfo: {
    name: string;
    version: string;
  };
};

export type MCPInitializeResult = {
  protocolVersion: string;
  capabilities: Record<string, unknown>;
  serverInfo: {
    name: string;
    version: string;
  };
};

export type MCPToolsListResult = {
  tools: MCPTool[];
};

export type MCPToolCallParams = {
  name: string;
  arguments: Record<string, unknown>;
};

export type MCPToolCallResult = {
  content: Array<{ type: "text"; text: string }>;
  isError: boolean;
};

export type MCPRequest = {
  jsonrpc: "2.0";
  id: string | null;
  method: string;
  params?: unknown;
};

export type MCPResponse<T> = {
  jsonrpc: "2.0";
  id: string | null;
  result?: T;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
};

export const MCP_PROTOCOL_VERSION = "2025-11-25";

export const MCP_METHODS = {
  INITIALIZE: "initialize",
  INITIALIZED: "notifications/initialized",
  TOOLS_LIST: "tools/list",
  TOOLS_CALL: "tools/call",
  PING: "ping",
} as const;