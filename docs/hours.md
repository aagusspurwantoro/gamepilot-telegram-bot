# /hours — Cumulative Hours Progress Calculator

`/hourly` converts one shift's trash loot into hours; `/hours` tracks
those hours toward a goal across shifts. A pilot adds their shift's time
onto the cumulative total from the previous report:

```
/hours 25h 40m/50h 5h 14m

Current: 25h 40m / 50h
Added: +5h 14m

= 30h 54m / 50h (61.8%)
Remaining: 19h 6m
```

## Usage

```
/hours <current>/<goal> <added>
```

Same shape as `/progress` — `<current>/<goal>` joined by a tight slash,
then the added part. (Spaces around the slash work too.)

Durations accept `h` and `m` parts with any spacing (`25h40m`,
`25 h 40 m`, `1.5h`, `45m`); a bare number counts as hours (`50` = 50h).

## Duration boundaries

A new duration starts at every `h` part; an `m` part attaches to the
`h` part before it:

- `25h 40m` → one duration (25h 40m)
- `50h 5h 14m` → two durations (50h, then 5h 14m)
- `10h 45m` → one duration (10h 45m) — so a minute-only added part
  merges into the goal. If the shift was under an hour, write the added
  part with its own `h`: `/hours 10h/50h 0h45m`

## Examples

```
/hours 25h 40m/50h 5h 14m   ->  = 30h 54m / 50h (61.8%), Remaining: 19h 6m
/hours 1h30m/10h 1h15m      ->  compact form
/hours 49h/50h 2h           ->  Goal reached!   (total met or exceeded)
```

Plain `/hours` (or malformed input) shows terminal-style usage:

```
usage: /hours <current>/<goal> <added>
examples: /hours 25h 40m/50h 5h 14m  ·  /hours 1h30m/10h 1h15m
```

## How it works (`hours.py`)

- `parse_durations()` — regex-scans `number + h/m` parts and groups them
  into durations (in minutes), validating that everything between parts
  is whitespace. Rejects empty/garbage text, zero/negative, and absurd
  values.
- `_fmt_duration()` — minutes back to `25h 40m` / `50h` / `45m`.
- The first `/`-separated part must be exactly one duration (current);
  the second must be exactly two (goal, added) — anything else gets the
  usage text instead of a confusing result.
- Percentage prints with up to 1 decimal (`61.8%`, `100%`); when the
  total meets or exceeds the goal, the reply ends with `Goal reached!`.
- Errors raise `HoursError`; `bot.py` turns them into friendly replies.

Tests: `tests/test_hours.py` pins the parsing rules (including the
m-attaches-to-h boundary rule), the breakdown output, exact/exceeded-goal
behavior, and every usage error.
