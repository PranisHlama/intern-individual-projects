"""Single-image Instagram Graph API client; Facebook Login token route."""
import re

import requests


class InstagramAPIError(Exception):
    def __init__(self, message, uncertain=False):
        super().__init__(message)
        self.uncertain = uncertain


class InstagramService:
    VERSION = "v26.0"

    @staticmethod
    def _id(value):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
            raise InstagramAPIError("Instagram returned an invalid or missing identifier.", uncertain=True)
        return value

    @classmethod
    def _request(cls, method, object_id, token, edge=None, data=None):
        cls._id(object_id)
        url = f"https://graph.facebook.com/{cls.VERSION}/{object_id}"
        if edge:
            if edge not in ("media", "media_publish"):
                raise InstagramAPIError("Unsupported Instagram operation.")
            url += "/" + edge
        try:
            if method == "GET":
                response = requests.get(url, params=data, headers={"Authorization": f"Bearer {token}"},
                                        timeout=(10, 45), allow_redirects=False)
            else:
                response = requests.post(url, data=data, headers={"Authorization": f"Bearer {token}"},
                                         timeout=(10, 45), allow_redirects=False)
        except requests.RequestException as exc:
            raise InstagramAPIError(
                "Instagram network error. Check Instagram before resending; the operation may have completed.",
                uncertain=method != "GET",
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise InstagramAPIError("Instagram returned an unreadable response.", uncertain=method != "GET") from exc
        if not isinstance(payload, dict):
            raise InstagramAPIError("Instagram returned an unexpected response.", uncertain=method != "GET")
        if not response.ok or payload.get("error"):
            err = payload.get("error")
            err = err if isinstance(err, dict) else {}
            # Remote messages/IDs may echo request data or tokens: retain only numeric codes.
            code = err.get("code") if isinstance(err.get("code"), int) else "unknown"
            subcode = err.get("error_subcode") if isinstance(err.get("error_subcode"), int) else "none"
            raise InstagramAPIError(
                f"Instagram rejected the request (HTTP {response.status_code}, code {code}, subcode {subcode}). "
                "Check token permissions/expiry, account access and JPEG URL requirements.",
                uncertain=method != "GET" and (response.status_code >= 500 or 300 <= response.status_code < 400),
            )
        return payload

    @classmethod
    def create_container(cls, user_id, token, caption, image_url):
        payload = cls._request("POST", user_id, token, "media", {"caption": caption, "image_url": image_url})
        return cls._id(payload.get("id"))

    @classmethod
    def container_status(cls, container_id, token):
        payload = cls._request("GET", container_id, token, data={"fields": "status_code"})
        status = payload.get("status_code")
        if status not in ("IN_PROGRESS", "FINISHED", "ERROR", "EXPIRED", "PUBLISHED"):
            raise InstagramAPIError("Instagram container status was missing or unrecognised. Recheck the same container.")
        return status

    @classmethod
    def publish_container(cls, user_id, token, container_id):
        cls._id(container_id)
        payload = cls._request("POST", user_id, token, "media_publish", {"creation_id": container_id})
        return cls._id(payload.get("id"))
