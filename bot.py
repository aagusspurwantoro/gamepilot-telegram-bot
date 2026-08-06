import asyncio
import html
import logging
import os
import re
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


def _render_inline(text: str) -> str:
    """Inline markdown -> Telegram HTML: **bold**, `code`, [text](url).
    Only & < > need escaping for Telegram; quotes stay as-is."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text
    )
    return text


def _render_markdown(text: str) -> list[str]:
    """Convert docs markdown to Telegram HTML blocks: headers -> bold,
    ``` fences and tables -> <pre>, everything else inline."""
    blocks: list[str] = []
    fence: list[str] = []
    table: list[str] = []
    in_fence = False

    def flush_fence() -> None:
        if fence:
            blocks.append(
                "<pre>" + html.escape("\n".join(fence), quote=False) + "</pre>"
            )
            fence.clear()

    def flush_table() -> None:
        if table:
            # inline-render rows so ** and [links] work inside the <pre>
            blocks.append(
                "<pre>" + "\n".join(_render_inline(r) for r in table) + "</pre>"
            )
            table.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_fence:
                flush_fence()
                in_fence = False
            else:
                flush_table()
                in_fence = True
            continue
        if in_fence:
            fence.append(line)
            continue
        if stripped.startswith("|"):
            # keep table rows, skip the |---|---| separator
            if not re.fullmatch(r"\|[\s:|-]+\|", stripped):
                table.append(line)
            continue
        flush_table()
        header = re.match(r"#{1,6}\s+(.*)", stripped)
        if header:
            blocks.append(f"<b>{_render_inline(header.group(1))}</b>")
        else:
            blocks.append(_render_inline(line))
    flush_fence()
    flush_table()
    return blocks


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
    # chunk whole blocks under the message cap so HTML tags never split
    chunk: list[str] = []
    length = 0
    for block in _render_markdown(text):
        if length + len(block) + 1 > _MAX_MESSAGE and chunk:
            await message.answer("\n".join(chunk), parse_mode="HTML")
            chunk, length = [], 0
        chunk.append(block)
        length += len(block) + 1
    if chunk:
        await message.answer("\n".join(chunk), parse_mode="HTML")


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
