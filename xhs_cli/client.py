"""
XHS API Client

Handles all HTTP requests to edith.xiaohongshu.com and creator.xiaohongshu.com
with proper signing, headers, and error handling.

Ported from: ~/readers/redbook/src/lib/client.ts
"""

import json
import logging
import random
import time
from typing import Any

import httpx

from .constants import CREATOR_HOST, EDITH_HOST, HOME_URL, UPLOAD_HOST, USER_AGENT
from .cookies import cookies_to_string
from .creator_signing import sign_creator
from .exceptions import (
    IpBlockedError,
    NeedVerifyError,
    SessionExpiredError,
    SignatureError,
    UnsupportedOperationError,
    XhsApiError,
)
from .signing import build_get_uri, sign_main_api

logger = logging.getLogger(__name__)


def _generate_search_id() -> str:
    """Generate a unique search ID (base36 of timestamp << 64 + random)."""
    e = int(time.time() * 1000) << 64
    t = random.randint(0, 2147483646)
    num = e + t

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return "0"
    result = ""
    while num > 0:
        result = alphabet[num % 36] + result
        num //= 36
    return result


class XhsClient:
    """Xiaohongshu API client with automatic signing."""

    def __init__(self, cookies: dict[str, str], timeout: float = 30.0):
        self.cookies = cookies
        self._http = httpx.Client(timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _base_headers(self) -> dict[str, str]:
        return {
            "user-agent": USER_AGENT,
            "content-type": "application/json",
            "cookie": cookies_to_string(self.cookies),
            "origin": HOME_URL,
            "referer": f"{HOME_URL}/",
        }

    def _handle_response(self, resp: httpx.Response) -> Any:
        """Handle API response, raising appropriate errors."""
        if resp.status_code in (461, 471):
            raise NeedVerifyError(
                verify_type=resp.headers.get("verifytype", "unknown"),
                verify_uuid=resp.headers.get("verifyuuid", "unknown"),
            )

        text = resp.text
        if not text:
            return None

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise XhsApiError(f"Non-JSON response: {text[:200]}") from None

        if data.get("success"):
            return data.get("data", data.get("success"))

        code = data.get("code")
        if code == 300012:
            raise IpBlockedError()
        if code == 300015:
            raise SignatureError()
        if code == -100:
            raise SessionExpiredError()

        raise XhsApiError(
            f"API error: {json.dumps(data)[:300]}",
            code=code,
            response=data,
        )

    # ─── Main API Methods ──────────────────────────────────────────────────

    def _main_api_get(
        self,
        uri: str,
        params: dict[str, str | int | list[str]] | None = None,
    ) -> Any:
        """GET request to edith.xiaohongshu.com with signing."""
        sign_headers = sign_main_api("GET", uri, self.cookies, params=params)
        full_uri = build_get_uri(uri, params)
        url = f"{EDITH_HOST}{full_uri}"

        logger.debug("GET %s", url)
        resp = self._http.get(url, headers={**self._base_headers(), **sign_headers})
        return self._handle_response(resp)

    def _main_api_post(
        self,
        uri: str,
        data: dict[str, Any],
        header_overrides: dict[str, str] | None = None,
    ) -> Any:
        """POST request to edith.xiaohongshu.com with signing."""
        sign_headers = sign_main_api("POST", uri, self.cookies, payload=data)
        url = f"{EDITH_HOST}{uri}"

        headers = {**self._base_headers(), **sign_headers}
        if header_overrides:
            headers.update(header_overrides)

        logger.debug("POST %s", url)
        resp = self._http.post(url, headers=headers, content=json.dumps(data, separators=(",", ":")))
        return self._handle_response(resp)

    # ─── Creator API Methods ───────────────────────────────────────────────

    def _creator_host(self, uri: str) -> str:
        return CREATOR_HOST if uri.startswith("/api/galaxy/") else EDITH_HOST

    def _creator_get(
        self,
        uri: str,
        params: dict[str, str | int] | None = None,
    ) -> Any:
        """GET request to creator API with signing."""
        api_str = f"url={uri}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            api_str = f"url={uri}?{qs}"

        sign = sign_creator(api_str, None, self.cookies["a1"])
        full_uri = f"{uri}?{'&'.join(f'{k}={v}' for k, v in params.items())}" if params else uri
        host = self._creator_host(uri)
        url = f"{host}{full_uri}"

        headers = {
            **self._base_headers(),
            "x-s": sign["x-s"],
            "x-t": sign["x-t"],
            "origin": CREATOR_HOST,
            "referer": f"{CREATOR_HOST}/",
        }

        logger.debug("Creator GET %s", url)
        resp = self._http.get(url, headers=headers)
        return self._handle_response(resp)

    def _creator_post(
        self,
        uri: str,
        data: dict[str, Any],
    ) -> Any:
        """POST request to creator API with signing."""
        sign = sign_creator(f"url={uri}", data, self.cookies["a1"])
        host = self._creator_host(uri)
        url = f"{host}{uri}"

        headers = {
            **self._base_headers(),
            "x-s": sign["x-s"],
            "x-t": sign["x-t"],
            "origin": CREATOR_HOST,
            "referer": f"{CREATOR_HOST}/",
        }

        logger.debug("Creator POST %s", url)
        resp = self._http.post(url, headers=headers, content=json.dumps(data, separators=(",", ":")))
        return self._handle_response(resp)

    # ─── Reading Endpoints ─────────────────────────────────────────────────

    def get_self_info(self) -> dict[str, Any]:
        """Get current user's profile info."""
        return self._main_api_get("/api/sns/web/v2/user/me")

    def get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get another user's profile info."""
        return self._main_api_get("/api/sns/web/v1/user/otherinfo", {
            "target_user_id": user_id,
        })

    def get_user_notes(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        """Get a user's published notes."""
        return self._main_api_get("/api/sns/web/v1/user_posted", {
            "num": 30,
            "cursor": cursor,
            "user_id": user_id,
            "image_scenes": "FD_WM_WEBP",
        })

    def search_notes(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "general",
        note_type: int = 0,
    ) -> Any:
        """
        Search notes by keyword.

        Args:
            keyword: Search query
            page: Page number
            page_size: Results per page
            sort: "general", "popularity_descending", "time_descending"
            note_type: 0=all, 1=video, 2=image
        """
        search_id = _generate_search_id()
        return self._main_api_post("/api/sns/web/v1/search/notes", {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "search_id": search_id,
            "sort": sort,
            "note_type": note_type,
        })

    def get_note_by_id(
        self,
        note_id: str,
        xsec_token: str = "",
        xsec_source: str = "pc_feed",
    ) -> Any:
        """Get note details by ID."""
        return self._main_api_post("/api/sns/web/v1/feed", {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": 1},
            "xsec_source": xsec_source,
            "xsec_token": xsec_token,
        })

    def get_home_feed(self, category: str = "homefeed_recommend") -> dict[str, Any]:
        """Get homepage recommendation feed."""
        return self._main_api_post("/api/sns/web/v1/homefeed", {
            "cursor_score": "",
            "num": 40,
            "refresh_type": 1,
            "note_index": 0,
            "unread_begin_note_id": "",
            "unread_end_note_id": "",
            "unread_note_count": 0,
            "category": category,
            "search_key": "",
            "need_num": 40,
            "image_scenes": ["FD_PRV_WEBP", "FD_WM_WEBP"],
        })

    def get_comments(
        self,
        note_id: str,
        cursor: str = "",
        xsec_token: str = "",
    ) -> Any:
        """Get comments for a note."""
        return self._main_api_get("/api/sns/web/v2/comment/page", {
            "note_id": note_id,
            "cursor": cursor,
            "image_formats": "jpg,webp,avif",
            "xsec_token": xsec_token,
        })

    def get_sub_comments(
        self,
        note_id: str,
        root_comment_id: str,
        num: int = 30,
        cursor: str = "",
    ) -> Any:
        """Get sub-comments (replies) for a comment."""
        return self._main_api_get("/api/sns/web/v2/comment/sub/page", {
            "note_id": note_id,
            "root_comment_id": root_comment_id,
            "num": num,
            "cursor": cursor,
        })

    # ─── Interaction Endpoints ──────────────────────────────────────────────

    def post_comment(self, note_id: str, content: str) -> dict[str, Any]:
        """Post a top-level comment on a note."""
        return self._main_api_post("/api/sns/web/v1/comment/post", {
            "note_id": note_id,
            "content": content,
            "at_users": [],
        })

    def reply_comment(
        self,
        note_id: str,
        target_comment_id: str,
        content: str,
    ) -> Any:
        """Reply to a specific comment."""
        return self._main_api_post("/api/sns/web/v1/comment/post", {
            "note_id": note_id,
            "content": content,
            "target_comment_id": target_comment_id,
            "at_users": [],
        })

    def like_note(self, note_id: str) -> dict[str, Any]:
        """Like a note."""
        return self._main_api_post("/api/sns/web/v1/note/like", {
            "note_oid": note_id,
        })

    def unlike_note(self, note_id: str) -> dict[str, Any]:
        """Unlike a note."""
        return self._main_api_post("/api/sns/web/v1/note/dislike", {
            "note_oid": note_id,
        })

    def favorite_note(self, note_id: str) -> dict[str, Any]:
        """Favorite (bookmark) a note."""
        return self._main_api_post("/api/sns/web/v1/note/collect", {
            "note_id": note_id,
        })

    def unfavorite_note(self, note_id: str) -> dict[str, Any]:
        """Unfavorite (unbookmark) a note."""
        return self._main_api_post("/api/sns/web/v1/note/uncollect", {
            "note_ids": note_id,
        })

    def delete_comment(self, note_id: str, comment_id: str) -> dict[str, Any]:
        """Delete a comment."""
        return self._main_api_post("/api/sns/web/v1/comment/delete", {
            "note_id": note_id,
            "comment_id": comment_id,
        })

    # ─── Creator/Posting Endpoints ────────────────────────────────────────

    def search_topics(self, keyword: str) -> dict[str, Any]:
        """Search for topics/hashtags."""
        return self._creator_post("/web_api/sns/v1/search/topic", {
            "keyword": keyword,
            "suggest_topic_request": {"title": "", "desc": ""},
            "page": {"page_size": 20, "page": 1},
        })

    def search_users(self, keyword: str) -> dict[str, Any]:
        """Search for users."""
        return self._creator_post("/web_api/sns/v1/search/user_info", {
            "keyword": keyword,
            "search_id": str(int(time.time() * 1000)),
            "page": {"page_size": 20, "page": 1},
        })

    def get_upload_permit(
        self,
        file_type: str = "image",
        count: int = 1,
    ) -> dict[str, str]:
        """Get upload permit for file upload."""
        data = self._creator_get("/api/media/v1/upload/web/permit", {
            "biz_name": "spectrum",
            "scene": file_type,
            "file_count": count,
            "version": 1,
            "source": "web",
        })

        permit = data["uploadTempPermits"][0]
        return {"fileId": permit["fileIds"][0], "token": permit["token"]}

    def upload_file(
        self,
        file_id: str,
        token: str,
        file_path: str,
        content_type: str = "image/jpeg",
    ) -> None:
        """Upload a file to XHS storage."""
        with open(file_path, "rb") as f:
            file_data = f.read()

        url = f"{UPLOAD_HOST}/{file_id}"
        resp = self._http.put(
            url,
            headers={
                "X-Cos-Security-Token": token,
                "Content-Type": content_type,
            },
            content=file_data,
        )

        if resp.status_code >= 400:
            raise XhsApiError(f"Upload failed: {resp.status_code} {resp.reason_phrase}")

    def create_image_note(
        self,
        title: str,
        desc: str,
        image_file_ids: list[str],
        topics: list[dict[str, str]] | None = None,
        is_private: bool = False,
    ) -> Any:
        """Create and publish an image note."""
        images = [{"file_id": fid, "metadata": {"source": -1}} for fid in image_file_ids]

        business_binds = {
            "version": 1,
            "noteId": 0,
            "noteOrderBind": {},
            "notePostTiming": {"postTime": None},
            "noteCollectionBind": {"id": ""},
        }

        data = {
            "common": {
                "type": "normal",
                "title": title,
                "note_id": "",
                "desc": desc,
                "source": '{"type":"web","ids":"","extraInfo":"{\\"subType\\":\\"official\\"}"}',
                "business_binds": json.dumps(business_binds),
                "ats": [],
                "hash_tag": topics or [],
                "post_loc": {},
                "privacy_info": {"op_type": 1, "type": 1 if is_private else 0},
            },
            "image_info": {"images": images},
            "video_info": None,
        }

        return self._main_api_post("/web_api/sns/v2/note", data, {
            "origin": CREATOR_HOST,
            "referer": f"{CREATOR_HOST}/",
        })

    def delete_note(self, note_id: str) -> dict[str, Any]:
        """Delete a note."""
        try:
            return self._creator_post("/api/galaxy/creator/note/delete", {
                "note_id": note_id,
            })
        except XhsApiError as exc:
            response = exc.response if isinstance(exc.response, dict) else {}
            if response.get("status") == 404 or "404" in str(exc):
                raise UnsupportedOperationError(
                    "Delete note is currently unavailable from the public web API. "
                    "The command remains experimental until the new endpoint is re-captured."
                ) from None
            raise

    def get_creator_note_list(self, tab: int = 0, page: int = 0) -> dict[str, Any]:
        """Get list of creator's own notes."""
        return self._creator_get("/api/galaxy/v2/creator/note/user/posted", {
            "tab": tab,
            "page": page,
        })

    # ─── P1: Social Graph Endpoints ───────────────────────────────────────

    def follow_user(self, user_id: str) -> dict[str, Any]:
        """Follow a user."""
        return self._main_api_post("/api/sns/web/v1/user/follow", {
            "target_user_id": user_id,
        })

    def unfollow_user(self, user_id: str) -> dict[str, Any]:
        """Unfollow a user."""
        return self._main_api_post("/api/sns/web/v1/user/unfollow", {
            "target_user_id": user_id,
        })

    # ─── P1: Discovery Endpoints ──────────────────────────────────────────

    def get_hot_feed(self, category: str = "homefeed.fashion_v3") -> dict[str, Any]:
        """Get hot/trending notes feed.

        Categories: homefeed.fashion_v3 (穿搭), homefeed.food_v3 (美食),
        homefeed.cosmetics_v3 (彩妆), homefeed.movie_and_tv_v3 (影视),
        homefeed.career_v3 (职场), homefeed.love_v3 (情感),
        homefeed.household_product_v3 (家居), homefeed.gaming_v3 (游戏),
        homefeed.travel_v3 (旅行), homefeed.fitness_v3 (健身)
        """
        return self.get_home_feed(category=category)

    # ─── P1: User Content Lists ───────────────────────────────────────────

    def get_user_favorites(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        """Get a user's favorited (bookmarked) notes."""
        return self._main_api_get("/api/sns/web/v2/note/collect/page", {
            "user_id": user_id,
            "cursor": cursor,
            "num": 30,
        })

    # ─── P1: Notification Endpoints (reverse-engineered) ─────────────────

    def get_unread_count(self) -> dict[str, Any]:
        """Get unread notification counts.

        Returns: {unread_count: int, likes: int, connections: int, mentions: int}
        """
        return self._main_api_get("/api/sns/web/unread_count", {})

    def get_notification_mentions(self, cursor: str = "", num: int = 20) -> dict[str, Any]:
        """Get comment and @mention notifications."""
        return self._main_api_get("/api/sns/web/v1/you/mentions", {
            "num": num,
            "cursor": cursor,
        })

    def get_notification_likes(self, cursor: str = "", num: int = 20) -> dict[str, Any]:
        """Get like and collect notifications."""
        return self._main_api_get("/api/sns/web/v1/you/likes", {
            "num": num,
            "cursor": cursor,
        })

    def get_notification_connections(self, cursor: str = "", num: int = 20) -> dict[str, Any]:
        """Get new follower notifications."""
        return self._main_api_get("/api/sns/web/v1/you/connections", {
            "num": num,
            "cursor": cursor,
        })

    # ─── HTML Fallback ────────────────────────────────────────────────────

    def get_note_from_html(self, note_id: str, xsec_token: str) -> dict[str, Any]:
        """Fallback: extract note data from HTML page's __INITIAL_STATE__."""
        import re

        url = f"{HOME_URL}/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_feed"
        resp = self._http.get(
            url,
            headers={
                "user-agent": USER_AGENT,
                "referer": f"{HOME_URL}/",
                "cookie": cookies_to_string(self.cookies),
            },
        )

        html = resp.text
        match = re.search(r'window\.__INITIAL_STATE__=({.*})</script>', html)
        if not match:
            raise XhsApiError("Could not parse __INITIAL_STATE__ from HTML")

        # Replace bare `undefined` values with JSON null
        state_str = re.sub(r'\bundefined\b', 'null', match.group(1))
        state = json.loads(state_str)

        detail_map = state.get("note", {}).get("noteDetailMap", {})
        if detail_map:
            entry = detail_map.get(note_id) or next(iter(detail_map.values()), None)
            if entry and "note" in entry:
                return entry["note"]

        raise XhsApiError("Note not found in HTML state")
