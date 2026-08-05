"""Trash loot hourly calculator.

A pilot's shift produces some total trash loot (TL) at a known
per-hour rate; this works out how many hours that total represents:

  /hourly 55k 15k  ->  55,000 TL at 15,000 TL/hour = 3.67 hours (3h 40m)
"""

import math

_SUFFIXES = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
}


class HourlyError(Exception):
    """Raised when the /hourly input cannot be understood."""


def parse_amount(text: str) -> int:
    """Parse an amount like 55000, 55,000, 55k, 1.5m into an int."""
    cleaned = text.strip().lower().replace(",", "").replace("_", "")
    if not cleaned:
        raise HourlyError("missing amount")

    multiplier = 1
    if cleaned[-1] in _SUFFIXES:
        multiplier = _SUFFIXES[cleaned[-1]]
        cleaned = cleaned[:-1]

    try:
        amount = float(cleaned) * multiplier
    except ValueError:
        raise HourlyError(f"'{text}' is not a valid amount")

    if not math.isfinite(amount):
        raise HourlyError(f"'{text}' is not a valid amount")
    if amount <= 0:
        raise HourlyError("amount must be greater than zero")
    if amount > 1e15:
        raise HourlyError("amount is too large")
    return int(amount)


def _hours_text(hours: float) -> str:
    """Format hours as decimal and as hours+minutes: '3.67 hours (3h 40m)'."""
    total_minutes = round(hours * 60)
    h, m = divmod(total_minutes, 60)
    decimal = f"{hours:.2f}".rstrip("0").rstrip(".")
    unit = "hour" if decimal == "1" else "hours"
    return f"{decimal} {unit} ({h}h {m}m)"


def run(arguments: str) -> str:
    """Handle the /hourly argument string and return the reply text.

    Usage: /hourly <total> <per-hour>
    """
    tokens = arguments.split()
    if len(tokens) != 2:
        raise HourlyError(
            "usage: /hourly <total> <per-hour>\n"
            "examples: /hourly 55k 15k  ·  /hourly 120k 15k"
        )

    total = parse_amount(tokens[0])
    rate = parse_amount(tokens[1])

    return (
        f"Total: {total:,} TL\n"
        f"Rate: {rate:,} TL/hour\n"
        f"\n"
        f"= {_hours_text(total / rate)}"
    )
