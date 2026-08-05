import asyncio
import json
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, ErrorEvent, Message
from dotenv import load_dotenv

from bdotax import BdoTaxError
from bdotax import run as bdotax_run
from calculator import CalculatorError, calculate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resolve data files relative to this file, so the bot works no matter
# which directory it is started from.
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1m4p1gzCgbTrQUMn81e2YGEZ3s23WesE5s8fZaH1ViKY"

dp = Dispatcher()

HELP_TEXT = (
    "GamePilot commands:\n\n"
    "Calculator — send any math expression:\n"
    "  2+2*5 · (10-4)/3 · sqrt(16) + 3^2 · 2*pi*5\n"
    "  Functions: sqrt abs round floor ceil sin cos tan log ln exp pow\n\n"
    "/bdotax <price> [vp] [ring] [fame1|fame2|fame3]\n"
    "  BDO central market tax, e.g. /bdotax 100m vp\n\n"
    "/templates — copy-paste login/logout/progress templates\n"
    "/combo — class combos (witch, witch-macro)\n"
    "/schedule — pilot schedule link\n"
    "/type-job — job type list (LAIN2, IT, MT, TR)\n"
    "/info — unit status (Used / Kosong)\n"
    "/idle — no-order PC number (1410 + PC)"
)

# Shown in Telegram's command menu. Names must be a-z/0-9/underscore,
# so the /type-job handler appears here as "typejob" (an alias).
BOT_COMMANDS = [
    BotCommand(command="help", description="Command overview"),
    BotCommand(command="bdotax", description="BDO central market tax calculator"),
    BotCommand(command="templates", description="Copy-paste login/logout/progress templates"),
    BotCommand(command="combo", description="Class combos (witch, witch-macro)"),
    BotCommand(command="schedule", description="Pilot schedule link"),
    BotCommand(command="typejob", description="Job type list (LAIN2, IT, MT, TR)"),
    BotCommand(command="info", description="Unit status (Used / Kosong)"),
    BotCommand(command="idle", description="No-order PC number rule"),
]


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer("Hello! I'm GamePilot bot.\n\n" + HELP_TEXT)


@dp.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@dp.message(Command("bdotax"))
async def handle_bdotax(message: Message, command: CommandObject) -> None:
    try:
        reply = bdotax_run(command.args or "")
    except BdoTaxError as exc:
        await message.answer(f"Error: {exc}")
        return
    await message.answer(reply)


def _load_json(filename: str) -> dict:
    with open(BASE_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@dp.message(Command("type-job", "typejob", "type_job"))
async def handle_type_job(message: Message) -> None:
    await message.answer(_load_json("info.json")["type-job"])


@dp.message(Command("info"))
async def handle_info(message: Message) -> None:
    await message.answer(_load_json("info.json")["info"])


@dp.message(Command("idle"))
async def handle_idle(message: Message, command: CommandObject) -> None:
    args = (command.args or "").strip().lower().removeprefix("pc").strip()
    if not args:
        await message.answer(_load_json("info.json")["idle"])
        return
    try:
        pc = int(args)
    except ValueError:
        await message.answer("Error: give me a PC number, e.g. /idle 5")
        return
    if not 1 <= pc <= 10:
        await message.answer("Error: PC number must be 1-10, e.g. /idle 5")
        return
    await message.answer(str(14100 + pc))


@dp.message(Command("schedule"))
async def handle_schedule(message: Message) -> None:
    await message.answer(f"Pilot schedule:\n{SCHEDULE_URL}")


@dp.message(Command("combo"))
async def handle_combo(message: Message, command: CommandObject) -> None:
    combos = _load_json("combos.json")
    name = (command.args or "").strip().lower()
    if not name:
        await message.answer(
            "Available combos:\n"
            + "\n".join(f"  /combo {n}" for n in sorted(combos))
        )
        return
    if name not in combos:
        await message.answer(
            f"No combo called '{name}' — available: {', '.join(sorted(combos))}"
        )
        return
    # code block = one-tap copy in Telegram
    await message.answer(f"```\n{combos[name]}\n```", parse_mode="Markdown")


@dp.message(Command("templates"))
async def handle_templates(message: Message, command: CommandObject) -> None:
    templates = _load_json("templates.json")
    name = (command.args or "").strip().lower()
    if not name:
        await message.answer(
            "Available templates:\n"
            + "\n".join(f"  /templates {n}" for n in sorted(templates))
            + "\n\nTap one, then copy the text and fill in the [placeholders]."
        )
        return
    if name not in templates:
        await message.answer(
            f"No template called '{name}' — available: {', '.join(sorted(templates))}"
        )
        return
    # code block = one-tap copy in Telegram
    await message.answer(f"```\n{templates[name]}\n```", parse_mode="Markdown")


@dp.message(F.chat.type == ChatType.PRIVATE)
async def handle_expression(message: Message) -> None:
    if not message.text:
        await message.answer("Please send a text math expression.")
        return
    try:
        result = calculate(message.text)
    except CalculatorError as exc:
        await message.answer(f"Error: {exc}\n\nSend /help to see what I understand.")
        return
    await message.answer(result)


@dp.error()
async def handle_error(event: ErrorEvent) -> None:
    logger.error("update handling failed", exc_info=event.exception)
    if event.update.message:
        await event.update.message.answer(
            "Something went wrong on my side. Please try again."
        )


async def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "your-bot-token-here":
        raise RuntimeError(
            "BOT_TOKEN is not set. Get a token from @BotFather on Telegram "
            "and put it in the .env file."
        )
    bot = Bot(token=BOT_TOKEN)
    await bot.set_my_commands(BOT_COMMANDS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
