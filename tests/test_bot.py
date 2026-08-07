"""Tests for the bot.py handler layer.

The logic modules are tested directly in their own test files; here we
only verify the wiring: each handler passes the command args to the right
logic function, replies with the result, and turns domain errors into
"Error: ..." replies instead of crashing.

The dispatcher filters (private-chat-only calculator, command matching)
are aiogram wiring and are not exercised here.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import bot


def _message(text: str | None = None) -> AsyncMock:
    message = AsyncMock()
    message.text = text
    return message


def _command(args: str | None = None) -> MagicMock:
    return MagicMock(args=args)


def _run(coro):
    return asyncio.run(coro)


def _replied(message: AsyncMock) -> str:
    """The text of the single answer the handler sent."""
    message.answer.assert_awaited_once()
    return message.answer.call_args.args[0]


class TestHelp:
    def test_start_sends_overview(self):
        message = _message()
        _run(bot.handle_start(message))
        assert "Game Pilot Bot" in _replied(message)

    def test_help_sends_help_text(self):
        message = _message()
        _run(bot.handle_help(message))
        assert _replied(message) == bot.HELP_TEXT

    def test_help_lists_every_command(self):
        for name in ("bdotax", "hourly", "hours", "agris", "agriscost", "progress"):
            assert f"/{name}" in bot.HELP_TEXT

    def test_bot_commands_match_help_text(self):
        for command in bot.BOT_COMMANDS:
            assert f"/{command.command}" in bot.HELP_TEXT


class TestCommandHandlers:
    """Each command handler: happy path replies with the result, bad input
    replies with 'Error: ...' from the domain exception."""

    def test_bdotax(self):
        message = _message()
        _run(bot.handle_bdotax(message, _command("100m vp")))
        assert "You receive" in _replied(message)

    def test_bdotax_error(self):
        message = _message()
        _run(bot.handle_bdotax(message, _command("banana")))
        assert _replied(message).startswith("Error:")

    def test_hourly(self):
        message = _message()
        _run(bot.handle_hourly(message, _command("55k 15k")))
        assert "3h 40m" in _replied(message)

    def test_hourly_error(self):
        message = _message()
        _run(bot.handle_hourly(message, _command("55k")))
        assert _replied(message).startswith("Error:")

    def test_hours(self):
        message = _message()
        _run(bot.handle_hours(message, _command("25h 40m/50h 5h 14m")))
        assert "30h 54m / 50h" in _replied(message)

    def test_hours_error(self):
        message = _message()
        _run(bot.handle_hours(message, _command("25h")))
        assert _replied(message).startswith("Error:")

    def test_agris(self):
        message = _message()
        _run(bot.handle_agris(message, _command("30k 15k 10k 1.33")))
        assert "1h 30m" in _replied(message)

    def test_agris_error(self):
        message = _message()
        _run(bot.handle_agris(message, _command("30k 15k 10k")))
        assert _replied(message).startswith("Error:")

    def test_agriscost(self):
        message = _message()
        _run(bot.handle_agriscost(message, _command("40k 25k 1 12k")))
        assert "pts/item" in _replied(message)

    def test_agriscost_error(self):
        message = _message()
        _run(bot.handle_agriscost(message, _command("")))
        assert _replied(message).startswith("Error:")

    def test_progress(self):
        message = _message()
        _run(bot.handle_progress(message, _command("463/500 5.1")))
        assert "468.1 B / 500 B" in _replied(message)

    def test_progress_error(self):
        message = _message()
        _run(bot.handle_progress(message, _command("463 5.1")))
        assert _replied(message).startswith("Error:")

    def test_missing_args_defaults_to_empty(self):
        # Telegram sends no CommandObject.args for a bare "/hourly".
        message = _message()
        _run(bot.handle_hourly(message, _command(None)))
        assert _replied(message).startswith("Error:")


class TestCalculatorHandler:
    def test_expression_result(self):
        message = _message("2+2*5")
        _run(bot.handle_expression(message))
        assert _replied(message) == "12"

    def test_expression_error_points_to_help(self):
        message = _message("1/0")
        _run(bot.handle_expression(message))
        reply = _replied(message)
        assert reply.startswith("Error:")
        assert "/help" in reply

    def test_non_text_message(self):
        message = _message(None)
        _run(bot.handle_expression(message))
        assert "text math expression" in _replied(message)


class TestErrorHandler:
    def test_replies_generic_message(self):
        message = _message("2+2")
        event = MagicMock()
        event.exception = ValueError("boom")
        event.update.message = message
        _run(bot.handle_error(event))
        assert "try again" in _replied(message)

    def test_no_message_no_reply(self):
        event = MagicMock()
        event.exception = ValueError("boom")
        event.update.message = None
        _run(bot.handle_error(event))  # must not raise
