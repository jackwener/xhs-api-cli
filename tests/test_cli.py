"""Tests for CLI commands using Click's test runner."""

import yaml
from click.testing import CliRunner

from xhs_cli.cli import cli

runner = CliRunner()


class TestCliBasic:
    """Test CLI basics without requiring cookies."""

    def test_version(self):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "xhs" in result.output
        assert "search" in result.output
        assert "read" in result.output

    def test_search_help(self):
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "keyword" in result.output.lower() or "KEYWORD" in result.output

    def test_read_help(self):
        result = runner.invoke(cli, ["read", "--help"])
        assert result.exit_code == 0

    def test_login_help(self):
        result = runner.invoke(cli, ["login", "--help"])
        assert result.exit_code == 0

    def test_status_help(self):
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_all_commands_registered(self):
        result = runner.invoke(cli, ["--help"])
        commands_expected = [
            # Auth
            "login", "status", "logout", "whoami",
            # Reading
            "search", "read", "comments", "sub-comments", "user", "user-posts",
            "feed", "hot", "topics", "search-user", "my-notes",
            "notifications", "unread",
            # Interactions
            "like", "favorite", "unfavorite", "comment", "reply", "delete-comment",
            # Social
            "follow", "unfollow", "favorites",
            # Creator
            "post", "delete",
        ]
        for cmd in commands_expected:
            assert cmd in result.output, f"Command '{cmd}' not found in CLI help"

    def test_whoami_help(self):
        result = runner.invoke(cli, ["whoami", "--help"])
        assert result.exit_code == 0

    def test_hot_help(self):
        result = runner.invoke(cli, ["hot", "--help"])
        assert result.exit_code == 0
        assert "category" in result.output.lower()

    def test_unread_help(self):
        result = runner.invoke(cli, ["unread", "--help"])
        assert result.exit_code == 0

    def test_my_notes_help(self):
        result = runner.invoke(cli, ["my-notes", "--help"])
        assert result.exit_code == 0

    def test_status_auto_yaml_when_stdout_is_not_tty(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "auto")

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def get_self_info(self):
                return {"nickname": "Alice", "red_id": "alice001"}

        monkeypatch.setattr("xhs_cli.commands.auth.get_cookies", lambda source: {"a1": "cookie"})
        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["nickname"] == "Alice"
