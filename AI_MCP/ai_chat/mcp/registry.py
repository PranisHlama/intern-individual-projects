from dataclasses import dataclass
from typing import Any, Callable

from odoo.api import Environment


ToolHandler = Callable[
    [Environment, dict[str, Any]],
    Any,
]


@dataclass(frozen=True)
class McpTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler


class McpToolRegistry:

    def __init__(self) -> None:
        self._tools: dict[str, McpTool] = {}

    def register(
        self,
        tool: McpTool,
    ) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"MCP tool already registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def get(
        self,
        name: str,
    ) -> McpTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]
