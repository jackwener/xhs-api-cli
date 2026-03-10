"""Authentication commands: login, status, logout."""

import click

from ..client import XhsClient
from ..cookies import clear_cookies, get_cookies
from ..exceptions import NoCookieError, XhsApiError
from ..formatter import (
    console,
    maybe_print_structured,
    print_error,
    print_success,
    render_user_info,
)


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def login(ctx, as_json: bool, as_yaml: bool):
    """Log in by extracting cookies from browser."""
    cookie_source = ctx.obj.get("cookie_source", "chrome") if ctx.obj else "chrome"
    try:
        cookies = get_cookies(cookie_source)
        print_success(f"Cookies extracted from {cookie_source}")

        # Verify by fetching user info
        with XhsClient(cookies) as client:
            info = client.get_self_info()

        if not maybe_print_structured(info, as_json=as_json, as_yaml=as_yaml):
            nickname = info.get("nickname", "Unknown")
            red_id = info.get("red_id", "")
            print_success(f"Logged in as: {nickname} (ID: {red_id})")

    except NoCookieError as e:
        print_error(str(e))
        raise SystemExit(1) from None
    except XhsApiError as e:
        print_error(f"Login verification failed: {e}")
        raise SystemExit(1) from None


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def status(ctx, as_json: bool, as_yaml: bool):
    """Check current login status and user info."""
    cookie_source = ctx.obj.get("cookie_source", "chrome") if ctx.obj else "chrome"
    try:
        cookies = get_cookies(cookie_source)
        with XhsClient(cookies) as client:
            info = client.get_self_info()

        if not maybe_print_structured(info, as_json=as_json, as_yaml=as_yaml):
            nickname = info.get("nickname", "Unknown")
            red_id = info.get("red_id", "")
            ip_location = info.get("ip_location", "")
            desc = info.get("desc", "")

            console.print("[bold green]✓ Logged in[/bold green]")
            console.print(f"  昵称: [bold]{nickname}[/bold]")
            if red_id:
                console.print(f"  小红书号: {red_id}")
            if ip_location:
                console.print(f"  IP 属地: {ip_location}")
            if desc:
                console.print(f"  简介: {desc}")

    except NoCookieError:
        print_error("Not logged in. Run: xhs login")
        raise SystemExit(1) from None
    except XhsApiError as e:
        print_error(f"Status check failed: {e}")
        raise SystemExit(1) from None


@click.command()
def logout():
    """Clear saved cookies and log out."""
    clear_cookies()
    print_success("Logged out — cookies cleared")


@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def whoami(ctx, as_json: bool, as_yaml: bool):
    """Show detailed profile of current user (level, fans, likes)."""
    cookie_source = ctx.obj.get("cookie_source", "chrome") if ctx.obj else "chrome"
    try:
        cookies = get_cookies(cookie_source)
        with XhsClient(cookies) as client:
            info = client.get_self_info()

        if not maybe_print_structured(info, as_json=as_json, as_yaml=as_yaml):
            render_user_info(info)

    except NoCookieError:
        print_error("Not logged in. Run: xhs login")
        raise SystemExit(1) from None
    except XhsApiError as e:
        print_error(f"Failed to get profile: {e}")
        raise SystemExit(1) from None
