"""Helpers shared by the ONLYOFFICE and browser editor controllers."""

import base64
import json

from odoo.http import request


def get_param(key):
    """System parameter value, or False when it is not set."""
    return request.env["ir.config_parameter"].sudo().get_str(key) or False


def get_file_binary(dms_file):
    """DMS file content as raw bytes."""
    content = dms_file.content

    if not content:
        return b""

    if isinstance(content, str):
        return base64.b64decode(content)

    return bytes(content)


def json_response(data, status=200):
    return request.make_response(
        json.dumps(data),
        headers=[("Content-Type", "application/json")],
        status=status,
    )


def text_response(message, status):
    return request.make_response(
        message,
        headers=[("Content-Type", "text/plain; charset=utf-8")],
        status=status,
    )
