# GamePilot Telegram Bot

A Telegram bot built with [aiogram 3](https://docs.aiogram.dev/) — calculator, Black Desert Online market tax calculator, and copy-paste helpers for pilot workflows.

## Commands

| Command | Description |
|---|---|
| _(any text)_ | Calculator — evaluates math expressions: `2+2*5`, `(10-4)/3`, `sqrt(16) + 3^2` |
| `/bdotax <price> [vp] [ring] [fame1\|fame2\|fame3]` | BDO central market tax breakdown (65% base, 84.5% with Value Pack, +5% ring/pass, family fame tiers). Supports price shortcuts: `500k`, `100m`, `1.5b` |
| `/templates [name]` | Copy-paste templates (login, logout, progress) with `[placeholders]` |
| `/combo [class]` | Class combos (witch, witch-macro) |
| `/schedule` | Pilot schedule link |
| `/type-job` | Job type list (LAIN2, IT, MT, TR) |
| `/info` | Unit status reference (Used / Kosong) |
| `/idle` | No-order PC number rule (1410 + PC number → 14101–14110) |
| `/help` | Command overview |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your bot token in .env
python bot.py
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram.

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
```

## License

MIT — see [LICENSE](LICENSE).
