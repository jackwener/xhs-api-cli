# xiaohongshu-cli

小红书 CLI — 通过逆向 API 在终端操作小红书 📕

## 推荐项目

- [bilibili-cli](https://github.com/jackwener/bilibili-cli) — Bilibili CLI
- [twitter-cli](https://github.com/jackwener/twitter-cli) — Twitter/X CLI

## Features

- 🔐 **Auth** — auto-extract browser cookies, status, whoami
- 🔍 **Search** — notes by keyword, user search, topic search
- 📖 **Reading** — note detail, comments, sub-comments, user profiles
- 📰 **Feed** — recommendation feed, hot/trending by category
- 👥 **Social** — follow/unfollow, favorites
- 👍 **Interactions** — like, favorite, comment, reply, delete
- ✍️ **Creator** — post image notes, delete notes, my-notes list
- 🔔 **Notifications** — unread count, mentions, likes, new followers
- 📊 **Structured output** — commands support `--yaml` and `--json`; non-TTY stdout defaults to YAML

## Installation

```bash
# From source
git clone git@github.com:jackwener/xiaohongshu-cli.git
cd xiaohongshu-cli
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
xhs favorites <user_id>                # User's bookmarked notes
xhs follow <user_id>                  # Follow a user
xhs unfollow <user_id>                # Unfollow a user

# ─── Interactions ─────────────────────────────────
xhs like <note_id>                     # Like a note
xhs like <note_id> --undo             # Unlike
xhs favorite <note_id>                 # Favorite (bookmark)
xhs unfavorite <note_id>               # Unfavorite
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
xhs unread                             # Unread counts (likes, mentions, follows)
xhs notifications                      # 评论和@ notifications
xhs notifications --type likes        # 赞和收藏 notifications
xhs notifications --type connections   # 新增关注 notifications
```

## Authentication

xiaohongshu-cli uses a 2-tier authentication strategy:

1. **Saved cookies** — loads from `~/.xiaohongshu-cli/cookies.json`
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
