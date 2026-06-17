"""
Instagram Service — powered by Instagrapi
Handles all Instagram interactions using the unofficial Instagrapi library.
No Meta Developer App or API key required — uses your real Instagram credentials.

Session is persisted to a JSON file to avoid logging in on every request.
"""
import logging
import os
import json
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


class InstagramAPIError(Exception):
    """Raised when an Instagram operation fails."""


def _get_client():
    """
    Return an authenticated Instagrapi Client instance.
    Loads a persisted session if available; otherwise logs in fresh.
    Raises InstagramAPIError if credentials are missing or login fails.
    """
    from instagrapi import Client
    from instagrapi.exceptions import (
        LoginRequired,
        BadPassword,
        TwoFactorRequired,
        ChallengeRequired,
    )

    username = getattr(settings, 'INSTAGRAM_USERNAME', '')
    password = getattr(settings, 'INSTAGRAM_PASSWORD', '')
    session_file = getattr(settings, 'INSTAGRAM_SESSION_FILE', 'instagram_session.json')

    if not username or not password:
        raise InstagramAPIError(
            'Instagram credentials not configured. '
            'Add INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD to your .env file.'
        )

    cl = Client()
    cl.delay_range = [1, 3]  # Be polite: wait 1–3s between requests

    # Try to reuse existing session
    session_path = Path(session_file)
    if session_path.exists():
        try:
            cl.load_settings(session_path)
            cl.login(username, password)
            logger.info('Instagram: session reloaded for @%s', username)
            return cl
        except LoginRequired:
            logger.warning('Instagram: session expired, re-logging in...')
        except Exception as exc:
            logger.warning('Instagram: session load failed (%s), re-logging in...', exc)

    # Fresh login
    try:
        cl.login(username, password)
        cl.dump_settings(session_path)
        logger.info('Instagram: fresh login successful for @%s', username)
        return cl
    except BadPassword:
        raise InstagramAPIError('Invalid Instagram password. Check INSTAGRAM_PASSWORD in .env.')
    except TwoFactorRequired:
        raise InstagramAPIError(
            '2FA is enabled on this Instagram account. '
            'Disable 2FA or use a dedicated account without 2FA.'
        )
    except ChallengeRequired:
        raise InstagramAPIError(
            'Instagram requires a challenge (e.g. phone verification). '
            'Log into Instagram manually once to clear the challenge, then retry.'
        )
    except Exception as exc:
        raise InstagramAPIError(f'Instagram login failed: {exc}') from exc


# ---------------------------------------------------------------------------
# Fetch user's own media (syncs into ConnectSphere feed)
# ---------------------------------------------------------------------------

def fetch_user_media(username, amount=12):
    """
    Fetch the latest posts from any public Instagram profile by username.
    Returns a list of dicts with: id, media_type, url, thumbnail_url,
    caption, taken_at, permalink
    """
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        medias = cl.user_medias(user_id, amount=amount)
        results = []
        for m in medias:
            results.append({
                'id': str(m.id),
                'media_type': m.media_type.name if hasattr(m.media_type, 'name') else str(m.media_type),
                'url': str(m.thumbnail_url or m.video_url or ''),
                'thumbnail_url': str(m.thumbnail_url or ''),
                'caption': m.caption_text or '',
                'taken_at': m.taken_at,
                'permalink': f'https://www.instagram.com/p/{m.code}/',
                'like_count': m.like_count,
                'comment_count': m.comment_count,
            })
        return results
    except InstagramAPIError:
        raise
    except Exception as exc:
        raise InstagramAPIError(f'Failed to fetch media for @{username}: {exc}') from exc


def fetch_own_media(amount=12):
    """
    Fetch the authenticated account's own latest media.
    Used when syncing the logged-in Instagram account's posts.
    """
    try:
        cl = _get_client()
        own_username = cl.account_info().username
        return fetch_user_media(own_username, amount=amount)
    except InstagramAPIError:
        raise
    except Exception as exc:
        raise InstagramAPIError(f'Failed to fetch own media: {exc}') from exc


# ---------------------------------------------------------------------------
# Download media to a Django File object
# ---------------------------------------------------------------------------

def download_media_to_file(media_url, filename):
    """
    Download an Instagram media file and return it as a Django ContentFile.
    Returns None if the download fails.
    """
    import urllib.request
    import urllib.error
    from django.core.files.base import ContentFile

    if not media_url:
        return None

    try:
        req = urllib.request.Request(
            media_url,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) '
                    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
                )
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
        return ContentFile(content, name=filename)
    except Exception as exc:
        logger.error('Failed to download media from %s: %s', media_url, exc)
        return None


# ---------------------------------------------------------------------------
# oEmbed for public iframe embeds (no auth required)
# ---------------------------------------------------------------------------

def fetch_oembed(instagram_url):
    """
    Fetch oEmbed data for a public Instagram post.
    Uses Instagram's unofficial oEmbed endpoint — no token required.
    Returns dict with 'html' key, or None if unavailable.
    """
    import urllib.request
    import urllib.parse
    import urllib.error

    endpoint = 'https://www.instagram.com/api/v1/oembed/'
    url = f'{endpoint}?url={urllib.parse.quote(instagram_url)}&hidecaption=false&omitscript=true'

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ConnectSphere/1.0)',
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        return data
    except Exception as exc:
        logger.info('oEmbed unavailable for %s: %s', instagram_url, exc)
        return None


# ---------------------------------------------------------------------------
# Session management helpers
# ---------------------------------------------------------------------------

def clear_session():
    """Delete the persisted session file to force a fresh login."""
    session_file = getattr(settings, 'INSTAGRAM_SESSION_FILE', 'instagram_session.json')
    path = Path(session_file)
    if path.exists():
        path.unlink()
        logger.info('Instagram session cleared.')


def get_connection_info():
    """
    Return basic info about the connected Instagram account.
    Returns dict with username, full_name, follower_count, following_count,
    or raises InstagramAPIError if not connected.
    """
    try:
        cl = _get_client()
        info = cl.account_info()
        return {
            'username': info.username,
            'full_name': info.full_name,
            'follower_count': info.follower_count,
            'following_count': info.following_count,
            'media_count': info.media_count,
            'profile_pic_url': str(info.profile_pic_url or ''),
            'is_private': info.is_private,
        }
    except InstagramAPIError:
        raise
    except Exception as exc:
        raise InstagramAPIError(f'Failed to get account info: {exc}') from exc
