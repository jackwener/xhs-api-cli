"""Creator commands: post, delete."""

import click

from ..formatter import extract_note_id, maybe_print_structured, print_info, print_success
from ._common import exit_for_error, run_client_action


@click.command()
@click.option("--title", required=True, help="Note title")
@click.option("--body", required=True, help="Note body text")
@click.option("--images", required=True, multiple=True, help="Image file path(s)")
@click.option("--topic", default=None, help="Topic/hashtag to search and attach")
@click.option("--private", "is_private", is_flag=True, help="Publish as private note")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.pass_context
def post(
    ctx,
    title: str,
    body: str,
    images: tuple[str, ...],
    topic: str | None,
    is_private: bool,
    as_json: bool,
    as_yaml: bool,
):
    """Publish an image note."""
    try:
        def _publish(client):
            file_ids = []
            for img_path in images:
                print_info(f"Uploading {img_path}...")
                permit = client.get_upload_permit()
                client.upload_file(permit["fileId"], permit["token"], img_path)
                file_ids.append(permit["fileId"])
                print_success(f"Uploaded: {img_path}")

            topics = []
            if topic:
                topic_data = client.search_topics(topic)
                topic_list = topic_data if isinstance(topic_data, list) else topic_data.get("topic_info_dtos", [])
                if topic_list:
                    first = topic_list[0]
                    topics.append({
                        "id": first.get("id", ""),
                        "name": first.get("name", topic),
                        "type": "topic",
                    })

            return client.create_image_note(
                title=title,
                desc=body,
                image_file_ids=file_ids,
                topics=topics,
                is_private=is_private,
            )

        data = run_client_action(ctx, _publish)
        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Note published: {title}" + (" (private)" if is_private else ""))

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)


@click.command("delete")
@click.argument("id_or_url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--yaml", "as_yaml", is_flag=True, help="Output as YAML")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx, id_or_url: str, as_json: bool, as_yaml: bool, yes: bool):
    """Delete a note. Experimental: the public web endpoint is unstable."""
    note_id = extract_note_id(id_or_url)

    if not yes:
        click.confirm(f"Delete note {note_id}?", abort=True)

    try:
        data = run_client_action(ctx, lambda client: client.delete_note(note_id))

        if not maybe_print_structured(data, as_json=as_json, as_yaml=as_yaml):
            print_success(f"Deleted note {note_id}")

    except Exception as exc:
        exit_for_error(exc, as_json=as_json, as_yaml=as_yaml)
