# /hourly — Trash Loot Hours Calculator

Works out how many hours a shift's trash loot (TL) represents, given a
known per-hour rate. Example: a pilot farms 15K TL/hour and ends the
shift with 55K TL — that is 3.67 hours of farming.

## Usage

```
/hourly <total> <per-hour>
```

Both amounts accept plain numbers (`55000`), thousands separators
(`55,000`), and suffixes: `k` (thousand), `m` (million), `b` (billion).

## Examples

```
/hourly 55k 15k

Total: 55,000 TL
Rate: 15,000 TL/hour

= 3.67 hours (3h 40m)
```

```
/hourly 120k 15k   ->  = 8 hours (8h 0m)
/hourly 15k 15k    ->  = 1 hour (1h 0m)      (singular "hour")
```

Plain `/hourly` (or the wrong number of arguments) shows terminal-style
usage, same convention as `/bdotax`:

```
usage: /hourly <total> <per-hour>
examples: /hourly 55k 15k  ·  /hourly 120k 15k
```

## How it works (`hourly.py`)

- `parse_amount()` — same parsing rules as `/bdotax`: suffixes,
  separators stripped, rejects empty/non-numeric/zero/negative, NaN and
  infinity (`math.isfinite`), and values above 1e15.
- The reply shows **both** decimal hours and hours+minutes, because
  "3h 40m" is what a pilot actually needs, not "3.67".
- Time is computed as `round(hours × 60)` total minutes, then split with
  `divmod` — so a result like 59.6 minutes correctly carries into the
  next hour (`2h 0m`, never `1h 60m`).
- Decimal hours print with up to 2 places, trailing zeros stripped
  (`8` not `8.00`); the word "hour" is singular only for exactly 1.
- Errors raise `HourlyError`; `bot.py` turns them into friendly replies.

Tests: `tests/test_hourly.py` pins the parsing, the breakdown output,
exact-hour and singular forms, minute rounding/carry, zero rate, wrong
argument counts, and garbage input.
