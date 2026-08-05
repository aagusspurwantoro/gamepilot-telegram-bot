# GamePilot Telegram Bot

A Telegram bot built with [aiogram 3](https://docs.aiogram.dev/) — calculator, Black Desert Online market tax calculator, and copy-paste helpers for pilot workflows.

## Commands

| Command | Description |
|---|---|
| _(any text, private chat)_ | Calculator — evaluates math expressions: `2+2*5`, `(10-4)/3`, `sqrt(16) + 3^2`, `pow(2,10)` |
| `/bdotax <price> [vp] [ring] [fame1\|fame2\|fame3]` | BDO central market tax breakdown (65% base, 84.5% with Value Pack, +5% ring/pass, family fame tiers). Supports price shortcuts: `500k`, `100m`, `1.5b` |
| `/templates [name]` | Copy-paste templates (login, logout, progress) with `[placeholders]` |
| `/combo [class]` | Class combos (witch, witch-macro) |
| `/schedule` | Pilot schedule link |
| `/type-job` | Type Job list (LAIN2 pairs: Kosong, Used, IT, MT, TR) |
| `/info` | Unit status reference (Kosong / Used / IT / MT / TR) |
| `/idle <pc>` | No-order number for a PC — `/idle 5` -> `14105` (PCs 1-10) |
| `/help` | Command overview |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your bot token in .env
python bot.py
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram. The bot registers its command menu (`/bdotax`, `/templates`, …) automatically on startup.

Notes:
- The calculator only answers in **private chats** — in groups it responds to commands only, never to regular chatter.
- Comma semantics differ by command, matching each community's convention: the calculator reads `2,5` as a decimal comma (= 2.5; inside parentheses commas separate function arguments, e.g. `pow(2,10)`), while `/bdotax` reads `1,000,000` as thousands separators.

## Tests

```bash
pytest -q
```

Tests for the calculator and tax logic live in `tests/` and run on every push/PR via GitHub Actions (`.github/workflows/test.yml`).

## Configuration

Content is data-driven — edit these files, no code changes needed:

| File | Contents |
|---|---|
| `templates.json` | Copy-paste templates for `/templates` |
| `combos.json` | Class combos for `/combo` |
| `info.json` | Reference texts for `/type-job`, `/info`, `/idle` |
| `.env` | `BOT_TOKEN` (never committed) |

## Project structure

```
bot.py          — entry point, all command handlers
calculator.py   — safe AST-based math expression evaluator
bdotax.py       — BDO central market tax logic
*.json          — editable content (templates, combos, info)
pyproject.toml  — project metadata + pytest config
tests/          — pytest suite for calculator and bdotax
```

## License

MIT — see [LICENSE](LICENSE).
