"""Explicit Meta profile fetches; no credentials or remote URLs are persisted."""
import io
import ipaddress
import re
import socket
import time
from urllib.parse import urlsplit

import requests
from PIL import Image, ImageOps, UnidentifiedImageError

GRAPH = 'https://graph.facebook.com/v26.0'
MAX_PHOTO = 2 * 1024 * 1024
CDN_SUFFIXES = ('fbcdn.net', 'cdninstagram.com', 'fbsbx.com')


class ProfileSyncError(Exception):
    pass


def _cdn_url(url):
    try:
        if not isinstance(url, str) or len(url) > 8192 or any(c.isspace() or ord(c) < 32 for c in url):
            raise ValueError()
        parsed = urlsplit(url)
        host = (parsed.hostname or '').lower()
        if (parsed.scheme != 'https' or parsed.username is not None or parsed.password is not None
                or parsed.fragment or parsed.port not in (None, 443)
                or not any(host == suffix or host.endswith('.' + suffix) for suffix in CDN_SUFFIXES)):
            raise ValueError()
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or not all(ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError()
    except (ValueError, TypeError, OSError):
        raise ProfileSyncError('The platform returned an unsupported profile photo address.') from None
    return url


def _avatar(url):
    url = _cdn_url(url)
    try:
        started = time.monotonic()
        with requests.get(url, timeout=(5, 10), allow_redirects=False, stream=True) as response:
            if response.status_code != 200:
                raise ValueError()
            raw = bytearray()
            for chunk in response.iter_content(32768):
                if time.monotonic() - started > 20:
                    raise ValueError()
                raw.extend(chunk)
                if len(raw) > MAX_PHOTO:
                    raise ValueError()
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 16_000_000:
                    raise ValueError()
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                image = ImageOps.exif_transpose(image)
                image.thumbnail((192, 192), Image.Resampling.LANCZOS)
                rgba = image.convert('RGBA')
                clean = Image.new('RGB', rgba.size, 'white')
                clean.paste(rgba, mask=rgba.getchannel('A'))
                output = io.BytesIO()
                clean.save(output, format='JPEG', quality=85)
                return output.getvalue()
    except (requests.RequestException, ValueError, TypeError, OSError, UnidentifiedImageError,
            Image.DecompressionBombError):
        raise ProfileSyncError('Could not download the profile photo. The previous profile was kept; try again later.') from None


def _text(value, maximum, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ProfileSyncError('The platform returned an invalid profile. The previous profile was kept.')
    return value.strip()


class MetaProfileService:
    @staticmethod
    def fetch(platform, remote_id, token):
        if platform not in ('facebook', 'instagram') or not re.fullmatch(r'[0-9]+', remote_id or ''):
            raise ProfileSyncError('Select a Facebook Page or Instagram professional account with a numeric ID.')
        fields = 'id,name,picture.width(192).height(192)' if platform == 'facebook' else 'id,name,username,profile_picture_url'
        try:
            response = requests.get(f'{GRAPH}/{remote_id}', params={'fields': fields},
                                    headers={'Authorization': 'Bearer ' + token},
                                    timeout=(5, 20), allow_redirects=False)
            try:
                if response.status_code != 200:
                    raise ValueError()
                result = response.json()
            finally:
                response.close()
            if not isinstance(result, dict) or 'error' in result or result.get('id') != remote_id:
                raise ValueError()
        except (requests.RequestException, ValueError, TypeError):
            raise ProfileSyncError('Could not read the profile. Check the account ID, token and read permissions, then retry.') from None
        name = _text(result.get('name', ''), 200, required=platform == 'facebook')
        username = _text(result.get('username', ''), 100, required=platform == 'instagram')
        if platform == 'facebook':
            picture = result.get('picture', {})
            if not isinstance(picture, dict) or not isinstance(picture.get('data', {}), dict):
                raise ProfileSyncError('The platform returned an invalid profile photo response.')
            picture = picture.get('data', {})
            url = '' if picture.get('is_silhouette') else picture.get('url', '')
        else:
            url = result.get('profile_picture_url', '')
        if not isinstance(url, str):
            raise ProfileSyncError('The platform returned an invalid profile photo response.')
        photo = _avatar(url) if url else b''
        return {'name': name or username, 'username': username, 'image': photo}
