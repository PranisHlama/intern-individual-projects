import os

import requests

from odoo import http
from odoo.http import request


class AIChatController(http.Controller):

    def _backend_url(self):
        return os.environ.get(
            "AI_CHAT_BACKEND_URL",
            "http://host.docker.internal:8080",
        )

    def _headers(self):
        api_key = os.environ.get(
            "AI_CHAT_API_KEY",
        )

        if not api_key:
            raise RuntimeError(
                "AI_CHAT_API_KEY is not configured"
            )

        return {
            "X-API-Key": api_key,
            "X-User-Id": str(
                request.env.user.id
            ),
        }

    @http.route(
        "/ai_chat/chat",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def chat(self, message=None, model_id=None, **kwargs):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("AI Chat RPC received", extra={"message_type": type(message).__name__, "model_id_type": type(model_id).__name__, "msg_preview": str(message)[:100], "model_id": str(model_id)[:100], "kwargs_keys": list(kwargs.keys())})

        # Handle both positional and named RPC params
        if isinstance(message, dict):
            # RPC sent { message, modelId } as single object (positional)
            model_id = message.get("modelId") or message.get("model_id")
            message = message.get("message")
        elif message is None and isinstance(model_id, dict):
            # RPC sent { message, modelId } as first positional arg
            message = model_id.get("message")
            model_id = model_id.get("modelId") or model_id.get("model_id")
        elif model_id is None:
            # Named params: check kwargs for camelCase or snake_case
            model_id = kwargs.get("modelId") or kwargs.get("model_id")

        _logger.info("AI Chat after parsing", extra={"message_type": type(message).__name__, "model_id": str(model_id), "msg_preview": str(message)[:100]})

        if (
            not isinstance(message, str)
            or not message.strip()
        ):
            return {
                "error":
                    "message is required",
            }

        payload = {"message": message.strip()}
        if model_id and isinstance(model_id, str) and model_id.strip():
            payload["modelId"] = model_id.strip()

        try:
            response = requests.post(
                f"{self._backend_url()}/v1/chat",
                headers={
                    **self._headers(),
                    "Content-Type":
                        "application/json",
                },
                json=payload,
                timeout=60,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error":
                    f"AI backend unavailable: {error}",
            }

        except (
            ValueError,
            TypeError,
        ):
            return {
                "error":
                    "Invalid response from AI backend",
            }

        except RuntimeError as error:
            return {
                "error": str(error),
            }

    @http.route(
        "/ai_chat/current",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def current(self):
        try:
            response = requests.get(
                f"{self._backend_url()}/v1/chat/current",
                headers=self._headers(),
                timeout=10,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error":
                    f"AI backend unavailable: {error}",
            }

        except RuntimeError as error:
            return {
                "error": str(error),
            }

    @http.route(
        "/ai_chat/new",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def new_chat(self):
        try:
            response = requests.delete(
                f"{self._backend_url()}/v1/chat/current",
                headers=self._headers(),
                timeout=10,
            )

            response.raise_for_status()

            return {
                "success": True,
            }

        except requests.RequestException as error:
            return {
                "error":
                    f"AI backend unavailable: {error}",
            }

        except RuntimeError as error:
            return {
                "error": str(error),
            }

    @http.route(
        "/ai_chat/models",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def models(self):
        try:
            response = requests.get(
                f"{self._backend_url()}/v1/models",
                headers=self._headers(),
                timeout=10,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error":
                    f"AI backend unavailable: {error}",
            }

        except RuntimeError as error:
            return {
                "error": str(error),
            }

    @http.route(
        "/ai_chat/model/preference",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def model_preference_get(self):
        try:
            response = requests.get(
                f"{self._backend_url()}/v1/model/preference",
                headers=self._headers(),
                timeout=10,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error":
                    f"AI backend unavailable: {error}",
            }

        except RuntimeError as error:
            return {
                "error": str(error),
            }

    @http.route(
        "/ai_chat/model/preference/set",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def model_preference_set(self, model_id):
        if not isinstance(model_id, str) or not model_id.strip():
            return {
                "error": "model_id is required",
            }

        try:
            response = requests.post(
                f"{self._backend_url()}/v1/model/preference",
                headers={
                    **self._headers(),
                    "Content-Type": "application/json",
                },
                json={"modelId": model_id.strip()},
                timeout=10,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error":
                    f"AI backend unavailable: {error}",
            }

        except RuntimeError as error:
            return {
                "error": str(error),
            }

