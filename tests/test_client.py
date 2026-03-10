"""Unit tests for XHS client request payloads and endpoint selection."""

import pytest

from xhs_cli.client import XhsClient
from xhs_cli.exceptions import UnsupportedOperationError, XhsApiError


class TestFavorites:
    def test_unfavorite_uses_note_ids_payload(self, monkeypatch):
        captured = {}

        def fake_post(self, uri, data, header_overrides=None):
            captured["uri"] = uri
            captured["data"] = data
            return True

        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            client.unfavorite_note("note-123")
        finally:
            client.close()

        assert captured["uri"] == "/api/sns/web/v1/note/uncollect"
        assert captured["data"] == {"note_ids": "note-123"}


class TestCreatorEndpoints:
    def test_creator_note_list_uses_v2_endpoint(self, monkeypatch):
        captured = {}

        def fake_get(self, uri, params=None):
            captured["uri"] = uri
            captured["params"] = params
            return {"notes": [], "page": -1}

        monkeypatch.setattr(XhsClient, "_creator_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_creator_note_list(page=2)
        finally:
            client.close()

        assert result["page"] == -1
        assert captured["uri"] == "/api/galaxy/v2/creator/note/user/posted"
        assert captured["params"] == {"tab": 0, "page": 2}

    def test_delete_note_raises_unsupported_for_404(self, monkeypatch):
        def fake_post(self, uri, data):
            raise XhsApiError(
                "API error: {\"status\": 404}",
                response={"status": 404},
            )

        monkeypatch.setattr(XhsClient, "_creator_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="Delete note is currently unavailable"):
                client.delete_note("note-123")
        finally:
            client.close()
