import hmac
import json
import os

from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response

from ..mcp.server import McpProtocolError
from ..mcp.server import mcp_server


class McpController(http.Controller):

    @staticmethod
    def _internal_key() -> str | None:
        return os.environ.get(
            "AI_CHAT_MCP_KEY",
        )

    @staticmethod
    def _authenticate() -> bool:
        expected_key = (
            McpController._internal_key()
        )

        if not expected_key:
            return False

        provided_key = request.httprequest.headers.get(
            "X-MCP-Internal-Key",
        )

        if not provided_key:
            return False

        return hmac.compare_digest(
            provided_key,
            expected_key,
        )

    @staticmethod
    def _user_id() -> int:
        raw_user_id = (
            request.httprequest.headers.get(
                "X-Odoo-User-Id",
            )
        )

        if not raw_user_id:
            raise ValueError(
                "X-Odoo-User-Id header is required",
            )

        try:
            user_id = int(raw_user_id)
        except ValueError as error:
            raise ValueError(
                "X-Odoo-User-Id must be an integer",
            ) from error

        if user_id <= 0:
            raise ValueError(
                "X-Odoo-User-Id must be positive",
            )

        return user_id

    @staticmethod
    def _json_response(
        payload: dict,
        status: int = 200,
        protocol_version: str | None = None,
    ) -> Response:

        headers = [
            (
                "Content-Type",
                "application/json",
            ),
        ]

        if protocol_version:
            headers.append(
                (
                    "MCP-Protocol-Version",
                    protocol_version,
                )
            )

        return Response(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            status=status,
            headers=headers,
        )

    @http.route(
        "/ai_chat/mcp",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def mcp(
        self,
        **kwargs,
    ):
        if not self._authenticate():
            return self._json_response(
                {
                    "error":
                        "Unauthorized",
                },
                status=401,
            )

        body = request.httprequest.get_json(
            silent=True,
        )

        if not isinstance(body, dict):
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                    },
                },
                status=400,
            )

        try:
            user_id = self._user_id()

            user = (
                request.env["res.users"]
                .sudo()
                .browse(user_id)
                .exists()
            )

            if not user:
                return self._json_response(
                    {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32602,
                            "message":
                                "Invalid Odoo user",
                        },
                    },
                    status=400,
                )

            request.update_env(
                user=user_id,
                su=False,
            )

            response_payload = (
                mcp_server.handle(
                    body,
                    request.env,
                )
            )

            # MCP notifications do not
            # receive JSON-RPC responses.
            if response_payload is None:
                return Response(
                    status=202,
                )

            protocol_version = (
                response_payload
                .get("result", {})
                .get("protocolVersion")
            )

            if not protocol_version:
                protocol_version = (
                    request.httprequest.headers.get(
                        "MCP-Protocol-Version",
                    )
                )

            return self._json_response(
                response_payload,
                protocol_version=protocol_version,
            )

        except McpProtocolError as error:
            payload = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": error.code,
                    "message": error.message,
                },
            }

            if error.data is not None:
                payload["error"]["data"] = (
                    error.data
                )

            return self._json_response(
                payload,
                status=400,
            )

        except ValueError as error:
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32602,
                        "message": str(error),
                    },
                },
                status=400,
            )

        except Exception as error:
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32603,
                        "message":
                            "Internal server error",
                    },
                },
                status=500,
            )
