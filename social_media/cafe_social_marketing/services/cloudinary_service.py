"""Signed JPEG upload; no SDK, unsigned preset, arbitrary endpoint or URL fetch."""
import hashlib
import os
import re
import time
from urllib.parse import urlsplit

import requests


class CloudinaryError(Exception):
    pass


class CloudinaryService:
    @staticmethod
    def credentials():
        cloud = os.environ.get('CAFE_CLOUDINARY_CLOUD_NAME', '').strip()
        key = os.environ.get('CAFE_CLOUDINARY_API_KEY', '').strip()
        secret = os.environ.get('CAFE_CLOUDINARY_API_SECRET', '').strip()
        if not re.fullmatch(r'[a-z0-9_-]{1,100}', cloud) or not key or not secret:
            raise CloudinaryError(
                'Photo hosting is not configured. Ask your administrator to set '
                'CAFE_CLOUDINARY_CLOUD_NAME, CAFE_CLOUDINARY_API_KEY and CAFE_CLOUDINARY_API_SECRET in Docker.'
            )
        return cloud, key, secret

    @staticmethod
    def signature(parameters, secret):
        value = '&'.join(f'{key}={parameters[key]}' for key in sorted(parameters))
        return hashlib.sha256((value + secret).encode('utf-8')).hexdigest()

    @classmethod
    def upload_jpeg(cls, image, public_id):
        cloud, key, secret = cls.credentials()
        if (not isinstance(image, bytes) or not image.startswith(b'\xff\xd8\xff')
                or len(image) > 8 * 1024 * 1024):
            raise CloudinaryError('Upload one JPEG no larger than 8 MiB.')
        if not re.fullmatch(r'cafe_social/[a-f0-9]{32}_[a-f0-9]{64}', public_id or ''):
            raise CloudinaryError('Invalid internal image upload identifier.')
        parameters = {'timestamp': str(int(time.time())), 'public_id': public_id,
                      'overwrite': 'false', 'type': 'upload'}
        data = dict(parameters, api_key=key, signature=cls.signature(parameters, secret))
        try:
            response = requests.post(
                f'https://api.cloudinary.com/v1_1/{cloud}/image/upload', data=data,
                files={'file': ('post.jpg', image, 'image/jpeg')},
                timeout=(10, 60), allow_redirects=False,
            )
        except requests.RequestException:
            raise CloudinaryError(
                'Photo hosting could not confirm the upload. Instagram was not contacted. '
                'Try Publish again; the same image identifier will be reused.'
            ) from None
        try:
            result = response.json()
        except ValueError:
            raise CloudinaryError('Photo hosting returned an unreadable response. Instagram was not contacted.') from None
        if not (200 <= response.status_code < 300) or not isinstance(result, dict) or result.get('error'):
            raise CloudinaryError(
                f'Photo hosting rejected the upload (HTTP {response.status_code}). '
                'Check Cloudinary credentials, upload settings and account limits. Instagram was not contacted.'
            )
        url = result.get('secure_url')
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
            expected = f'/{cloud}/image/upload/'
            if (not parsed or parsed.scheme != 'https' or parsed.netloc != 'res.cloudinary.com'
                    or parsed.query or parsed.fragment or not parsed.path.startswith(expected)
                    or result.get('public_id') != public_id or result.get('format') not in ('jpg', 'jpeg')):
                raise ValueError()
            suffix = parsed.path[len(expected):]
            if not re.fullmatch(r'v[0-9]+/' + re.escape(public_id) + r'\.(?:jpg|jpeg)', suffix):
                raise ValueError()
        except ValueError:
            raise CloudinaryError('Photo hosting returned an unexpected image destination. Instagram was not contacted.') from None
        return url, public_id
