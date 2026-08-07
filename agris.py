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

from hourly import HourlyError, _hours_text
from hourly import parse_amount as _parse_tl


class AgrisError(Exception):
    """Raised when the /agris input cannot be understood."""


def _tl(text: str) -> int:
    """Parse a trash loot / points amount, converting errors."""
    try:
        return _parse_tl(text)
    except HourlyError as exc:
        raise AgrisError(str(exc)) from exc


def _parse_positive_float(text: str, label: str) -> float:
    cleaned = text.strip().lower()
    try:
        value = float(cleaned)
    except ValueError:
        raise AgrisError(f"'{text}' is not a valid {label}") from None
    if not math.isfinite(value):
        raise AgrisError(f"'{text}' is not a valid {label}")
    if value <= 0:
        raise AgrisError(f"{label} must be greater than zero")
    if value > 1e6:
        raise AgrisError(f"{label} is too large")
    return value


def parse_cost(text: str) -> float:
    """Parse the points-per-extra-item ratio (e.g. 1.33, 2)."""
    return _parse_positive_float(text, "points-per-item value")


def parse_hours(text: str) -> float:
    """Parse a duration in hours (e.g. 1, 1.5)."""
    return _parse_positive_float(text, "hours value")


def _fmt(value: float) -> str:
    """0.8 -> '0.8', 2.0 -> '2', 1.1428... -> '1.14'."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


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
        f"Agris: {points:,} pts at {_fmt(cost)} pts/item = +{round(extra):,} TL\n"
        f"\n"
        f"= {_hours_text(hours)}"
    )


def cost_run(arguments: str) -> str:
    """Handle the /agriscost argument string and return the reply text.

    Works out the points-per-item ratio from a timed calibration grind:
    the Agris extra loot is total minus (normal rate x hours), and the
    ratio is points consumed divided by that extra.

    Usage: /agriscost <total> <per-hour> <hours> <points>
    """
    tokens = arguments.split()
    if len(tokens) != 4:
        raise AgrisError(
            "usage: /agriscost <total> <per-hour> <hours> <points>\n"
            "examples: /agriscost 40k 25k 1 12k  ·  /agriscost 55k 25k 1.5 20k"
        )

    total = _tl(tokens[0])
    rate = _tl(tokens[1])
    hours = parse_hours(tokens[2])
    points = _tl(tokens[3])

    normal = rate * hours
    extra = total - normal
    if extra <= 0:
        raise AgrisError(
            f"no extra loot here — total must be more than rate x hours "
            f"({normal:,.0f} TL), otherwise Agris added nothing"
        )
    cost = points / extra

    unit = "hour" if _fmt(hours) == "1" else "hours"
    return (
        f"Total: {total:,} TL\n"
        f"Rate: {rate:,} TL/hour x {_fmt(hours)} {unit} = {normal:,.0f} TL\n"
        f"Extra from Agris: +{extra:,.0f} TL\n"
        f"Points: {points:,}\n"
        f"\n"
        f"= {_fmt(cost)} pts/item\n"
        f"\n"
        f"Use it: /agris <total> {rate:,} <points> {_fmt(cost)}"
    )
