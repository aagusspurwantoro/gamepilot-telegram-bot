"""Cumulative hours progress calculator.

/hourly converts one shift's trash loot into hours; /hours tracks those
hours toward a goal across shifts — a pilot adds their shift's time onto
the cumulative total from the previous report:

  /hours 25h 40m/50h 5h 14m  ->  30h 54m / 50h (61.8%), remaining 19h 6m

Durations accept h and m parts with any spacing ('25h40m', '25 h 40 m',
'1.5h', '45m'); a bare number counts as hours. Internally everything is
minutes.

Duration boundaries: a new duration starts at every 'h' part; an 'm'
part attaches to the 'h' part before it. So '50h 5h 14m' is two
durations (50h and 5h 14m), while '10h 45m' is one (10h 45m) — an added
part that starts with minutes merges into the goal, so give the added
part its own 'h' ('/hours 10h/50h 0h45m' if the shift was under an hour).
"""

import re


class HoursError(Exception):
    """Raised when the /hours input cannot be understood."""


_PART_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([hm]?)")

_MAX_MINUTES = 1e9  # ~1900 years — plenty

_USAGE = (
    "usage: /hours <current>/<goal> <added>\n"
    "examples: /hours 25h 40m/50h 5h 14m  ·  /hours 1h30m/10h 1h15m"
)


def parse_durations(text: str) -> list:
    """Split duration text into separate durations, in minutes.

    '25h 40m' -> [1540], '50h 5h 14m' -> [3000, 314]. An 'm' part right
    after an 'h' part attaches to it; anything else starts a new
    duration. Bare numbers count as hours.
    """
    cleaned = text.strip().lower().replace(",", "")
    if not cleaned:
        raise HoursError("missing duration")

    durations = []
    attach = False  # an 'm' part may still attach to the current duration
    pos = 0
    for match in _PART_RE.finditer(cleaned):
        if cleaned[pos : match.start()].strip():
            raise HoursError(f"'{text}' is not a valid duration")
        pos = match.end()
        value = float(match.group(1))
        if match.group(2) == "m" and attach:
            durations[-1] += value
            attach = False
        elif match.group(2) == "m":
            durations.append(value)
        else:  # 'h', or a bare number read as hours
            durations.append(value * 60)
            attach = True
    if cleaned[pos:].strip():
        raise HoursError(f"'{text}' is not a valid duration")
    if not durations:
        raise HoursError("missing duration")

    for minutes in durations:
        if minutes <= 0:
            raise HoursError("duration must be greater than zero")
        if minutes > _MAX_MINUTES:
            raise HoursError("duration is too large")
    return durations


def _fmt_duration(minutes: float) -> str:
    """1540 -> '25h 40m', 3000 -> '50h', 45 -> '45m'."""
    total = round(minutes)
    hours, mins = divmod(total, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def _fmt_percent(value: float) -> str:
    """0.618 -> '61.8%', 1.0 -> '100%'."""
    return f"{value * 100:.1f}".rstrip("0").rstrip(".") + "%"


def run(arguments: str) -> str:
    """Handle the /hours argument string and return the reply text.

    Usage: /hours <current>/<goal> <added>  (same shape as /progress)
    """
    if arguments.count("/") != 1:
        raise HoursError(_USAGE)
    current_text, rest = arguments.split("/", 1)

    current_parts = parse_durations(current_text)
    parts = parse_durations(rest)
    if len(current_parts) != 1 or len(parts) != 2:
        raise HoursError(_USAGE)
    current = current_parts[0]
    goal, added = parts

    total = current + added
    lines = [
        f"Current: {_fmt_duration(current)} / {_fmt_duration(goal)}",
        f"Added: +{_fmt_duration(added)}",
        "",
        f"= {_fmt_duration(total)} / {_fmt_duration(goal)} "
        f"({_fmt_percent(total / goal)})",
    ]
    if total >= goal:
        lines.append("Goal reached!")
    else:
        lines.append(f"Remaining: {_fmt_duration(goal - total)}")
    return "\n".join(lines)
