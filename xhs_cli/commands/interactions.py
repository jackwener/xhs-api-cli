"""Interaction commands: like, collect, comment, reply."""

import click

from ..formatter import extract_note_id, maybe_print_structured, print_success
from ._common import exit_for_error, run_client_action, structured_output_options


@click.command()
@click.argument("id_or_url")
@click.option("--undo", is_flag=True, help="Unlike instead of like")
@structured_output_options
@click.pass_context
def like(ctx, id_or_url: str, undo: bool, as_json: bool, as_yaml: bool):
    """Like or unlike a note."""
    note_id = extract_note_id(id_or_url)

    try:
        action = (lambda client: client.unlike_note(note_id)) if undo else (lambda client: client.like_note(note_id))
        data = run_client_action(ctx, action)
        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"{'Unliked' if undo else 'Liked'} note {note_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("id_or_url")
@structured_output_options
@click.pass_context
def favorite(ctx, id_or_url: str, as_json: bool, as_yaml: bool):
    """Favorite (bookmark) a note."""
    note_id = extract_note_id(id_or_url)

    try:
        data = run_client_action(ctx, lambda client: client.favorite_note(note_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Favorited note {note_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("id_or_url")
@structured_output_options
@click.pass_context
def unfavorite(ctx, id_or_url: str, as_json: bool, as_yaml: bool):
    """Unfavorite (unbookmark) a note."""
    note_id = extract_note_id(id_or_url)

    try:
        data = run_client_action(ctx, lambda client: client.unfavorite_note(note_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Unfavorited note {note_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("id_or_url")
@click.option("--content", "-c", required=True, help="Comment content")
@structured_output_options
@click.pass_context
def comment(ctx, id_or_url: str, content: str, as_json: bool, as_yaml: bool):
    """Post a comment on a note."""
    note_id = extract_note_id(id_or_url)

    try:
        data = run_client_action(ctx, lambda client: client.post_comment(note_id, content))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Comment posted on {note_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("id_or_url")
@click.option("--comment-id", required=True, help="Target comment ID to reply to")
@click.option("--content", "-c", required=True, help="Reply content")
@structured_output_options
@click.pass_context
def reply(ctx, id_or_url: str, comment_id: str, content: str, as_json: bool, as_yaml: bool):
    """Reply to a specific comment."""
    note_id = extract_note_id(id_or_url)

    try:
        data = run_client_action(ctx, lambda client: client.reply_comment(note_id, comment_id, content))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Reply posted on comment {comment_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command("delete-comment")
@click.argument("note_id")
@click.argument("comment_id")
@structured_output_options
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_comment(ctx, note_id: str, comment_id: str, as_json: bool, as_yaml: bool, yes: bool):
    """Delete a comment you posted."""
    if not yes:
        click.confirm(f"Delete comment {comment_id} on note {note_id}?", abort=True)

    try:
        data = run_client_action(ctx, lambda client: client.delete_comment(note_id, comment_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Deleted comment {comment_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)
