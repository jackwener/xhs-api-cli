"""Common helpers for CLI commands."""

from __future__ import annotations

from typing import Callable, TypeVar

from ..client import XhsClient
from ..cookies import get_cookies
from ..exceptions import (
    IpBlockedError,
    NeedVerifyError,
    NoCookieError,
    SessionExpiredError,
    SignatureError,
    UnsupportedOperationError,
    XhsApiError,
)
from ..formatter import emit_error, print_error

T = TypeVar("T")


def _cookie_source(ctx) -> str:
    return ctx.obj.get("cookie_source", "chrome") if ctx.obj else "chrome"


def get_client(ctx, *, force_refresh: bool = False) -> XhsClient:
    """Get an XhsClient from the click context."""
    cookies = get_cookies(_cookie_source(ctx), force_refresh=force_refresh)
    return XhsClient(cookies)


def run_client_action(ctx, action: Callable[[XhsClient], T]) -> T:
    """Run an authenticated client action and retry once with fresh browser cookies."""
    try:
        with get_client(ctx) as client:
            return action(client)
    except SessionExpiredError as exc:
        try:
            with get_client(ctx, force_refresh=True) as client:
                return action(client)
        except NoCookieError:
            raise exc from None


def error_code_for_exception(exc: Exception) -> str:
    """Map domain exceptions to stable structured error codes."""
    if isinstance(exc, (NoCookieError, SessionExpiredError)):
        return "not_authenticated"
    if isinstance(exc, NeedVerifyError):
        return "verification_required"
    if isinstance(exc, IpBlockedError):
        return "ip_blocked"
    if isinstance(exc, SignatureError):
        return "signature_error"
    if isinstance(exc, UnsupportedOperationError):
        return "unsupported_operation"
    if isinstance(exc, XhsApiError):
        return "api_error"
    return "unknown_error"


def exit_for_error(
    exc: Exception,
    *,
    as_json: bool,
    as_yaml: bool,
    prefix: str | None = None,
) -> None:
    """Emit a structured/non-structured error and terminate the command."""
    message = str(exc)
    if prefix:
        message = f"{prefix}: {message}"

    if emit_error(error_code_for_exception(exc), message, as_json=as_json, as_yaml=as_yaml):
        raise SystemExit(1) from None

    print_error(message)
    raise SystemExit(1) from None
