"""Silver grinding progress calculator.

A pilot takes over a cumulative progress report ("463 B / 500 B") and
adds their own shift's progress on top:

  /progress 463/500 5.1  ->  468.1 B / 500 B (93.6%), remaining 31.9 B

Bare numbers are billions (B) — the scale silver grinding reports use.
Suffixes also work: b = billions, m = millions, k = thousands.
"""

import math

# Divisors, not multipliers: 5100 / 1000 is exactly 5.1, while
# 5100 * (1/1000) is not — floats can't represent 0.001 precisely.
_DIVISORS = {
    "b": 1,
    "m": 1_000,
    "k": 1_000_000,
}


class ProgressError(Exception):
    """Raised when the /progress input cannot be understood."""


def parse_amount(text: str) -> float:
    """Parse an amount into billions: 463 -> 463, 5.1 -> 5.1, 500m -> 0.5."""
    cleaned = text.strip().lower().replace(",", "").replace("_", "")
    if not cleaned:
        raise ProgressError("missing amount")

    divisor = 1
    if cleaned[-1] in _DIVISORS:
        divisor = _DIVISORS[cleaned[-1]]
        cleaned = cleaned[:-1]

    try:
        amount = float(cleaned) / divisor
    except ValueError:
        raise ProgressError(f"'{text}' is not a valid amount") from None

    if not math.isfinite(amount):
        raise ProgressError(f"'{text}' is not a valid amount")
    if amount <= 0:
        raise ProgressError("amount must be greater than zero")
    if amount > 1e6:
        raise ProgressError("amount is too large")
    return amount


def _fmt(value: float) -> str:
    """463.0 -> '463', 468.1 -> '468.1' (up to 2 decimals)."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _fmt_percent(value: float) -> str:
    """0.9362 -> '93.6%', 1.0 -> '100%'."""
    return f"{value * 100:.1f}".rstrip("0").rstrip(".") + "%"


def run(arguments: str) -> str:
    """Handle the /progress argument string and return the reply text.

    Usage: /progress <current>/<goal> <added>
    """
    tokens = arguments.split()
    if len(tokens) != 2 or "/" not in tokens[0]:
        raise ProgressError(
            "usage: /progress <current>/<goal> <added>\n"
            "examples: /progress 463/500 5.1  ·  /progress 450b/500b 5100m"
        )

    current_text, goal_text = tokens[0].split("/", 1)
    current = parse_amount(current_text)
    goal = parse_amount(goal_text)
    added = parse_amount(tokens[1])

    total = current + added
    lines = [
        f"Current: {_fmt(current)} B / {_fmt(goal)} B",
        f"Added: +{_fmt(added)} B",
        "",
        f"= {_fmt(total)} B / {_fmt(goal)} B ({_fmt_percent(total / goal)})",
    ]
    if total >= goal:
        lines.append("Goal reached!")
    else:
        lines.append(f"Remaining: {_fmt(goal - total)} B")
    return "\n".join(lines)
