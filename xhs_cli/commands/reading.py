"""Reading commands: search, read, comments, sub-comments, user, user-posts, feed, topics, search-user, my-notes."""

import click

from ..formatter import (
    console,
    maybe_print_structured,
    parse_note_url,
    print_info,
    render_comments,
    render_creator_notes,
    render_feed,
    render_note,
    render_notifications,
    render_search_results,
    render_topics,
    render_user_info,
    render_user_posts,
    render_users,
)
from ._common import exit_for_error, run_client_action, structured_output_options

# ─── Sort mapping ────────────────────────────────────────────────────────────

SORT_MAP = {
    "general": "general",
    "popular": "popularity_descending",
    "latest": "time_descending",
}

TYPE_MAP = {
    "all": 0,
    "video": 1,
    "image": 2,
}


@click.command()
@click.argument("keyword")
@click.option("--sort", type=click.Choice(["general", "popular", "latest"]), default="general", help="Sort order")
@click.option("--type", "note_type", type=click.Choice(["all", "video", "image"]), default="all", help="Note type")
@click.option("--page", default=1, help="Page number")
@structured_output_options
@click.pass_context
def search(ctx, keyword: str, sort: str, note_type: str, page: int, as_json: bool, as_yaml: bool):
    """Search notes by keyword."""
    try:
        data = run_client_action(
            ctx,
            lambda client: client.search_notes(
                keyword=keyword,
                page=page,
                sort=SORT_MAP[sort],
                note_type=TYPE_MAP[note_type],
            ),
        )

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_search_results(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("id_or_url")
@click.option("--xsec-token", default="", help="Security token (auto-resolved if cached)")
@structured_output_options
@click.pass_context
def read(ctx, id_or_url: str, xsec_token: str, as_json: bool, as_yaml: bool):
    """Read a note by ID or URL."""
    note_id, url_token = parse_note_url(id_or_url)
    # --xsec-token flag overrides; otherwise use token from URL
    token = xsec_token or url_token

    try:
        data = run_client_action(ctx, lambda client: client.get_note_by_id(note_id, xsec_token=token))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_note(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("id_or_url")
@click.option("--cursor", default="", help="Pagination cursor")
@click.option("--xsec-token", default="", help="Security token")
@click.option("--all", "fetch_all", is_flag=True, help="Auto-paginate to fetch ALL comments")
@structured_output_options
@click.pass_context
def comments(ctx, id_or_url: str, cursor: str, xsec_token: str, fetch_all: bool, as_json: bool, as_yaml: bool):
    """View comments on a note. Use --all to fetch all pages."""
    note_id, url_token = parse_note_url(id_or_url)
    token = xsec_token or url_token

    try:
        if fetch_all:
            data = run_client_action(
                ctx,
                lambda client: client.get_all_comments(note_id, xsec_token=token),
            )
        else:
            data = run_client_action(
                ctx,
                lambda client: client.get_comments(note_id, cursor=cursor, xsec_token=token),
            )

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_comments(data)
            if fetch_all and isinstance(data, dict):
                total = data.get('total_fetched', 0)
                pages = data.get('pages_fetched', 0)
                print_info(f"Fetched {total} comments across {pages} pages")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("user_id")
@structured_output_options
@click.pass_context
def user(ctx, user_id: str, as_json: bool, as_yaml: bool):
    """View user profile info."""
    try:
        data = run_client_action(ctx, lambda client: client.get_user_info(user_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_user_info(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command("user-posts")
@click.argument("user_id")
@click.option("--cursor", default="", help="Pagination cursor")
@structured_output_options
@click.pass_context
def user_posts(ctx, user_id: str, cursor: str, as_json: bool, as_yaml: bool):
    """List a user's published notes."""
    try:
        data = run_client_action(ctx, lambda client: client.get_user_notes(user_id, cursor=cursor))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            notes = data.get("notes", [])
            render_user_posts(notes)
            if data.get("has_more"):
                cursor = data.get("cursor", "")
                print_info(f"More notes available — use --cursor {cursor}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@structured_output_options
@click.pass_context
def feed(ctx, as_json: bool, as_yaml: bool):
    """Browse the recommendation feed."""
    try:
        data = run_client_action(ctx, lambda client: client.get_home_feed())

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_feed(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("keyword")
@structured_output_options
@click.pass_context
def topics(ctx, keyword: str, as_json: bool, as_yaml: bool):
    """Search for topics/hashtags."""
    try:
        data = run_client_action(ctx, lambda client: client.search_topics(keyword))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_topics(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command("sub-comments")
@click.argument("note_id")
@click.argument("comment_id")
@click.option("--cursor", default="", help="Pagination cursor")
@structured_output_options
@click.pass_context
def sub_comments(ctx, note_id: str, comment_id: str, cursor: str, as_json: bool, as_yaml: bool):
    """View replies to a specific comment."""
    try:
        data = run_client_action(ctx, lambda client: client.get_sub_comments(note_id, comment_id, cursor=cursor))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_comments(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command("search-user")
@click.argument("keyword")
@structured_output_options
@click.pass_context
def search_user(ctx, keyword: str, as_json: bool, as_yaml: bool):
    """Search for users by keyword."""
    try:
        data = run_client_action(ctx, lambda client: client.search_users(keyword))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_users(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command("my-notes")
@click.option("--page", default=0, help="Page number (0-indexed)")
@structured_output_options
@click.pass_context
def my_notes(ctx, page: int, as_json: bool, as_yaml: bool):
    """List your own published notes."""
    try:
        data = run_client_action(ctx, lambda client: client.get_creator_note_list(page=page))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_creator_notes(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


HOT_CATEGORIES = {
    "fashion": "homefeed.fashion_v3",
    "food": "homefeed.food_v3",
    "cosmetics": "homefeed.cosmetics_v3",
    "movie": "homefeed.movie_and_tv_v3",
    "career": "homefeed.career_v3",
    "love": "homefeed.love_v3",
    "home": "homefeed.household_product_v3",
    "gaming": "homefeed.gaming_v3",
    "travel": "homefeed.travel_v3",
    "fitness": "homefeed.fitness_v3",
}


@click.command()
@click.option(
    "--category", "-c",
    type=click.Choice(list(HOT_CATEGORIES.keys())),
    default="food",
    help="Category (fashion, food, cosmetics, movie, career, love, home, gaming, travel, fitness)",
)
@structured_output_options
@click.pass_context
def hot(ctx, category: str, as_json: bool, as_yaml: bool):
    """Browse hot/trending notes by category."""
    try:
        data = run_client_action(ctx, lambda client: client.get_hot_feed(HOT_CATEGORIES[category]))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_feed(data)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.option(
    "--type", "notif_type",
    type=click.Choice(["mentions", "likes", "connections"]),
    default="mentions",
    help="Notification type: mentions (评论和@), likes (赞和收藏), connections (新增关注)",
)
@click.option("--cursor", default="", help="Pagination cursor")
@click.option("--num", default=20, help="Number of items per page")
@structured_output_options
@click.pass_context
def notifications(ctx, notif_type: str, cursor: str, num: int, as_json: bool, as_yaml: bool):
    """View notifications (mentions, likes, connections)."""
    try:
        def _load_notifications(client):
            if notif_type == "mentions":
                return client.get_notification_mentions(cursor=cursor, num=num)
            if notif_type == "likes":
                return client.get_notification_likes(cursor=cursor, num=num)
            return client.get_notification_connections(cursor=cursor, num=num)

        data = run_client_action(ctx, _load_notifications)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            render_notifications(data, notif_type)

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@structured_output_options
@click.pass_context
def unread(ctx, as_json: bool, as_yaml: bool):
    """Show unread notification counts."""
    try:
        data = run_client_action(ctx, lambda client: client.get_unread_count())

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            mentions = data.get("mentions", 0)
            likes = data.get("likes", 0)
            connections = data.get("connections", 0)
            total = data.get("unread_count", 0)
            console.print(f"📬 未读通知: [bold]{total}[/bold]")
            console.print(f"   💬 评论和@: {mentions}")
            console.print(f"   ❤️ 赞和收藏: {likes}")
            console.print(f"   👥 新增关注: {connections}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)
