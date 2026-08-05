"""Black Desert Online Central Market tax calculator.

Mechanics (official PA Wiki + BDFoundry, verified Aug 2026):
  - Base tax 35% (30% Central Market + 5% territory) -> collect 65%.
  - Value Pack: +30% on the after-tax profit (65% * 1.3 = 84.5%).
  - Rich Merchant's Ring / Old Moon Trade Pass: +5% on the after-tax
    profit (the two items do not stack with each other).
  - Family Fame reduction: >=1000 +0.5%, >=4000 +1.0%, >=7000 +1.5%,
    applied to the after-tax profit.

Bonuses stack multiplicatively off the 65% profit, matching the
community-standard model used by veliainn.com and bdolytics.com.
"""

import math

BASE_RATE = 0.65
VP_BONUS = 0.30
RING_BONUS = 0.05
FAME_BONUSES = {
    1: 0.005,  # Family Fame >= 1000
    2: 0.010,  # Family Fame >= 4000
    3: 0.015,  # Family Fame >= 7000
}

_SUFFIXES = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
    "t": 1_000_000_000_000,
}


class BdoTaxError(Exception):
    """Raised when the /bdotax input cannot be understood."""


def fame_tier(points: int) -> int:
    """Map Family Fame points (the number shown in-game on the P window)
    to a bonus tier: >=1000 -> 1, >=4000 -> 2, >=7000 -> 3, else 0."""
    if points >= 7000:
        return 3
    if points >= 4000:
        return 2
    if points >= 1000:
        return 1
    return 0


def parse_price(text: str) -> int:
    """Parse a price like 1000000, 1,000,000, 100m, 1.5b into an int."""
    cleaned = text.strip().lower().replace(",", "").replace("_", "")
    if not cleaned:
        raise BdoTaxError("missing price")

    multiplier = 1
    if cleaned[-1] in _SUFFIXES:
        multiplier = _SUFFIXES[cleaned[-1]]
        cleaned = cleaned[:-1]

    try:
        price = float(cleaned) * multiplier
    except ValueError:
        raise BdoTaxError(f"'{text}' is not a valid price")

    if math.isnan(price):
        raise BdoTaxError(f"'{text}' is not a valid price")
    if price <= 0:
        raise BdoTaxError("price must be greater than zero")
    if price > 1e15:
        raise BdoTaxError("price is too large")
    return int(price)


def parse_flags(tokens: list) -> dict:
    """Parse option flags: vp, ring, fame1/fame2/fame3, or raw Family Fame
    points (e.g. 4500) which are resolved to a tier automatically.
    Defaults all off."""
    options = {"vp": False, "ring": False, "fame": 0, "fame_points": None}
    for token in tokens:
        token = token.strip().lower()
        if token == "vp":
            options["vp"] = True
        elif token == "ring":
            options["ring"] = True
        elif token in ("fame1", "fame2", "fame3"):
            options["fame"] = int(token[-1])
            options["fame_points"] = None
        elif token.isdigit():
            options["fame_points"] = int(token)
            options["fame"] = fame_tier(options["fame_points"])
        else:
            raise BdoTaxError(
                f"unknown option '{token}' — use: vp, ring, fame1, fame2, fame3, "
                "or your Family Fame points (e.g. 4500)"
            )
    return options


def breakdown(
    price: int, vp: bool = False, ring: bool = False, fame: int = 0,
    fame_points: int | None = None,
) -> dict:
    """Compute the full tax breakdown for a sale price."""
    profit = price * BASE_RATE
    vp_bonus = profit * VP_BONUS if vp else 0
    ring_bonus = profit * RING_BONUS if ring else 0
    fame_bonus = profit * FAME_BONUSES.get(fame, 0) if fame else 0
    total = profit + vp_bonus + ring_bonus + fame_bonus
    return {
        "price": price,
        "tax": price - profit,
        "profit": profit,
        "vp_bonus": vp_bonus,
        "ring_bonus": ring_bonus,
        "fame_bonus": fame_bonus,
        "fame": fame,
        "fame_points": fame_points,
        "total": total,
        "rate": total / price,
    }


def _fmt(value: float) -> str:
    return f"{int(round(value)):,}"


def format_breakdown(result: dict) -> str:
    lines = [
        f"Sale price: {_fmt(result['price'])}",
        f"Tax ({1 - BASE_RATE:.0%}): -{_fmt(result['tax'])}",
        f"Base profit ({BASE_RATE:.0%}): {_fmt(result['profit'])}",
    ]
    if result["vp_bonus"]:
        lines.append(f"Value Pack (+30%): +{_fmt(result['vp_bonus'])}")
    if result["ring_bonus"]:
        lines.append(f"Ring/Pass (+5%): +{_fmt(result['ring_bonus'])}")
    if result["fame_bonus"]:
        points = (
            f"{result['fame_points']:,} pts, "
            if result["fame_points"] is not None else ""
        )
        lines.append(
            f"Family Fame ({points}+{FAME_BONUSES[result['fame']]:.1%}): "
            f"+{_fmt(result['fame_bonus'])}"
        )
    elif result["fame_points"] is not None:
        lines.append(
            f"Family Fame ({result['fame_points']:,} pts): no bonus (below 1000)"
        )
    lines += [
        "",
        f"You receive: {_fmt(result['total'])} ({result['rate']:.2%})",
    ]
    return "\n".join(lines)


def run(arguments: str) -> str:
    """Handle the /bdotax argument string and return the reply text.

    Usage: /bdotax <price> [vp] [ring] [fame1|fame2|fame3|<fame points>]
    With no flags, shows both plain and Value Pack results.
    """
    tokens = arguments.split()
    if not tokens:
        raise BdoTaxError(
            "usage: /bdotax <price> [vp] [ring] [fame1|fame2|fame3|<fame points>]\n"
            "examples: /bdotax 100m  ·  /bdotax 1.5b vp  ·  /bdotax 5m vp ring 4500"
        )

    price = parse_price(tokens[0])
    options = parse_flags(tokens[1:])

    no_flags = (
        not any([options["vp"], options["ring"], options["fame"]])
        and options["fame_points"] is None
    )
    if no_flags:
        plain = breakdown(price)
        with_vp = breakdown(price, vp=True)
        return (
            format_breakdown(plain)
            + "\n\n--- with Value Pack ---\n\n"
            + format_breakdown(with_vp)
        )

    return format_breakdown(
        breakdown(
            price,
            vp=options["vp"],
            ring=options["ring"],
            fame=options["fame"],
            fame_points=options["fame_points"],
        )
    )
