# Game Pilot Bot

A Telegram bot built with [aiogram 3](https://docs.aiogram.dev/) — a safe math calculator, a Black Desert Online market tax calculator, trash loot hours calculators (plain and Agris Fever), and a silver grinding progress tracker.

## Commands

| Command | Description |
|---|---|
| _(any text, private chat)_ | Calculator — evaluates math expressions: `2+2*5`, `(10-4)/3`, `sqrt(16) + 3^2`, `pow(2,10)` |
| `/bdotax <price> [vp] [ring] [fame1\|fame2\|fame3\|<points>]` | BDO central market tax breakdown (65% base, 84.5% with Value Pack, +5% ring/pass, family fame tiers). Fame accepts presets or raw points (e.g. `4500` -> +1.0%). Supports price shortcuts: `500k`, `100m`, `1.5b` |
| `/hourly <total> <per-hour>` | Hours from trash loot — `/hourly 55k 15k` -> `3.67 hours (3h 40m)` |
| `/agris <total> <per-hour> <points> <points-per-item>` | Hours with Agris Fever — `/agris 30k 15k 10k 1.33` -> `1.5 hours (1h 30m)` |
| `/progress <current>/<goal> <added>` | Silver grinding progress — `/progress 463/500 5.1` -> `468.1 B / 500 B (93.6%)` |
| `/help` | Command overview |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your bot token in .env
python bot.py
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram. The bot registers its command menu (`/bdotax`, `/hourly`, `/agris`, `/progress`) automatically on startup.

Notes:
- The calculator only answers in **private chats** — in groups it responds to commands only, never to regular chatter.
- Comma semantics differ by command, matching each community's convention: the calculator auto-detects — `1,000,000` is thousands separators, `2,5` is a decimal comma (= 2.5; inside parentheses commas separate function arguments, e.g. `pow(2,10)`), while `/bdotax`, `/hourly`, `/agris`, and `/progress` always read commas as thousands separators.

## Tests

```bash
pytest -q
```

Tests for the calculator, tax, and hourly logic live in `tests/` and run on every push/PR via GitHub Actions (`.github/workflows/test.yml`).

## Configuration

| File | Contents |
|---|---|
| `.env` | `BOT_TOKEN` (never committed) |

## Project structure

```
bot.py          — entry point, all command handlers
calculator.py   — safe AST-based math expression evaluator
bdotax.py       — BDO central market tax logic
hourly.py       — trash loot hours calculator
agris.py        — Agris Fever trash loot hours calculator
progress.py     — silver grinding progress calculator
pyproject.toml  — project metadata + pytest config
tests/          — pytest suite for calculator, bdotax, hourly, agris, and progress
```

## Documentation

How each feature works, in detail:

- [docs/bdotax.md](docs/bdotax.md) — tax mechanics (verified against official sources), flags, fame tiers
- [docs/calculator.md](docs/calculator.md) — supported syntax, comma semantics, safety limits
- [docs/hourly.md](docs/hourly.md) — usage, output format, rounding rules
- [docs/agris.md](docs/agris.md) — Agris Fever mechanics, points-per-item ratio, usage
- [docs/progress.md](docs/progress.md) — usage, units, goal-reached behavior

## License

MIT — see [LICENSE](LICENSE).
