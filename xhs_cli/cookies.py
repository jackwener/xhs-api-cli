"""Cookie extraction and management for XHS API client."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable

from .constants import CONFIG_DIR_NAME, COOKIE_FILE

logger = logging.getLogger(__name__)

BrowserLoader = Callable[..., object]
SUPPORTED_BROWSERS: dict[str, str] = {
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "edge",
    "safari": "safari",
    "brave": "brave",
}


def get_config_dir() -> Path:
    """Get or create config directory."""
    config_dir = Path.home() / CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cookie_path() -> Path:
    """Get cookie file path."""
    return get_config_dir() / COOKIE_FILE


def load_saved_cookies() -> dict[str, str] | None:
    """Load cookies from local storage."""
    cookie_path = get_cookie_path()
    if not cookie_path.exists():
        return None
    try:
        data = json.loads(cookie_path.read_text())
        if data.get("a1"):
            logger.debug("Loaded saved cookies from %s", cookie_path)
            return data
    except (OSError, json.JSONDecodeError) as e:
        logger.debug("Failed to load saved cookies: %s", e)
    return None


def save_cookies(cookies: dict[str, str]) -> None:
    """Save cookies to local storage with restricted permissions."""
    cookie_path = get_cookie_path()
    cookie_path.write_text(json.dumps(cookies, indent=2))
    cookie_path.chmod(0o600)
    logger.debug("Saved cookies to %s", cookie_path)


def clear_cookies() -> None:
    """Remove saved cookies."""
    cookie_path = get_cookie_path()
    if cookie_path.exists():
        cookie_path.unlink()
        logger.debug("Cleared cookies from %s", cookie_path)


def _browser_loaders() -> dict[str, BrowserLoader]:
    import browser_cookie3 as bc3

    return {
        "chrome": bc3.chrome,
        "firefox": bc3.firefox,
        "edge": bc3.edge,
        "safari": bc3.safari,
        "brave": bc3.brave,
    }


def _extract_in_process(source: str) -> dict[str, str] | None:
    """Extract cookies in-process for macOS Keychain compatibility."""
    try:
        loader = _browser_loaders().get(source)
    except ImportError:
        logger.debug("browser_cookie3 not installed, skipping in-process extraction")
        return None

    if loader is None:
        logger.debug("Unsupported browser source: %s", source)
        return None

    try:
        jar = loader(domain_name=".xiaohongshu.com")
    except Exception as exc:
        logger.debug("%s in-process extraction failed: %s", source, exc)
        return None

    cookies = {cookie.name: cookie.value for cookie in jar if "xiaohongshu.com" in (cookie.domain or "")}
    if cookies.get("a1"):
        logger.debug("Loaded XHS cookies from %s in-process", source)
        return cookies

    logger.debug("No usable a1 cookie found in %s in-process extraction", source)
    return None


def _extract_via_subprocess(source: str) -> dict[str, str] | None:
    """Extract cookies via subprocess to avoid browser SQLite locks."""
    extract_script = '''
import json, sys
try:
    import browser_cookie3 as bc3
except ImportError:
    print(json.dumps({"error": "browser-cookie3 not installed"}))
    sys.exit(0)

browsers = {
    "chrome": bc3.chrome,
    "firefox": bc3.firefox,
    "edge": bc3.edge,
    "safari": bc3.safari,
    "brave": bc3.brave,
}

source = sys.argv[1]
loader = browsers.get(source)
if not loader:
    print(json.dumps({"error": f"Unknown browser: {source}"}))
    sys.exit(0)

try:
    cj = loader(domain_name=".xiaohongshu.com")
    cookies = {c.name: c.value for c in cj if "xiaohongshu.com" in (c.domain or "")}
    if cookies.get("a1"):
        print(json.dumps({"browser": source, "cookies": cookies}))
    else:
        print(json.dumps({"error": "no_a1_cookie"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
'''

    try:
        result = subprocess.run(
            [sys.executable, "-c", extract_script, source],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode != 0:
            logger.debug("Cookie extraction subprocess failed: %s", result.stderr)
            return None

        data = json.loads(result.stdout.strip())
        if "error" in data:
            logger.debug("Cookie extraction error: %s", data["error"])
            return None

        return data["cookies"]

    except subprocess.TimeoutExpired:
        logger.debug("Cookie extraction timed out")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.debug("Cookie extraction parse error: %s", e)
        return None


def extract_browser_cookies(source: str = "chrome") -> dict[str, str] | None:
    """
    Extract XHS cookies from browser using browser-cookie3.

    macOS requires an in-process attempt for Keychain-backed browsers; when that
    fails we fall back to a subprocess to avoid SQLite DB locks.
    """
    cookies = _extract_in_process(source)
    if cookies:
        return cookies
    return _extract_via_subprocess(source)


def get_cookies(cookie_source: str = "chrome", *, force_refresh: bool = False) -> dict[str, str]:
    """
    Multi-strategy cookie acquisition.

    1. Load saved cookies
    2. Extract from browser
    3. Raise error if all fail
    """
    # 1. Try saved cookies first
    if not force_refresh:
        saved = load_saved_cookies()
        if saved:
            return saved

    # 2. Try browser extraction
    from .exceptions import NoCookieError

    extracted = extract_browser_cookies(cookie_source)
    if extracted:
        save_cookies(extracted)
        return extracted

    raise NoCookieError(cookie_source)


def cookies_to_string(cookies: dict[str, str]) -> str:
    """Format cookies as a cookie header string."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())
