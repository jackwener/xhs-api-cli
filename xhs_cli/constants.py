"""Constants for XHS API client.

Targets the xiaohongshu.com PC web by default. Set ``XHS_TARGET=rednote`` to
point at the international rednote.com host triplet — the two domains share
the same backend, API surface, and signing scheme; they differ only in host
names and cookie domain.
"""

from __future__ import annotations

import os
from typing import NamedTuple


class _Target(NamedTuple):
    name: str
    edith_host: str
    creator_host: str
    home_url: str
    upload_host: str
    cookie_domain: str
    login_url: str


_TARGETS: dict[str, _Target] = {
    "xiaohongshu": _Target(
        name="xiaohongshu",
        edith_host="https://edith.xiaohongshu.com",
        creator_host="https://creator.xiaohongshu.com",
        home_url="https://www.xiaohongshu.com",
        upload_host="https://ros-upload.xiaohongshu.com",
        cookie_domain="xiaohongshu.com",
        login_url="https://www.xiaohongshu.com/login",
    ),
    "rednote": _Target(
        name="rednote",
        edith_host="https://webapi.rednote.com",
        creator_host="https://webapi.rednote.com",
        home_url="https://www.rednote.com",
        # Creator endpoints return an uploadAddr per request; this is only the fallback.
        upload_host="https://ros-upload.xiaohongshu.com",
        cookie_domain="rednote.com",
        login_url="https://www.rednote.com/login",
    ),
}


def _resolve_target() -> _Target:
    raw = os.environ.get("XHS_TARGET", "xiaohongshu").strip().lower()
    if not raw:
        raw = "xiaohongshu"
    if raw not in _TARGETS:
        valid = ", ".join(sorted(_TARGETS))
        raise ValueError(f"Unknown XHS_TARGET={raw!r}. Valid targets: {valid}")
    return _TARGETS[raw]


TARGET = _resolve_target()

EDITH_HOST = TARGET.edith_host
CREATOR_HOST = TARGET.creator_host
HOME_URL = TARGET.home_url
UPLOAD_HOST = TARGET.upload_host
COOKIE_DOMAIN = TARGET.cookie_domain
LOGIN_URL = TARGET.login_url

CHROME_VERSION = "145"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36"
)

SDK_VERSION = "4.2.6"
APP_ID = "xhs-pc-web"
PLATFORM = "macOS"

# Config directory — shared dir, target-namespaced cache files so xiaohongshu
# and rednote sessions can coexist on disk without overwriting each other.
CONFIG_DIR_NAME = ".xiaohongshu-cli"
_SUFFIX = "" if TARGET.name == "xiaohongshu" else f".{TARGET.name}"
COOKIE_FILE = f"cookies{_SUFFIX}.json"
TOKEN_CACHE_FILE = f"token_cache{_SUFFIX}.json"
INDEX_CACHE_FILE = f"index_cache{_SUFFIX}.json"
