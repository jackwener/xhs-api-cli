"""Interaction commands: like, collect, comment, reply."""

import click

from ..exceptions import NoCookieError, XhsApiError
from ..formatter import extract_note_id, maybe_print_structured, print_error, print_success
from ._common import get_client as _get_client


@click.command()
@click.argument("id_or_url")
@click.option("--undo", is_flag=True, help="Unlike instead of like")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def like(ctx, id_or_url: str, undo: bool, as_json: bool, as_yaml: bool):
    """Like or unlike a note."""
    note_id = extract_note_id(id_or_url)

    try:
        with _get_client(ctx) as client:
            if undo:
                data = client.unlike_note(note_id)
                if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
                    print_success(f"Unliked note {note_id}")
            else:
                data = client.like_note(note_id)
                if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
                    print_success(f"Liked note {note_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("id_or_url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def favorite(ctx, id_or_url: str, as_json: bool, as_yaml: bool):
    """Favorite (bookmark) a note."""
    note_id = extract_note_id(id_or_url)

    try:
        with _get_client(ctx) as client:
            data = client.favorite_note(note_id)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Favorited note {note_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("id_or_url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def unfavorite(ctx, id_or_url: str, as_json: bool, as_yaml: bool):
    """Unfavorite (unbookmark) a note."""
    note_id = extract_note_id(id_or_url)

    try:
        with _get_client(ctx) as client:
            data = client.unfavorite_note(note_id)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Unfavorited note {note_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("id_or_url")
@click.option("--content", "-c", required=True, help="Comment content")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def comment(ctx, id_or_url: str, content: str, as_json: bool, as_yaml: bool):
    """Post a comment on a note."""
    note_id = extract_note_id(id_or_url)

    try:
        with _get_client(ctx) as client:
            data = client.post_comment(note_id, content)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Comment posted on {note_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command()
@click.argument("id_or_url")
@click.option("--comment-id", required=True, help="Target comment ID to reply to")
@click.option("--content", "-c", required=True, help="Reply content")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def reply(ctx, id_or_url: str, comment_id: str, content: str, as_json: bool, as_yaml: bool):
    """Reply to a specific comment."""
    note_id = extract_note_id(id_or_url)

    try:
        with _get_client(ctx) as client:
            data = client.reply_comment(note_id, comment_id, content)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Reply posted on comment {comment_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None


@click.command("delete-comment")
@click.argument("note_id")
@click.argument("comment_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_comment(ctx, note_id: str, comment_id: str, as_json: bool, as_yaml: bool, yes: bool):
    """Delete a comment you posted."""
    if not yes:
        click.confirm(f"Delete comment {comment_id} on note {note_id}?", abort=True)

    try:
        with _get_client(ctx) as client:
            data = client.delete_comment(note_id, comment_id)

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Deleted comment {comment_id}")

    except (NoCookieError, XhsApiError) as e:
        print_error(str(e))
        raise SystemExit(1) from None
