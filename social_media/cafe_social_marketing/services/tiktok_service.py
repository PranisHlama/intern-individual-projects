import math

import requests


class TikTokAPIError(Exception):
    """Raised when TikTok's Content Posting API returns an error."""


class TikTokService:
    """Small wrapper around TikTok Content Posting API (video upload draft flow)."""

    API_BASE = "https://open.tiktokapis.com"
    INIT_UPLOAD_PATH = "/v2/post/publish/inbox/video/init/"
    STATUS_PATH = "/v2/post/publish/status/fetch/"

    SUPPORTED_MIME_TYPES = {
        "video/mp4",
        "video/quicktime",
        "video/webm",
    }

    MIN_CHUNK_SIZE = 5 * 1024 * 1024
    MAX_CHUNK_SIZE = 64 * 1024 * 1024
    MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024

    @classmethod
    def _headers(cls, access_token, content_type="application/json; charset=UTF-8"):
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
        }

    @classmethod
    def _raise_for_api_error(cls, response, action):
        try:
            payload = response.json()
        except ValueError as exc:
            raise TikTokAPIError(
                f"TikTok returned a non-JSON response while {action}. "
                f"HTTP {response.status_code}."
            ) from exc

        error = payload.get("error") or {}
        code = error.get("code")

        if not response.ok or (code and code != "ok"):
            message = error.get("message") or response.text or "Unknown TikTok API error"
            raise TikTokAPIError(
                f"TikTok API error while {action}: {code or response.status_code} - {message}"
            )

        return payload

    @classmethod
    def _chunk_plan(cls, video_size):
        if video_size <= 0:
            raise TikTokAPIError("The selected video is empty.")

        if video_size > cls.MAX_VIDEO_SIZE:
            raise TikTokAPIError("TikTok video uploads cannot exceed 4 GB.")

        if video_size <= cls.MAX_CHUNK_SIZE:
            return video_size, 1

        chunk_size = cls.MAX_CHUNK_SIZE
        full_chunks, remainder = divmod(video_size, chunk_size)

        if remainder == 0:
            total_chunk_count = full_chunks
        elif remainder < cls.MIN_CHUNK_SIZE:
            # Merge the tiny remainder into the final full chunk.
            total_chunk_count = full_chunks
        else:
            total_chunk_count = full_chunks + 1

        if total_chunk_count > 1000:
            raise TikTokAPIError("The video requires too many upload chunks.")

        return chunk_size, total_chunk_count

    @classmethod
    def initialize_draft_upload(cls, access_token, video_size):
        chunk_size, total_chunk_count = cls._chunk_plan(video_size)

        response = requests.post(
            cls.API_BASE + cls.INIT_UPLOAD_PATH,
            headers=cls._headers(access_token),
            json={
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunk_count,
                }
            },
            timeout=30,
        )

        payload = cls._raise_for_api_error(
            response,
            "initializing the video upload",
        )

        data = payload.get("data") or {}
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")

        if not publish_id or not upload_url:
            raise TikTokAPIError(
                "TikTok did not return both publish_id and upload_url."
            )

        return {
            "publish_id": publish_id,
            "upload_url": upload_url,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunk_count,
        }

    @classmethod
    def upload_video_bytes(cls, upload_url, video_data, mime_type, chunk_size):
        if mime_type not in cls.SUPPORTED_MIME_TYPES:
            raise TikTokAPIError(
                "Unsupported video type. Use MP4, MOV, or WebM."
            )

        total_size = len(video_data)
        position = 0

        while position < total_size:
            remaining = total_size - position

            # If taking a normal chunk would leave a final piece smaller than
            # TikTok's 5 MB minimum, merge that trailing piece into this chunk.
            if remaining > chunk_size and (remaining - chunk_size) < cls.MIN_CHUNK_SIZE:
                current_size = remaining
            else:
                current_size = min(chunk_size, remaining)

            end_exclusive = position + current_size
            end_inclusive = end_exclusive - 1
            chunk = video_data[position:end_exclusive]

            response = requests.put(
                upload_url,
                headers={
                    "Content-Type": mime_type,
                    "Content-Length": str(current_size),
                    "Content-Range": (
                        f"bytes {position}-{end_inclusive}/{total_size}"
                    ),
                },
                data=chunk,
                timeout=120,
            )

            if not response.ok:
                raise TikTokAPIError(
                    "TikTok rejected a video chunk. "
                    f"HTTP {response.status_code}: {response.text[:500]}"
                )

            position = end_exclusive

        return True

    @classmethod
    def upload_video_as_draft(cls, access_token, video_data, mime_type):
        init = cls.initialize_draft_upload(
            access_token,
            len(video_data),
        )

        cls.upload_video_bytes(
            init["upload_url"],
            video_data,
            mime_type,
            init["chunk_size"],
        )

        return init["publish_id"]

    @classmethod
    def fetch_status(cls, access_token, publish_id):
        response = requests.post(
            cls.API_BASE + cls.STATUS_PATH,
            headers=cls._headers(access_token),
            json={"publish_id": publish_id},
            timeout=30,
        )

        payload = cls._raise_for_api_error(
            response,
            "checking the upload status",
        )

        return payload.get("data") or {}
