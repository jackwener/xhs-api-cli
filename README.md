# xhs-api-cli

小红书 CLI — 通过逆向 API 在终端操作小红书 📕

## 推荐项目

- [bilibili-cli](https://github.com/jackwener/bilibili-cli) — Bilibili CLI
- [twitter-cli](https://github.com/jackwener/twitter-cli) — Twitter/X CLI

## Features

- 🔐 **Auth** — auto-extract browser cookies, whoami
- 🔍 **Search** — notes by keyword, user search, topic search
- 📖 **Reading** — note detail, comments, sub-comments, user profiles
- 📰 **Feed** — recommendation feed, hot/trending by category
- 👥 **Social** — followers, following, follow/unfollow
- 👍 **Interactions** — like, collect, comment, reply, delete
- ✍️ **Creator** — post image notes, delete notes, my-notes list
- 🔔 **Notifications** — likes, comments, follows, mentions
- 📊 **JSON output** — all commands support `--json` for scripting

## Installation

```bash
# From source
git clone git@github.com:jackwener/xhs-api-cli.git
cd xhs-api-cli
uv sync

# Or: pip install
pip install -e .
```

## Usage

```bash
# ─── Auth ─────────────────────────────────────────
xhs login                             # Extract cookies from browser
xhs status                            # Check login status
xhs whoami                            # Detailed profile (fans, likes, etc)
xhs whoami --json                     # Raw JSON
xhs logout                            # Clear saved cookies

# ─── Search ───────────────────────────────────────
xhs search "美食"                      # Search notes
xhs search "旅行" --sort popular       # Sort: general, popular, latest
xhs search "穿搭" --type video         # Filter: all, video, image
xhs search "AI" --page 2              # Pagination
xhs search-user "用户名"               # Search users
xhs topics "美食"                      # Search hashtags/topics

# ─── Reading ──────────────────────────────────────
xhs read <note_id>                     # Read a note
xhs read https://xiaohongshu.com/...   # Read by URL
xhs comments <note_id>                 # View comments
xhs sub-comments <note_id> <cmt_id>   # View replies to a comment
xhs user <user_id>                     # User profile
xhs user-posts <user_id>              # User's published notes
xhs user-posts <user_id> --cursor X   # Paginate with cursor

# ─── Feed & Discovery ────────────────────────────
xhs feed                              # Recommendation feed
xhs hot                               # Hot notes (default: food)
xhs hot -c fashion                    # Categories: fashion, food, cosmetics,
                                      #   movie, career, love, home, gaming,
                                      #   travel, fitness

# ─── Social ───────────────────────────────────────
xhs user-collects <user_id>           # User's bookmarks ✅
xhs followers <user_id>               # ⚠️ experimental
xhs following <user_id>               # ⚠️ experimental
xhs follow <user_id>                  # ⚠️ experimental
xhs unfollow <user_id>                # ⚠️ experimental
xhs user-likes <user_id>              # ⚠️ experimental

# ─── Interactions ─────────────────────────────────
xhs like <note_id>                     # Like a note
xhs like <note_id> --undo             # Unlike
xhs collect <note_id>                  # Collect (bookmark)
xhs collect <note_id> --undo          # Uncollect
xhs comment <note_id> -c "好赞！"     # Post comment
xhs reply <note_id> --comment-id X -c "回复"  # Reply to comment
xhs delete-comment <note_id> <cmt_id> # Delete own comment

# ─── Creator ─────────────────────────────────────
xhs my-notes                           # List own notes
xhs my-notes --page 1                 # Next page
xhs post --title "标题" --body "正文" --images img.jpg  # Post note
xhs delete <note_id>                   # Delete note
xhs delete <note_id> -y               # Skip confirmation

# ─── Notifications ────────────────────────────────
xhs notifications                      # ⚠️ experimental
xhs notifications --type comments     # ⚠️ experimental
```

> **⚠️ Experimental commands**: `followers`, `following`, `follow`, `unfollow`, `user-likes`, `notifications` — XHS web API 可能未公开这些端点，需要浏览器抓包获取正确路径后才能使用。

## Authentication

xhs-api-cli uses a 2-tier authentication strategy:

1. **Saved cookies** — loads from `~/.xhs-api-cli/cookies.json`
2. **Browser cookies** — auto-extracts from Chrome, Firefox, Safari, Edge, Brave

Cookies are validated on use. Most commands require authentication. Use `--cookie-source` to specify browser (default: chrome).

## Development

```bash
# Run tests
.venv/bin/python -m pytest tests/ -v

# Unit tests only (no network)
.venv/bin/python -m pytest tests/ -v --ignore=tests/test_integration.py

# Integration tests (need cookies)
.venv/bin/python -m pytest tests/test_integration.py -v
```

## License

Apache-2.0
