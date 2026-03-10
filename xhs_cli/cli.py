"""CLI entry point for xiaohongshu-cli.

Usage:
    xhs login / status / logout
    xhs search <keyword> [--sort popular|latest] [--type video|image] [--page N]
    xhs read <id_or_url> [--xsec-token TOKEN]
    xhs comments <id_or_url>
    xhs user <user_id>
    xhs user-posts <user_id> [--cursor CURSOR]
    xhs feed
    xhs topics <keyword>
    xhs like <id_or_url> [--undo]
    xhs collect <id_or_url> [--undo]
    xhs comment <id_or_url> --content "..."
    xhs reply <id_or_url> --comment-id ID --content "..."
    xhs post --title "..." --body "..." --images img.png
    xhs delete <id_or_url> [-y]
"""

from __future__ import annotations

import logging

import click

from . import __version__
from .commands import auth, creator, interactions, reading, social


@click.group()
@click.version_option(version=__version__, prog_name="xhs")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--cookie-source",
    type=click.Choice(["chrome", "firefox", "edge", "safari", "brave"]),
    default="chrome",
    show_default=True,
    help="Browser to read cookies from",
)
@click.pass_context
def cli(ctx, verbose: bool, cookie_source: str):
    """xhs — Xiaohongshu CLI via reverse-engineered API 📕"""
    ctx.ensure_object(dict)
    ctx.obj["cookie_source"] = cookie_source

    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)


# ─── Auth commands ───────────────────────────────────────────────────────────

cli.add_command(auth.login)
cli.add_command(auth.status)
cli.add_command(auth.logout)
cli.add_command(auth.whoami)

# ─── Reading commands ────────────────────────────────────────────────────────

cli.add_command(reading.search)
cli.add_command(reading.read)
cli.add_command(reading.comments)
cli.add_command(reading.sub_comments)
cli.add_command(reading.user)
cli.add_command(reading.user_posts)
cli.add_command(reading.feed)
cli.add_command(reading.hot)
cli.add_command(reading.topics)
cli.add_command(reading.search_user)
cli.add_command(reading.my_notes)
cli.add_command(reading.notifications)
cli.add_command(reading.unread)

# ─── Interaction commands ────────────────────────────────────────────────────

cli.add_command(interactions.like)
cli.add_command(interactions.favorite)
cli.add_command(interactions.unfavorite)
cli.add_command(interactions.comment)
cli.add_command(interactions.reply)
cli.add_command(interactions.delete_comment)

# ─── Social commands ────────────────────────────────────────────────────────

cli.add_command(social.follow)
cli.add_command(social.unfollow)
cli.add_command(social.favorites)

# ─── Creator commands ───────────────────────────────────────────────────────

cli.add_command(creator.post)
cli.add_command(creator.delete)


if __name__ == "__main__":
    cli()
