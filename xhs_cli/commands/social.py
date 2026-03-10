"""Social commands: follow, unfollow, user-collects."""

import click

from ..exceptions import NoCookieError, XhsApiError
from ..formatter import maybe_print_structured, print_error, print_info, print_success
from ._common import get_client as _get_client


@click.command()
@click.argument("user_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def follow(ctx, user_id: str, as_json: bool, as_yaml: bool):
    """Follow a user."""
    try:
        with _get_client(ctx) as client:
            data = client.follow_user(user_id)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Followed user {user_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("user_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def unfollow(ctx, user_id: str, as_json: bool, as_yaml: bool):
    """Unfollow a user."""
    try:
        with _get_client(ctx) as client:
            data = client.unfollow_user(user_id)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Unfollowed user {user_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("user_id")
@click.option("--cursor", default="", help="Pagination cursor")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def favorites(ctx, user_id: str, cursor: str, as_json: bool, as_yaml: bool):
    """List a user's favorited (bookmarked) notes."""
    try:
        with _get_client(ctx) as client:
            data = client.get_user_favorites(user_id, cursor=cursor)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            from ..formatter import render_user_posts
            notes = data.get("notes", []) if isinstance(data, dict) else []
            render_user_posts(notes)
            if isinstance(data, dict) and data.get("has_more"):
                print_info(f"More notes — use --cursor {data.get('cursor', '')}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None
