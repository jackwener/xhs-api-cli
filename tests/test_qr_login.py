"""Unit tests for QR code login flow."""

import pytest

from xhs_cli.exceptions import XhsApiError
from xhs_cli.qr_login import qrcode_login


class _FakeQrClient:
    instances = []

    def __init__(self, cookies, request_delay=0, **kwargs):
        self.cookies = dict(cookies)
        self.activate_calls = 0
        self.status_calls = 0
        self.create_seen_web_session = None
        self.status_seen_web_session = None
        self.activate_seen_web_sessions = []
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def login_activate(self):
        self.activate_calls += 1
        self.activate_seen_web_sessions.append(self.cookies.get("web_session"))
        if self.activate_calls == 1:
            return {"session": "guest-session", "secure_session": "guest-sec", "user_id": "guest-user"}
        return {"session": "real-session", "secure_session": "real-sec", "user_id": "real-user"}

    def create_qr_login(self):
        self.create_seen_web_session = self.cookies.get("web_session")
        return {"qr_id": "qr-1", "code": "code-1", "url": "https://example.com/qr"}

    def check_qr_status(self, qr_id, code):
        self.status_calls += 1
        self.status_seen_web_session = self.cookies.get("web_session")
        return {"codeStatus": 2, "userId": "real-user"}


class _MismatchQrClient(_FakeQrClient):
    def check_qr_status(self, qr_id, code):
        self.status_calls += 1
        self.status_seen_web_session = self.cookies.get("web_session")
        return {"codeStatus": 2, "userId": "another-user"}


def test_qrcode_login_carries_guest_session_into_followup_requests(monkeypatch):
    saved = []

    monkeypatch.setattr("xhs_cli.qr_login.XhsClient", _FakeQrClient)
    monkeypatch.setattr("xhs_cli.qr_login._generate_a1", lambda: "a1-fixed")
    monkeypatch.setattr("xhs_cli.qr_login._generate_webid", lambda: "webid-fixed")
    monkeypatch.setattr("xhs_cli.qr_login._display_qr_in_terminal", lambda data: True)
    monkeypatch.setattr("xhs_cli.qr_login.time.sleep", lambda seconds: None)
    monkeypatch.setattr("xhs_cli.qr_login.save_cookies", lambda cookies: saved.append(cookies))

    cookies = qrcode_login(timeout_s=1)
    client = _FakeQrClient.instances[-1]

    assert client.activate_seen_web_sessions == [None, "guest-session"]
    assert client.create_seen_web_session == "guest-session"
    assert client.status_seen_web_session == "guest-session"
    assert cookies == {
        "a1": "a1-fixed",
        "webId": "webid-fixed",
        "web_session": "real-session",
        "web_session_sec": "real-sec",
    }
    assert saved == [cookies]


def test_qrcode_login_rejects_mismatched_confirmed_user(monkeypatch):
    monkeypatch.setattr("xhs_cli.qr_login.XhsClient", _MismatchQrClient)
    monkeypatch.setattr("xhs_cli.qr_login._generate_a1", lambda: "a1-fixed")
    monkeypatch.setattr("xhs_cli.qr_login._generate_webid", lambda: "webid-fixed")
    monkeypatch.setattr("xhs_cli.qr_login._display_qr_in_terminal", lambda data: True)
    monkeypatch.setattr("xhs_cli.qr_login.time.sleep", lambda seconds: None)
    monkeypatch.setattr("xhs_cli.qr_login.save_cookies", lambda cookies: None)

    with pytest.raises(XhsApiError, match="different user"):
        qrcode_login(timeout_s=1)
