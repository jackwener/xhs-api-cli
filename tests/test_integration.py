"""
Integration tests for XHS API client.

These tests require actual XHS cookies (a logged-in browser session).
They test against the real XHS API to verify the complete signing + request pipeline.

Run with: uv run pytest tests/test_integration.py -v
Skip if no cookies available.

Write operations are tested as self-cleaning PAIRS:
  - like + unlike → net effect = zero
  - favorite + unfavorite → net effect = zero
  - comment + delete-comment → net effect = zero
  The undo operation always runs in a `finally` block.
"""

import time

import pytest

from xhs_cli.client import XhsClient
from xhs_cli.cookies import get_cookies
from xhs_cli.exceptions import NoCookieError, SessionExpiredError, XhsApiError


def _get_test_cookies():
    """Try to get valid cookies for integration testing."""
    try:
        cookies = get_cookies("chrome")
        with XhsClient(cookies) as client:
            client.get_self_info()
        return cookies
    except SessionExpiredError:
        try:
            cookies = get_cookies("chrome", force_refresh=True)
            with XhsClient(cookies) as client:
                client.get_self_info()
            return cookies
        except (NoCookieError, SessionExpiredError, XhsApiError, Exception):
            return None
    except (NoCookieError, Exception):
        return None


# Skip all integration tests if no valid cookies are available
cookies = _get_test_cookies()
pytestmark = pytest.mark.skipif(cookies is None, reason="No valid XHS cookies available for integration testing")

# Cached values (discovered once, reused across tests)
_CACHED_NOTE_ID = None
_CACHED_XSEC_TOKEN = None
_CACHED_USER_ID = None
_CACHED_OTHER_USER_ID = None


def _ensure_test_note(client: XhsClient) -> tuple[str, str]:
    """Discover a note ID from search results for testing. Cached across tests."""
    global _CACHED_NOTE_ID, _CACHED_XSEC_TOKEN
    if _CACHED_NOTE_ID:
        return _CACHED_NOTE_ID, _CACHED_XSEC_TOKEN or ""

    search_data = client.search_notes("美食")
    items = search_data.get("items", [])
    if not items:
        pytest.skip("No search results available for testing")

    _CACHED_NOTE_ID = items[0].get("id", "")
    _CACHED_XSEC_TOKEN = items[0].get("xsec_token", "")
    if not _CACHED_NOTE_ID:
        pytest.skip("No note ID in search results")

    return _CACHED_NOTE_ID, _CACHED_XSEC_TOKEN or ""


def _ensure_self_user_id(client: XhsClient) -> str:
    """Get current user's ID. Cached across tests."""
    global _CACHED_USER_ID
    if _CACHED_USER_ID:
        return _CACHED_USER_ID

    info = client.get_self_info()
    _CACHED_USER_ID = info.get("user_id", "")
    if not _CACHED_USER_ID:
        pytest.skip("Cannot determine current user ID")

    return _CACHED_USER_ID


def _ensure_other_user_id(client: XhsClient) -> str:
    """Find another user ID for safe follow/unfollow testing."""
    global _CACHED_OTHER_USER_ID
    if _CACHED_OTHER_USER_ID:
        return _CACHED_OTHER_USER_ID

    self_user_id = _ensure_self_user_id(client)
    data = client.search_users("美食达人")
    users = data.get("user_info_dtos", []) if isinstance(data, dict) else []
    for item in users:
        user_id = item.get("user_base_dto", {}).get("user_id", "")
        if user_id and user_id != self_user_id:
            _CACHED_OTHER_USER_ID = user_id
            return user_id

    pytest.skip("No other user found for follow/unfollow testing")


@pytest.fixture
def client():
    """Create a test client with real cookies."""
    assert cookies is not None
    c = XhsClient(cookies)
    yield c
    c.close()


# ─── Auth ────────────────────────────────────────────────────────────────────


class TestAuth:
    """Test authentication and user info."""

    def test_get_self_info(self, client: XhsClient):
        info = client.get_self_info()
        assert isinstance(info, dict)
        assert any(k in info for k in ["nickname", "red_id", "user_id"])

    def test_cookies_have_a1(self):
        assert cookies is not None
        assert "a1" in cookies
        assert len(cookies["a1"]) > 0


