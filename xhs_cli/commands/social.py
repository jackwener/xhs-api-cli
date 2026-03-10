"""Social commands: follow, unfollow, user-collects."""

import click

from ..formatter import maybe_print_structured, print_info, print_success
from ._common import structured_output_options, exit_for_error, run_client_action


@click.command()
@click.argument("user_id")
@structured_output_options
@click.pass_context
def follow(ctx, user_id: str, as_json: bool, as_yaml: bool):
    """Follow a user."""
    try:
        data = run_client_action(ctx, lambda client: client.follow_user(user_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Followed user {user_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("user_id")
@structured_output_options
@click.pass_context
def unfollow(ctx, user_id: str, as_json: bool, as_yaml: bool):
    """Unfollow a user."""
    try:
        data = run_client_action(ctx, lambda client: client.unfollow_user(user_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Unfollowed user {user_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("user_id")
@click.option("--cursor", default="", help="Pagination cursor")
@structured_output_options
@click.pass_context
def favorites(ctx, user_id: str, cursor: str, as_json: bool, as_yaml: bool):
    """List a user's favorited (bookmarked) notes."""
    try:
        data = run_client_action(ctx, lambda client: client.get_user_favorites(user_id, cursor=cursor))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            from ..formatter import render_user_posts
            notes = data.get("notes", []) if isinstance(data, dict) else []
            render_user_posts(notes)
            if isinstance(data, dict) and data.get("has_more"):
                print_info(f"More notes — use --cursor {data.get('cursor', '')}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)
