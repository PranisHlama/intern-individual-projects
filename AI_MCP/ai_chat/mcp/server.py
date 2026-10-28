import json
from typing import Any

from odoo.api import Environment

from .registry import McpToolRegistry
from .tools import register_all_tools


MCP_PROTOCOL_VERSION = "2025-11-25"

SUPPORTED_PROTOCOL_VERSIONS = {
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
}


class McpProtocolError(Exception):

    def __init__(
        self,
        code: int,
        message: str,
        data: Any = None,
    ) -> None:
        super().__init__(message)

        self.code = code
        self.message = message
        self.data = data


class McpServer:

    def __init__(self) -> None:
        self.registry = McpToolRegistry()

        register_all_tools(
            self.registry,
        )

    def handle(
        self,
        message: dict[str, Any],
        env: Environment,
    ) -> dict[str, Any] | None:

        if message.get("jsonrpc") != "2.0":
            raise McpProtocolError(
                -32600,
                "Invalid Request",
            )

        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}

        if not isinstance(params, dict):
            raise McpProtocolError(
                -32602,
                "Invalid params",
            )

        if method == "initialize":
            return self._initialize(
                request_id,
                params,
            )

        if method == "notifications/initialized":
            # Notifications do not receive
            # a JSON-RPC response.
            return None

        if method == "ping":
            return self._success(
                request_id,
                {},
            )

        if method == "tools/list":
            return self._tools_list(
                request_id,
            )

        if method == "tools/call":
            return self._tools_call(
                request_id,
                params,
                env,
            )

        raise McpProtocolError(
            -32601,
            f"Method not found: {method}",
        )

    def _initialize(
        self,
        request_id: Any,
        params: dict[str, Any],
    ) -> dict[str, Any]:

        requested_version = params.get(
            "protocolVersion",
        )

        if (
            requested_version
            in SUPPORTED_PROTOCOL_VERSIONS
        ):
            negotiated_version = (
                requested_version
            )
        else:
            negotiated_version = (
                MCP_PROTOCOL_VERSION
            )

        return self._success(
            request_id,
            {
                "protocolVersion":
                    negotiated_version,

                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    },
                },

                "serverInfo": {
                    "name": "ai_chat",
                    "version": "20.0.1.0.0",
                },

                "instructions": (
                    "This MCP server exposes "
                    "Odoo-specific tools for the "
                    "AI Chat module."
                ),
            },
        )

    def _tools_list(
        self,
        request_id: Any,
    ) -> dict[str, Any]:

        return self._success(
            request_id,
            {
                "tools":
                    self.registry.list_tools(),
            },
        )

    def _tools_call(
        self,
        request_id: Any,
        params: dict[str, Any],
        env: Environment,
    ) -> dict[str, Any]:

        name = params.get("name")
        arguments = params.get(
            "arguments",
            {},
        )

        if not isinstance(name, str):
            raise McpProtocolError(
                -32602,
                "tools/call requires a tool name",
            )

        if not isinstance(arguments, dict):
            raise McpProtocolError(
                -32602,
                "tools/call arguments must be an object",
            )

        tool = self.registry.get(name)

        if tool is None:
            raise McpProtocolError(
                -32602,
                f"Unknown tool: {name}",
            )

        try:
            result = tool.handler(
                env,
                arguments,
            )

            return self._success(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                result,
                                ensure_ascii=False,
                            ),
                        },
                    ],
                    "isError": False,
                },
            )

        except Exception as error:
            return self._success(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": str(error),
                        },
                    ],
                    "isError": True,
                },
            )

    @staticmethod
    def _success(
        request_id: Any,
        result: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }


mcp_server = McpServer()
