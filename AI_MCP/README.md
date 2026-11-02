# AI Chat Assistant

AI-powered ERP assistant system for Odoo 20. Consists of two parts:

- **AI_MCP** - Odoo 20 addon (`ai_chat/`) that exposes ERP data as MCP tools
- **Harness** - Node.js orchestrator backend (`harness/`) that routes chat messages to LLMs and calls MCP tools

Together they let users chat with Odoo using natural language through an MCP (Model Context Protocol) bridge.

---

# AI_MCP (Odoo 20 Addon)

Odoo 20 addon that exposes ERP data and operations to an AI assistant through an **MCP (Model Context Protocol) server**. Works with the cafe-ai-harness orchestrator backend to let users chat with Odoo using natural language.

## What It Does

- **MCP Server** - JSON-RPC 2.0 endpoint at `/ai_chat/mcp` that exposes Odoo business data as callable tools
- **Manufacturing Tools** - List and view manufacturing orders, BOM lines, work orders, stock moves, scrap
- **BOM Tools** - List Bills of Materials and view full BOM detail (components, operations, by-products)
- **Inventory Tools** - Query stock levels per product/location and product stock summaries
- **Knowledge Search** - Full-text search over company Markdown documents (TF-IDF)
- **System** - Ping/health check that returns the current Odoo user
- **Odoo → Harness Proxy** - JSON-RPC controllers that forward chat messages to the harness backend

## MCP Tools Reference

| Tool | Model | Description |
|------|-------|-------------|
| `ping` | `res.users` | Health check; returns current Odoo user |
| `search_knowledge` | Markdown files | Full-text search over company knowledge documents |
| `get_manufacturing_orders` | `mrp.production` | List manufacturing orders (filter by state, product, dates, user) |
| `get_manufacturing_order` | `mrp.production` | Full MO detail: header, BOM lines, work orders, stock moves, scrap |
| `get_boms` | `mrp.bom` | List Bills of Materials (filter by product, type, company, active) |
| `get_bom` | `mrp.bom` | Full BOM detail: header, components, operations, by-products |
| `get_stock_levels` | `stock.quant` | Current stock levels per product/location (qty on hand, reserved, available) |
| `get_product_stock` | `product.product` | Product stock summary (on hand, forecasted, incoming, outgoing, free) |


## Configuration

Copy `ai_chat/.env.example` to `ai_chat/.env` and fill in values:

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_CHAT_MCP_KEY` | Shared secret for MCP auth (must match harness `MCP_INTERNAL_KEY`) | `test` |
| `AI_CHAT_BACKEND_URL` | Harness backend URL for chat proxying | `http://host.docker.internal:8080` |
| `AI_CHAT_API_KEY` | API key for Odoo → harness auth | `your-harness-api-key` |
| `AI_KNOWLEDGE_ROOT` | Root path for knowledge Markdown files | `/mnt/ai_chat_knowledge` |

## Installation

1. Copy the `ai_chat/` folder into your Odoo 20 `addons` path.
2. Update `__manifest__.py` dependencies if needed (currently: `web`, `mrp`, `stock`).
3. Configure `ai_chat/.env` with your MCP key and harness backend URL.
4. Update Odoo's app list and install the **AI Chat** module.

## MCP Endpoint

- **URL:** `http://<odoo-host>:8069/ai_chat/mcp`
- **Method:** `POST`
- **Auth headers:**
  - `X-MCP-Internal-Key` - must match `AI_CHAT_MCP_KEY`
  - `X-Odoo-User-Id` - integer ID of the Odoo user
  - `MCP-Protocol-Version` - e.g. `2025-11-25`


# cafe-ai-harness (Orchestrator Backend)

Orchestrator service for AI chat. Handles model routing, MCP tool calling, conversation storage and Redis caching.

## What It Does

- **Model Registry** - Loads models from `MODELS_CONFIG`, routes requests to correct provider
- **MCP Client** - Calls tools on external MCP server (Odoo AI chat)
- **Conversation Store** - Redis + in-memory fallback with TTL + token-aware sliding window
- **HTTP API** - Express endpoints for chat, history, model listing, preferences

## Quick Start

### 1. Prerequisites
- Node.js 20+
- Redis 7+
- MCP server running (default `http://localhost:8069/ai_chat/mcp`)

### 2. Install
```bash
cd harness
pnpm install
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your API keys and MCP URL
```

Required vars:
| Variable | Description |
|----------|-------------|
| `MODELS_CONFIG` | JSON string defining providers + models (see below) |
| `MCP_URL` | MCP server endpoint |
| `MCP_INTERNAL_KEY` | Shared secret for MCP auth |
| `REDIS_HOST`, `REDIS_PORT` | Redis connection |

### 4. Run
```bash
# Development
pnpm dev

# Production build
pnpm build && pnpm start
```

Server starts on `PORT` (default 8080).

## MODELS_CONFIG Format

Single source of truth for all model settings. No fallbacks.

```json
{
  "providers": [
    { "id": "nvidia", "baseUrl": "https://integrate.api.nvidia.com/v1", "apiKey": "..." },
    { "id": "gemini", "baseUrl": "https://generativelanguage.googleapis.com/v1beta", "apiKey": "..." }
  ],
  "models": [
    {
      "providerId": "nvidia",
      "modelId": "nvidia/nemotron-3-ultra-550b-a55b",
      "displayName": "Nemotron 3 Ultra",
      "capabilities": { "streaming": true, "tools": true, "contextWindow": 4096 },
      "maxTokens": 100000,
      "temperature": 0.7,
      "timeoutMs": 45000,
      "isDefault": true
    }
  ]
}
```

Each model **must** define:
- `capabilities.contextWindow` - input token limit (history window)
- `maxTokens` - output token limit (reply length)
- `temperature` - sampling temperature (0-2)
- `timeoutMs` - request timeout

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Send message, get response |
| GET | `/chat/:userId` | Get conversation history |
| DELETE | `/chat/:userId` | Delete conversation |
| GET | `/models` | List available models |
| GET | `/models/preference/:userId` | Get user's model preference |
| POST | `/models/preference` | Set user's model preference |

## Key Design Decisions

- **Per-model config** - No provider-level defaults; every model declares its own limits
- **Token-aware context window** - Sliding window uses model's actual `contextWindow`
- **Redis primary, in-memory fallback** - Conversations survive restarts
- **DI container** - Clean separation, easy to swap adapters

---

## How the Two Parts Work Together

1. User sends a message from the Odoo frontend (`ai_systray` widget).
2. `ai_chat/controllers/ai_controller.py` proxies the message to the harness backend at `/v1/chat`.
3. The harness routes the message to the configured LLM with available MCP tools.
4. If the LLM calls a tool (e.g., `get_boms`), the harness MCP client calls `http://<odoo>:8069/ai_chat/mcp`.
5. The Odoo MCP server queries the Odoo ORM and returns structured data.
6. The harness formats the result into human-readable Markdown and returns it to the user.

