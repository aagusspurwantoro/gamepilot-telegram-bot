import asyncio
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
