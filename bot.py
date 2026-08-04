import asyncio
import json
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from bdotax import BdoTaxError
from bdotax import run as bdotax_run
from calculator import CalculatorError, calculate

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

SCHEDULE_URL = "https://docs.google.com/spreadsheets/d/1m4p1gzCgbTrQUMn81e2YGEZ3s23WesE5s8fZaH1ViKY"

dp = Dispatcher()

HELP_TEXT = (
    "Send me any math expression and I'll calculate it.\n\n"
    "Operators: + - * / // % ** or ^ and parentheses\n"
    "Functions: sqrt abs round floor ceil sin cos tan log ln exp pow\n"
    "Constants: pi, e\n\n"
    "Examples:\n"
    "  2+2*5\n"
    "  (10-4)/3\n"
    "  sqrt(16) + 3^2\n"
    "  2*pi*5"
)


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Hello! I'm GamePilot calculator bot. 🎮🧮\n\n" + HELP_TEXT
    )


@dp.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@dp.message(Command("bdotax"))
async def handle_bdotax(message: Message, command: CommandObject) -> None:
    try:
        reply = bdotax_run(command.args or "")
    except BdoTaxError as exc:
        await message.answer(f"⚠️ {exc}")
        return
    await message.answer(reply)


@dp.message(Command("schedule"))
async def handle_schedule(message: Message) -> None:
    await message.answer(f"📅 Pilot schedule:\n{SCHEDULE_URL}")


@dp.message(Command("combo"))
async def handle_combo(message: Message, command: CommandObject) -> None:
    with open("combos.json", encoding="utf-8") as f:
        combos = json.load(f)
    name = (command.args or "").strip().lower()
    if not name:
        await message.answer(
            "⚔️ Available combos:\n"
            + "\n".join(f"  /combo {n}" for n in sorted(combos))
        )
        return
    if name not in combos:
        await message.answer(
            f"⚠️ no combo called '{name}' — available: {', '.join(sorted(combos))}"
        )
        return
    # code block = one-tap copy in Telegram
    await message.answer(f"```\n{combos[name]}\n```", parse_mode="Markdown")


@dp.message(Command("templates"))
async def handle_templates(message: Message, command: CommandObject) -> None:
    name = (command.args or "").strip().lower()
    if not name:
        await message.answer(
            "📋 Available templates:\n"
            "  /templates login\n\n"
            "Tap one, then copy the text and fill in the [placeholders]."
        )
        return
    if name != "login":
        await message.answer(f"⚠️ no template called '{name}' — available: login")
        return
    with open("templates.json", encoding="utf-8") as f:
        text = json.load(f)["login"]
    # code block = one-tap copy in Telegram
    await message.answer(f"```\n{text}\n```", parse_mode="Markdown")


@dp.message()
async def handle_expression(message: Message) -> None:
    if not message.text:
        await message.answer("Please send a text math expression.")
        return
    try:
        result = calculate(message.text)
    except CalculatorError as exc:
        await message.answer(f"⚠️ {exc}\n\nSend /help to see what I understand.")
        return
    await message.answer(result)


async def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "your-bot-token-here":
        raise RuntimeError(
            "BOT_TOKEN is not set. Get a token from @BotFather on Telegram "
            "and put it in the .env file."
        )
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
