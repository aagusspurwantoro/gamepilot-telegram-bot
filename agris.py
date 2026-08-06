"""Agris Fever trash loot hours calculator.

Like /hourly, but accounts for Agris Fever: while active it boosts the
junk loot drop amount, so part of a shift's trash loot came from Agris
points rather than farming time:

  /agris 30k 15k 10k 1.33

Mechanics (official PA Wiki, verified Aug 2026):
  - Agris Fever ON: junk item drop amount +100% (up to +150% after the
    Book of Margahan chapter 5).
  - Points are consumed per monster killed and the cost differs per
    grind spot, so points -> extra loot is a spot-specific ratio. A
    pilot measures it once (points used vs extra trash loot gained,
    e.g. 20k points for 15k extra items = 1.33 pts/item) and that
    number absorbs the spot cost and buff level automatically.

Formula:
  extra_items = points_used / points_per_item
  hours       = (total - extra_items) / hourly_rate
"""

import math

from hourly import HourlyError
from hourly import _hours_text
from hourly import parse_amount as _parse_tl


class AgrisError(Exception):
    """Raised when the /agris input cannot be understood."""


def _tl(text: str) -> int:
    """Parse a trash loot / points amount, converting errors."""
    try:
        return _parse_tl(text)
    except HourlyError as exc:
        raise AgrisError(str(exc))


def parse_cost(text: str) -> float:
    """Parse the points-per-extra-item ratio (e.g. 1.33, 2)."""
    cleaned = text.strip().lower()
    try:
        cost = float(cleaned)
    except ValueError:
        raise AgrisError(f"'{text}' is not a valid points-per-item value")
    if not math.isfinite(cost):
        raise AgrisError(f"'{text}' is not a valid points-per-item value")
    if cost <= 0:
        raise AgrisError("points per item must be greater than zero")
    if cost > 1e6:
        raise AgrisError("points per item is too large")
    return cost


def _fmt_cost(cost: float) -> str:
    """1.33 -> '1.33', 2.0 -> '2'."""
    return f"{cost:g}"


def run(arguments: str) -> str:
    """Handle the /agris argument string and return the reply text.

    Usage: /agris <total> <per-hour> <points> <points-per-item>
    """
    tokens = arguments.split()
    if len(tokens) != 4:
        raise AgrisError(
            "usage: /agris <total> <per-hour> <points> <points-per-item>\n"
            "examples: /agris 30k 15k 10k 1.33  ·  /agris 55k 15k 20k 2"
        )

    total = _tl(tokens[0])
    rate = _tl(tokens[1])
    points = _tl(tokens[2])
    cost = parse_cost(tokens[3])

    extra = points / cost
    if extra > total:
        raise AgrisError(
            f"Agris extra loot ({math.ceil(extra):,} TL) is more than the "
            "total — check the points-per-item value"
        )

    hours = (total - extra) / rate
    return (
        f"Total: {total:,} TL\n"
        f"Rate: {rate:,} TL/hour\n"
        f"Agris: {points:,} pts at {_fmt_cost(cost)} pts/item = +{round(extra):,} TL\n"
        f"\n"
        f"= {_hours_text(hours)}"
    )
