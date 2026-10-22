# Discord Post Agents

A multi-agent system built with LangGraph. Pick a post type, answer a few questions, and it proposes
angles, you pick one, it writes the post, a reviewer checks it, you approve, and it sends a styled
card (an embed) to your Discord channel.

```
choose type -> your answers -> ideas -> picker (you) -> writer -> reviewer
                                                          ^          |
                                                          └─ rewrite ┘  (max 2 reviews)
                                                                     |
                                                                 approval (you) -> publish -> END
```

## Post types

| Type | Use it for | Reviewer |
|---|---|---|
| Achievement | Sharing something you did | Strict: every number and claim must come from your answers |
| Announcement or event | Telling the server about an event or news | Strict. Dates show in each member's own timezone |
| Discussion question | Starting a conversation | Light: tone, no invented statistics |
| Free post | Any message: you type the main points, it polishes them | Light |

Add a new type by adding one entry to `MODES` in `modes.py`. Nothing else needs to change.

## The agents

| Step | Job |
|---|---|
| `ideas` | Proposes 3 angles that fit the post type |
| `picker` | You choose one (human step) |
| `writer` | Writes the post using only your answers, plus a short card headline |
| `reviewer` | Code checks length (and numbers in strict types); the LLM checks quality and, in strict types, every claim |
| `approval` | You see the card preview and say yes or no (human step) |
| `publish` | Plain code, no LLM. Builds the card and sends it to your webhook |

The card's fields (What I did, Result, When, Where, Link) are copied straight from what you typed,
so the AI can never change those details.

## Setup

```bash
uv sync
cp .env.example .env    # Windows PowerShell: copy .env.example .env
uv run main.py
```

Fill in `GOOGLE_API_KEY`, your name and your role in `.env` first. Set `TIMEZONE` (for example
`Asia/Kolkata`) so announcement dates are read correctly.

`DRY_RUN=true` is the default: the whole flow runs and shows the card, but nothing is sent.

## Announcement dates

Type the date as `YYYY-MM-DD HH:MM` in your own timezone, for example `2026-11-05 18:00`.
The card shows it as a Discord timestamp, so every member sees it in their local time,
with a live "in 3 days" countdown. Dates in the past are rejected.

## Get a Discord webhook (about 2 minutes)

1. Make a Discord server (or use one you already have).
2. Right-click a channel, then Edit Channel, Integrations, Webhooks, New Webhook.
3. Click Copy Webhook URL and paste it into `.env` as `DISCORD_WEBHOOK_URL`.
4. Set `DRY_RUN=false` when you want cards to really go out.

Treat the webhook URL like a password. If it leaks, delete the webhook and make a new one.

## Setting up your server (no code)

- Create channels like `#achievements` and `#announcements`.
- Make them read-only for members, so only your webhook posts there.
- Create an invite link and set it to never expire. Share that link, or use
  right-click, Copy Message Link on a single card to share one post.
- Remember: people have to join the server to read the channel.

## Your writing style (optional)

Create `voice.txt` and paste 2-3 of your past posts in it. The writer will copy that style.

## Safety choices

- Nothing is sent without your typed "yes".
- `DRY_RUN` is on by default.
- The writer may only use your answers. In strict types the reviewer blocks numbers that are not in
  your answers and flags unsupported or exaggerated claims.
- The publish step has no retry, so a failure can never send twice.
- `@everyone`, `@here` and role pings are blocked even if the text contains them.

## Switching platforms later

Only `agents/publisher.py` talks to Discord. To post somewhere else (LinkedIn, Telegram, Bluesky),
replace that one file. The other agents don't change.