# ─── Search ──────────────────────────────────────────────────────────────────


class TestSearch:
    """Test search functionality."""

    def test_search_notes(self, client: XhsClient):
        data = client.search_notes("美食", page=1)
        items = data.get("items", [])
        assert len(items) > 0

    def test_search_with_sort(self, client: XhsClient):
        time.sleep(1)
        data = client.search_notes("旅行", sort="popularity_descending")
        assert data is not None

    def test_search_returns_note_cards(self, client: XhsClient):
        time.sleep(1)
        data = client.search_notes("咖啡")
        items = data.get("items", [])
        if items:
            first = items[0]
            assert "note_card" in first or "model_type" in first

    def test_search_users(self, client: XhsClient):
        """Search for users by keyword."""
        time.sleep(1)
        data = client.search_users("美食达人")
        assert data is not None

    def test_search_topics(self, client: XhsClient):
        time.sleep(1)
        data = client.search_topics("美食")
        assert data is not None


# ─── Feed ────────────────────────────────────────────────────────────────────


class TestFeed:
    """Test feed functionality."""

    def test_get_home_feed(self, client: XhsClient):
        time.sleep(1)
        data = client.get_home_feed()
        items = data.get("items", [])
        assert len(items) > 0

    def test_feed_items_have_structure(self, client: XhsClient):
        time.sleep(1)
        data = client.get_home_feed()
        items = data.get("items", [])
        if items:
            assert "note_card" in items[0] or "id" in items[0]

    def test_hot_feed(self, client: XhsClient):
        """Hot/trending feed by category."""
        time.sleep(1)
        data = client.get_hot_feed("homefeed.food_v3")
        items = data.get("items", [])
        assert len(items) > 0


# ─── Note Reading ────────────────────────────────────────────────────────────


class TestNoteRead:
    """Test reading individual notes."""

    def test_read_note(self, client: XhsClient):
        time.sleep(1)
        note_id, xsec_token = _ensure_test_note(client)
        time.sleep(1)
        data = client.get_note_by_id(note_id, xsec_token=xsec_token)
        assert data is not None

    def test_get_comments(self, client: XhsClient):
        time.sleep(1)
        note_id, xsec_token = _ensure_test_note(client)
        time.sleep(1)
        data = client.get_comments(note_id, xsec_token=xsec_token)
        assert data is not None


# ─── User Content ────────────────────────────────────────────────────────────


class TestUserContent:
    """Test user content queries."""

    def test_get_user_info(self, client: XhsClient):
        time.sleep(1)
        user_id = _ensure_self_user_id(client)
        data = client.get_user_info(user_id)
        assert isinstance(data, dict)

    def test_get_user_notes(self, client: XhsClient):
        time.sleep(1)
        user_id = _ensure_self_user_id(client)
        data = client.get_user_notes(user_id)
        assert data is not None

    def test_get_user_favorites(self, client: XhsClient):
        time.sleep(1)
        user_id = _ensure_self_user_id(client)
        data = client.get_user_favorites(user_id)
        assert data is not None

    def test_get_creator_note_list(self, client: XhsClient):
        time.sleep(1)
        data = client.get_creator_note_list()
        assert data is not None
        assert "notes" in data
        assert "page" in data


# ─── Notifications ───────────────────────────────────────────────────────────


class TestNotifications:
    """Test notification endpoints (reverse-engineered)."""

    def test_unread_count(self, client: XhsClient):
        time.sleep(1)
        data = client.get_unread_count()
        assert isinstance(data, dict)

    def test_notification_mentions(self, client: XhsClient):
        time.sleep(1)
        data = client.get_notification_mentions()
        assert data is not None

    def test_notification_likes(self, client: XhsClient):
        time.sleep(1)
        data = client.get_notification_likes()
        assert data is not None

    def test_notification_connections(self, client: XhsClient):
        time.sleep(1)
        data = client.get_notification_connections()
        assert data is not None


# ─── Paired Write Tests (self-cleaning) ──────────────────────────────────────


