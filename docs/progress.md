# /progress — Silver Grinding Progress Calculator

Adds a pilot's shift progress onto the cumulative total from the
previous shift's report. Example: the report shows `463 B / 500 B`,
your shift earned `5.1 B` — the new total is `468.1 B / 500 B`.

Different from `/hourly`: that one converts trash loot into hours;
this one tracks silver grinding progress toward a goal.

## Usage

```
/progress <current>/<goal> <added>
```

**Bare numbers are billions (B)** — the scale silver grinding reports
use. Suffixes work too: `b` = billions, `m` = millions, `k` = thousands
(`5100m` = 5.1 B).

## Examples

```
/progress 463/500 5.1

Current: 463 B / 500 B
Added: +5.1 B

= 468.1 B / 500 B (93.6%)
Remaining: 31.9 B
```

```
/progress 495/500 10   ->  Goal reached!   (total met or exceeded)
/progress 450b/500b 5100m   ->  suffix form of the same input
```

Plain `/progress` (or malformed input) shows terminal-style usage:

```
usage: /progress <current>/<goal> <added>
examples: /progress 463/500 5.1  ·  /progress 450b/500b 5100m
```

## How it works (`progress.py`)

- `parse_amount()` — converts to billions; bare number = B, suffixes
  scale (`m` → ÷1000, `k` → ÷1,000,000). Rejects empty/non-numeric,
  zero/negative, NaN and infinity (`math.isfinite`), and absurd values.
- The first argument must contain `/` — `463/500`, not `463 500` — so a
  missing slash gets the usage text instead of a confusing error.
- Amounts print with up to 2 decimals, trailing zeros stripped
  (`468.1 B`, `463 B` — no float noise like `468.09999…`).
- Percentage prints with up to 1 decimal (`93.6%`, `100%`).
- When the total meets or exceeds the goal, the reply ends with
  `Goal reached!` instead of a remaining line.
- Errors raise `ProgressError`; `bot.py` turns them into friendly replies.

Tests: `tests/test_progress.py` pins the parsing, the breakdown output,
exact/exceeded-goal behavior, decimal formatting, and every usage error.
