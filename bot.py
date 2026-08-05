import asyncio
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
from hourly import HourlyError
from hourly import run as hourly_run
from progress import ProgressError
from progress import run as progress_run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resolve .env relative to this file, so the bot works no matter
# which directory it is started from.
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

HELP_TEXT = (
    "Game Pilot Bot commands:\n\n"
    "Calculator — send any math expression:\n"
    "  2+2*5 · (10-4)/3 · sqrt(16) + 3^2 · 2*pi*5\n"
    "  Functions: sqrt abs round floor ceil sin cos tan log ln exp pow\n\n"
    "/bdotax <price> [vp] [ring] [fame1|fame2|fame3|<points>]\n"
    "  BDO central market tax, e.g. /bdotax 100m vp\n\n"
    "/hourly <total> <per-hour>\n"
    "  hours from trash loot, e.g. /hourly 55k 15k\n\n"
    "/progress <current>/<goal> <added>\n"
    "  silver grinding progress, e.g. /progress 463/500 5.1\n\n"
    "/docs <name> — feature documentation, e.g. /docs bdotax"
)

# Shown in Telegram's command menu. Names must be a-z/0-9/underscore.
BOT_COMMANDS = [
    BotCommand(command="help", description="Command overview"),
    BotCommand(command="bdotax", description="BDO central market tax calculator"),
    BotCommand(command="hourly", description="Hours from trash loot (e.g. /hourly 55k 15k)"),
    BotCommand(command="progress", description="Silver grinding progress (e.g. /progress 463/500 5.1)"),
    BotCommand(command="docs", description="Feature documentation (e.g. /docs bdotax)"),
]


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer("Hello! I'm Game Pilot Bot.\n\n" + HELP_TEXT)


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


@dp.message(Command("hourly"))
async def handle_hourly(message: Message, command: CommandObject) -> None:
    try:
        reply = hourly_run(command.args or "")
    except HourlyError as exc:
        await message.answer(f"Error: {exc}")
        return
    await message.answer(reply)


@dp.message(Command("progress"))
async def handle_progress(message: Message, command: CommandObject) -> None:
    try:
        reply = progress_run(command.args or "")
    except ProgressError as exc:
        await message.answer(f"Error: {exc}")
        return
    await message.answer(reply)


DOCS_DIR = BASE_DIR / "docs"
# Telegram messages are capped at 4096 characters; leave headroom.
_MAX_MESSAGE = 4000


def _available_docs() -> list[str]:
    return sorted(p.stem for p in DOCS_DIR.glob("*.md"))


@dp.message(Command("docs"))
async def handle_docs(message: Message, command: CommandObject) -> None:
    docs = _available_docs()
    name = (command.args or "").strip().lower()
    if not name:
        await message.answer(
            "Available docs:\n" + "\n".join(f"  /docs {n}" for n in docs)
        )
        return
    if name not in docs:
        await message.answer(
            f"No docs called '{name}' — available: {', '.join(docs)}"
        )
        return
    text = (DOCS_DIR / f"{name}.md").read_text(encoding="utf-8")
    # split long docs into multiple messages on line boundaries
    chunk: list[str] = []
    length = 0
    for line in text.splitlines(keepends=True):
        if length + len(line) > _MAX_MESSAGE and chunk:
            await message.answer("".join(chunk))
            chunk, length = [], 0
        chunk.append(line)
        length += len(line)
    if chunk:
        await message.answer("".join(chunk))


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
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set. Get a token from @BotFather on Telegram "
            "and put it in the .env file."
        )
    bot = Bot(token=BOT_TOKEN)
    await bot.set_my_commands(BOT_COMMANDS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