class TestLikePair:
    """like + unlike → net effect = zero."""

    def test_like_then_unlike(self, client: XhsClient):
        time.sleep(1)
        note_id, _ = _ensure_test_note(client)

        time.sleep(1)
        try:
            result = client.like_note(note_id)
            assert result is not None or result is True
        finally:
            time.sleep(1)
            try:
                client.unlike_note(note_id)
            except XhsApiError:
                pass  # Best effort cleanup


class TestFavoritePair:
    """favorite + unfavorite → net effect = zero."""

    def test_favorite_then_unfavorite(self, client: XhsClient):
        time.sleep(1)
        note_id, _ = _ensure_test_note(client)

        time.sleep(1)
        try:
            result = client.favorite_note(note_id)
            assert result is not None or result is True
        finally:
            time.sleep(1)
            try:
                client.unfavorite_note(note_id)
            except XhsApiError:
                pass  # Best effort cleanup


class TestCommentPair:
    """comment + delete-comment → net effect = zero."""

    def test_comment_then_delete(self, client: XhsClient):
        time.sleep(1)
        note_id, _ = _ensure_test_note(client)

        time.sleep(1)
        comment_data = client.post_comment(note_id, "🤖 Integration test — will delete shortly")
        assert comment_data is not None

        # Extract comment ID from response
        comment_id = ""
        if isinstance(comment_data, dict):
            comment_id = (
                comment_data.get("comment", {}).get("id", "")
                or comment_data.get("id", "")
                or comment_data.get("comment_id", "")
            )

        try:
            assert comment_id, f"Should get comment ID back, got: {comment_data}"
        finally:
            if comment_id:
                time.sleep(1)
                try:
                    client.delete_comment(note_id, comment_id)
                except XhsApiError:
                    pass  # Best effort cleanup


# ─── End-to-End Workflows ────────────────────────────────────────────────────


class TestEndToEnd:
    """Full workflow tests combining multiple operations."""

    def test_search_read_comments_workflow(self, client: XhsClient):
        """search → read note → get comments."""
        time.sleep(1)
        result = client.search_notes("Python编程")
        items = result.get("items", [])
        if not items:
            pytest.skip("No search results")

        first = items[0]
        note_id = first.get("id", "")
        xsec_token = first.get("xsec_token", "")
        assert note_id

        time.sleep(1)
        note = client.get_note_by_id(note_id, xsec_token=xsec_token)
        assert note is not None

        time.sleep(1)
        comments = client.get_comments(note_id, xsec_token=xsec_token)
        assert comments is not None

    def test_like_favorite_workflow(self, client: XhsClient):
        """Like + favorite → unfavorite + unlike. Full interaction lifecycle."""
        time.sleep(1)
        note_id, _ = _ensure_test_note(client)

        liked = False
        favorited = False

        try:
            time.sleep(1)
            client.like_note(note_id)
            liked = True

            time.sleep(1)
            client.favorite_note(note_id)
            favorited = True
        finally:
            if favorited:
                time.sleep(1)
                try:
                    client.unfavorite_note(note_id)
                except XhsApiError:
                    pass
            if liked:
                time.sleep(1)
                try:
                    client.unlike_note(note_id)
                except XhsApiError:
                    pass


class TestFollowPair:
    """follow + unfollow → net effect = zero."""

    def test_follow_then_unfollow(self, client: XhsClient):
        time.sleep(1)
        user_id = _ensure_other_user_id(client)

        time.sleep(1)
        followed = False
        try:
            result = client.follow_user(user_id)
            followed = True
            assert isinstance(result, dict)
            assert result.get("fstatus") in {"follows", "followed"}
        finally:
            if followed:
                time.sleep(1)
                try:
                    undo = client.unfollow_user(user_id)
                    assert isinstance(undo, dict)
                    assert undo.get("fstatus") in {"none", "unfollowed"}
                except XhsApiError:
                    pass

    def test_notifications_workflow(self, client: XhsClient):
        """unread → mentions → likes → connections."""
        time.sleep(1)
        unread = client.get_unread_count()
        assert isinstance(unread, dict)

        time.sleep(1)
        assert client.get_notification_mentions(num=5) is not None

        time.sleep(1)
        assert client.get_notification_likes(num=5) is not None

        time.sleep(1)
        assert client.get_notification_connections(num=5) is not None
