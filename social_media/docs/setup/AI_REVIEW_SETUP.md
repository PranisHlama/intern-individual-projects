# Optional local AI Review

AI Review asks a local Ollama model to assess writing tone, clarity and potential wording issues, then returns a suggested rewrite. It does not establish discount/date/account correctness, approve a post, publish media or generate an image.

## Current configuration

The uploaded source defines Python constants in [services/ollama_service.py](../../cafe_social_marketing/services/ollama_service.py):

| Constant | Current value |
| --- | --- |
| `OLLAMA_URL` | `http://host.docker.internal:11434/api/chat` |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` |
| Request timeout | 90 seconds |

They are **not environment-variable settings** in this version. Editing an `.env` entry named `OLLAMA_MODEL` does not change this code. Changing the host/model requires a reviewed service-code change and restart, or a future configuration feature.

The example endpoint assumes Ollama is reachable from the Odoo container on its host. `host.docker.internal` is deployment-specific; do not assume it resolves in every Linux/container setup. Keep model access local/trusted rather than exposing the model API broadly merely to make the URL work.

## Workflow

Run the configured Ollama service/model separately, enter a caption and click AI Review. Read the returned assessment, tone, clarity, issues and suggested rewrite. Applying a rewrite changes the caption and resets the relevant workflow checks. Validate and obtain current manager approval afterward.

The model receives caption and selected campaign/branch/product/date/account context. No platform access token is included in that review payload. Use only content suitable for the configured model service.

## Failure and resource limits

Connection/timeouts or invalid JSON may produce a Review Error/UserError; they do not authorise publishing. The model can be slow on limited-memory hardware. Designer and deterministic validation do not require Ollama and remain useful without it.

Review the actual AI result fields and negative scenarios in Odoo before describing error persistence or all reset behavior as tested. Current documentation does not claim a fresh AI performance or runtime test.
