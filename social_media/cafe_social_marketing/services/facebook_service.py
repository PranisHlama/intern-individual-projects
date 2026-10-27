import re

import requests


class FacebookAPIError(Exception):
    def __init__(self, message, uncertain=False):
        super().__init__(message)
        self.uncertain = uncertain


class FacebookService:
    @staticmethod
    def _request(page_id, token, edge, data, files=None, version="v26.0"):
        if not re.fullmatch(r"[0-9]+", page_id or ""):
            raise FacebookAPIError("Enter a valid numeric Facebook Page ID.")
        if not re.fullmatch(r"v[0-9]+\.0", version or ""):
            raise FacebookAPIError("Invalid Graph API version.")
        try:
            kwargs = {"files": files} if files else {}
            response = requests.post(
                f"https://graph.facebook.com/{version}/{page_id}/{edge}",
                headers={"Authorization": f"Bearer {token}"},
                data=data,
                timeout=(10, 45),
                allow_redirects=False,
                **kwargs,
            )
        except requests.RequestException as exc:
            # Do not expose exception URLs/headers or automatically resend:
            # Facebook might have accepted the request before the timeout.
            raise FacebookAPIError(
                "Network error. Check the Facebook Page before retrying; "
                "the publishing outcome is unknown.", uncertain=True,
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise FacebookAPIError(
                "Unexpected response. Check the Page before retrying.",
                uncertain=True,
            ) from exc
        if not isinstance(payload, dict):
            raise FacebookAPIError("Unexpected response; check the Page.", uncertain=True)
        error = payload.get("error")
        if error or not response.ok:
            # Record codes only; remote error messages can echo credentials.
            error = error if isinstance(error, dict) else {}
            raise FacebookAPIError(
                f"Facebook rejected the request (HTTP {response.status_code}, "
                f"code {error.get('code', 'unknown')}, "
                f"subcode {error.get('error_subcode', 'none')}). "
                "Check token expiry, Page permissions and app access.",
                uncertain=response.status_code >= 500,
            )
        return payload

    @classmethod
    def publish_text(cls, page_id, token, message, version="v26.0"):
        payload = cls._request(page_id, token, "feed",
                               {"message": message, "published": "true"}, version=version)
        post_id = payload.get("id")
        if not isinstance(post_id, str) or not re.fullmatch(r"[0-9]+_[0-9]+", post_id):
            raise FacebookAPIError("Missing post ID; check the Page.", uncertain=True)
        return post_id

    @classmethod
    def publish_photo(cls, page_id, token, caption, image_data, mime_type, version="v26.0"):
        if mime_type not in ("image/jpeg", "image/png") or not image_data:
            raise FacebookAPIError("Use one nonempty JPEG or PNG image.")
        if len(image_data) > 10 * 1024 * 1024:
            raise FacebookAPIError("The image exceeds this adapter's 10 MiB limit.")
        filename = "photo.jpg" if mime_type == "image/jpeg" else "photo.png"
        payload = cls._request(
            page_id, token, "photos", {"caption": caption, "published": "true"},
            files={"source": (filename, image_data, mime_type)}, version=version,
        )
        photo_id, post_id = payload.get("id"), payload.get("post_id")
        if not isinstance(photo_id, str) or not re.fullmatch(r"[0-9]+", photo_id):
            raise FacebookAPIError("Missing photo ID; check the Page before retrying.", uncertain=True)
        if not isinstance(post_id, str) or not re.fullmatch(r"[0-9]+_[0-9]+", post_id):
            raise FacebookAPIError(
                "Facebook returned a photo ID but no confirmed feed post ID. "
                "Check the Page before retrying.", uncertain=True,
            )
        return post_id, photo_id
