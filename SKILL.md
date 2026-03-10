---
name: xiaohongshu-cli
description: Use xiaohongshu-cli for ALL Xiaohongshu (Little Red Book, 小红书) operations — searching notes, reading content, browsing users, liking, collecting, commenting, following, and posting. Invoke whenever the user requests any Xiaohongshu interaction.
author: jackwener
version: "1.0.0"
tags:
  - xiaohongshu
  - xhs
  - redbook
  - 小红书
  - social-media
  - cli
---

# xiaohongshu-cli — Xiaohongshu CLI Tool

**Binary:** `xhs`
**Credentials:** browser cookies (auto-extracted via `--cookie-source`)

## Setup

```bash
pip install xiaohongshu-cli   # or: uv pip install xiaohongshu-cli
```

No explicit login needed — cookies are auto-extracted from Chrome.
Use `--cookie-source firefox` (or `edge`, `safari`, `brave`) to switch browser source.

Verify with:

```bash
xhs status
```

## Agent Defaults

All machine-readable output uses the envelope documented in [SCHEMA.md](./SCHEMA.md).
Payloads live under `.data`.

- Non-TTY stdout → auto YAML
- `--json` / `--yaml` → explicit format
- `OUTPUT=json` env → global override
- `OUTPUT=rich` env → force human output

## Commands

### Reading

| Command | Description | Example |
|---------|-------------|---------|
| `xhs search <keyword>` | Search notes | `xhs search "美食" --sort popular --type video` |
| `xhs read <id_or_url>` | Read a note | `xhs read abc123 --json` |
| `xhs comments <id_or_url>` | Get comments | `xhs comments abc123` |
| `xhs sub-comments <note_id> <comment_id>` | Get replies to comment | `xhs sub-comments abc 123` |
| `xhs user <user_id>` | View user profile | `xhs user 5f2e123` |
| `xhs user-posts <user_id>` | List user's notes | `xhs user-posts 5f2e123 --cursor ""` |
| `xhs feed` | Browse recommendation feed | `xhs feed --yaml` |
| `xhs hot` | Browse trending notes | `xhs hot -c food` |
| `xhs topics <keyword>` | Search topics/hashtags | `xhs topics "旅行"` |
| `xhs search-user <keyword>` | Search users | `xhs search-user "摄影"` |
| `xhs my-notes` | List own published notes | `xhs my-notes --page 0` |
| `xhs notifications` | View notifications | `xhs notifications --type likes` |
| `xhs unread` | Show unread counts | `xhs unread --json` |

### Interactions (Write)

| Command | Description | Example |
|---------|-------------|---------|
| `xhs like <id_or_url>` | Like a note | `xhs like abc123` |
| `xhs like <id_or_url> --undo` | Unlike a note | `xhs like abc123 --undo` |
| `xhs favorite <id_or_url>` | Bookmark a note | `xhs favorite abc123` |
| `xhs unfavorite <id_or_url>` | Remove bookmark | `xhs unfavorite abc123` |
| `xhs comment <id_or_url> -c "text"` | Post a comment | `xhs comment abc123 -c "好看！"` |
| `xhs reply <id_or_url> --comment-id ID -c "text"` | Reply to comment | `xhs reply abc123 --comment-id 456 -c "谢谢"` |
| `xhs delete-comment <note_id> <comment_id>` | Delete own comment | `xhs delete-comment abc 123 -y` |

### Social

| Command | Description | Example |
|---------|-------------|---------|
| `xhs follow <user_id>` | Follow a user | `xhs follow 5f2e123` |
| `xhs unfollow <user_id>` | Unfollow a user | `xhs unfollow 5f2e123` |
| `xhs favorites` | List your collected notes | `xhs favorites --json` |

### Creator

| Command | Description | Example |
|---------|-------------|---------|
| `xhs post --title "..." --body "..." --images img.png` | Publish a note | `xhs post --title "Test" --body "Hello"` |
| `xhs delete <id_or_url>` | Delete own note | `xhs delete abc123 -y` |

### Account

| Command | Description |
|---------|-------------|
| `xhs login` | Verify and display cookie status |
| `xhs status` | Check authentication status |
| `xhs logout` | Clear cached cookies |
| `xhs whoami` | Show current user profile |

## Agent Workflow Examples

### Search → Read → Like pipeline

```bash
NOTE_ID=$(xhs search "美食推荐" --json | jq -r '.data.items[0].id')
xhs read "$NOTE_ID" --json | jq '.data'
xhs like "$NOTE_ID"
```

### Browse trending food notes

```bash
xhs hot -c food --json | jq '.data.items[:5] | .[].note_card | {title, likes: .interact_info.liked_count}'
```

### Get user info then follow

```bash
xhs user 5f2e123 --json | jq '.data.basic_info | {nickname, user_id}'
xhs follow 5f2e123
```

### Check notifications

```bash
xhs unread --json | jq '.data'
xhs notifications --type mentions --json | jq '.data.message_list[:5]'
```

## Hot Categories

Available for `xhs hot -c <category>`:
`fashion`, `food`, `cosmetics`, `movie`, `career`, `love`, `home`, `gaming`, `travel`, `fitness`

## Error Codes

Structured error codes returned in the `error.code` field:
- `not_authenticated` — cookies expired or missing
- `verification_required` — captcha/verification needed
- `ip_blocked` — IP rate limited
- `signature_error` — request signing failed
- `api_error` — upstream API error
- `unsupported_operation` — operation not available
