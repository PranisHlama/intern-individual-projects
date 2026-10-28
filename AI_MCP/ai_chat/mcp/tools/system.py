from typing import Any

from odoo.api import Environment

from ..registry import McpTool
from ..registry import McpToolRegistry


def ping(
    env: Environment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": True,
        "service": "ai_chat",
        "user_id": env.user.id,
        "user_name": env.user.name,
    }


def register_system_tools(
    registry: McpToolRegistry,
) -> None:
    registry.register(
        McpTool(
            name="ping",
            description=(
                "Check that the Odoo AI Chat MCP server "
                "is running and return the current Odoo user."
            ),
            input_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=ping,
        )
    )
