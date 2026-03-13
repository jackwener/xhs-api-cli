"""Integration smoke tests for xiaohongshu-cli.

These tests invoke the real CLI commands with ``--yaml`` against the live
Xiaohongshu API using your local browser cookies.  They are **skipped by
default** and only run when explicitly requested::

    uv run pytest -m smoke -v

Only read-only operations are tested — no writes.
"""

from __future__ import annotations

import pytest
import yaml
from click.testing import CliRunner

from xhs_cli.cli import cli

smoke = pytest.mark.smoke

runner = CliRunner()


def _invoke(*args: str):
    """Run a CLI command with --yaml and return parsed payload."""
    result = runner.invoke(cli, [*args, "--yaml"])
    if result.output:
        payload = yaml.safe_load(result.output)
    else:
        payload = None
    return result, payload


def _pick_note_reference(payload: dict) -> tuple[str, str]:
    """Extract ``(note_id, xsec_token)`` from a search/feed payload."""
    data = payload["data"]
    items = data.get("items", [])
    if not items:
        pytest.skip("No note items available in payload")

    first = items[0]
    note_card = first.get("note_card", {})
    note_id = first.get("id", note_card.get("note_id", ""))
    xsec_token = first.get("xsec_token", note_card.get("xsec_token", ""))
    if not note_id:
        pytest.skip("No note_id found in payload")
    return note_id, xsec_token


# ── Auth ────────────────────────────────────────────────────────────────


@smoke
class TestAuth:
    """Verify authentication is working end-to-end."""

    def test_status(self):
        result, payload = _invoke("status")
        assert result.exit_code == 0, f"status failed: {result.output}"
        assert payload["ok"] is True
        assert payload["data"]["authenticated"] is True

    def test_whoami(self):
        result, payload = _invoke("whoami")
        assert result.exit_code == 0, f"whoami failed: {result.output}"
        assert payload["ok"] is True


# ── Read-only queries ───────────────────────────────────────────────────


@smoke
class TestReadOnly:
    """Read-only CLI smoke tests."""

    def test_search(self):
        result, payload = _invoke("search", "美食")
        assert result.exit_code == 0, f"search failed: {result.output}"
        assert payload["ok"] is True

    def test_feed(self):
        result, payload = _invoke("feed")
        assert result.exit_code == 0, f"feed failed: {result.output}"
        assert payload["ok"] is True

    def test_hot(self):
        result, payload = _invoke("hot", "-c", "food")
        assert result.exit_code == 0, f"hot failed: {result.output}"
        assert payload["ok"] is True

    def test_topics(self):
        result, payload = _invoke("topics", "旅行")
        assert result.exit_code == 0, f"topics failed: {result.output}"
        assert payload["ok"] is True

    def test_search_feed_read_roundtrip(self):
        search_result, search_payload = _invoke("search", "黑丝")
        assert search_result.exit_code == 0, f"search 黑丝 failed: {search_result.output}"
        assert search_payload["ok"] is True
        search_note_id, search_xsec_token = _pick_note_reference(search_payload)

        first_read_result, first_read_payload = _invoke(
            "read",
            search_note_id,
            "--xsec-token",
            search_xsec_token,
        )
        assert first_read_result.exit_code == 0, f"first read failed: {first_read_result.output}"
        assert first_read_payload["ok"] is True

        feed_result, feed_payload = _invoke("feed")
        assert feed_result.exit_code == 0, f"feed failed: {feed_result.output}"
        assert feed_payload["ok"] is True
        feed_note_id, feed_xsec_token = _pick_note_reference(feed_payload)

        feed_read_result, feed_read_payload = _invoke(
            "read",
            feed_note_id,
            "--xsec-token",
            feed_xsec_token,
        )
        assert feed_read_result.exit_code == 0, f"feed read failed: {feed_read_result.output}"
        assert feed_read_payload["ok"] is True

        second_read_result, second_read_payload = _invoke("read", search_note_id)
        assert second_read_result.exit_code == 0, f"second read failed: {second_read_result.output}"
        assert second_read_payload["ok"] is True

    def test_search_then_comments(self):
        search_result, search_payload = _invoke("search", "黑丝")
        assert search_result.exit_code == 0, f"search 黑丝 failed: {search_result.output}"
        assert search_payload["ok"] is True
        note_id, xsec_token = _pick_note_reference(search_payload)

        comments_result, comments_payload = _invoke(
            "comments",
            note_id,
            "--xsec-token",
            xsec_token,
        )
        assert comments_result.exit_code == 0, f"comments after search failed: {comments_result.output}"
        assert comments_payload["ok"] is True

    def test_feed_comments_reread_same_note(self):
        feed_result, feed_payload = _invoke("feed")
        assert feed_result.exit_code == 0, f"feed failed: {feed_result.output}"
        assert feed_payload["ok"] is True
        note_id, xsec_token = _pick_note_reference(feed_payload)

        comments_result, comments_payload = _invoke(
            "comments",
            note_id,
            "--xsec-token",
            xsec_token,
        )
        assert comments_result.exit_code == 0, f"comments after feed failed: {comments_result.output}"
        assert comments_payload["ok"] is True

        reread_result, reread_payload = _invoke("read", note_id)
        assert reread_result.exit_code == 0, f"reread after comments failed: {reread_result.output}"
        assert reread_payload["ok"] is True

    def test_search_read_comments_feed_read_reread(self):
        search_result, search_payload = _invoke("search", "黑丝")
        assert search_result.exit_code == 0, f"search 黑丝 failed: {search_result.output}"
        assert search_payload["ok"] is True
        search_note_id, search_xsec_token = _pick_note_reference(search_payload)

        read_result, read_payload = _invoke(
            "read",
            search_note_id,
            "--xsec-token",
            search_xsec_token,
        )
        assert read_result.exit_code == 0, f"search read failed: {read_result.output}"
        assert read_payload["ok"] is True

        comments_result, comments_payload = _invoke("comments", search_note_id)
        assert comments_result.exit_code == 0, f"comments after read failed: {comments_result.output}"
        assert comments_payload["ok"] is True

        feed_result, feed_payload = _invoke("feed")
        assert feed_result.exit_code == 0, f"feed failed: {feed_result.output}"
        assert feed_payload["ok"] is True
        feed_note_id, feed_xsec_token = _pick_note_reference(feed_payload)

        feed_read_result, feed_read_payload = _invoke(
            "read",
            feed_note_id,
            "--xsec-token",
            feed_xsec_token,
        )
        assert feed_read_result.exit_code == 0, f"feed read failed: {feed_read_result.output}"
        assert feed_read_payload["ok"] is True

        reread_result, reread_payload = _invoke("read", search_note_id)
        assert reread_result.exit_code == 0, f"final reread failed: {reread_result.output}"
        assert reread_payload["ok"] is True

    def test_short_index_search_read_comments_roundtrip(self):
        search_result, search_payload = _invoke("search", "黑丝")
        assert search_result.exit_code == 0, f"search 黑丝 failed: {search_result.output}"
        assert search_payload["ok"] is True

        read_result, read_payload = _invoke("read", "1")
        assert read_result.exit_code == 0, f"read by short index failed: {read_result.output}"
        assert read_payload["ok"] is True

        comments_result, comments_payload = _invoke("comments", "1")
        assert comments_result.exit_code == 0, f"comments by short index failed: {comments_result.output}"
        assert comments_payload["ok"] is True
