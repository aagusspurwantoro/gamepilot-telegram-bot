# /agris — Agris Fever Trash Loot Hours Calculator

Like `/hourly`, but for shifts that used Agris Fever. While Agris is
active it boosts the junk loot drop amount, so part of the shift's
trash loot came from Agris points rather than farming time — this
command subtracts that part before computing hours.

## Usage

```
/agris <total> <per-hour> <points> <points-per-item>
```

- `<total>` — total trash loot for the shift (`30k`, `30,000`, `30000`)
- `<per-hour>` — your normal trash loot per hour **without** Agris
- `<points>` — Agris Fever points consumed during the shift
- `<points-per-item>` — how many points each extra trash item costs at
  your spot (a decimal like `1.33`, or a whole number like `2`)

## Examples

```
/agris 30k 15k 10k 1.33

Total: 30,000 TL
Rate: 15,000 TL/hour
Agris: 10,000 pts at 1.33 pts/item = +7,519 TL

= 1.5 hours (1h 30m)
```

If the Agris extra loot is larger than the total, the input is
inconsistent and the bot says so instead of printing negative hours.

## Mechanics (verified against official sources, Aug 2026)

From the [official PA Wiki — Agris Fever](https://www.naeu.playblackdesert.com/en-us/Wiki?wikiNo=145)
and [grumpygreen](https://grumpygreen.cricket/margahan-agris/):

- Agris Fever ON increases the **junk item drop amount by +100%**
  (trash loot doubled), up to **+150%** after Book of Margahan Vol. 1
  Chapter 5.
- Points are **consumed per monster killed**, and the cost differs per
  grind spot (e.g. Crescent Shrine ~3 pts/kill, Centaurus ~6,
  Hystria ~7). There is no single universal conversion.
- Daily recovery is 15,000 points (20,000 with the book completed),
  cap 50,000 (100,000 with the book).

### Why the points-per-item argument

Because points are spent per kill and each spot pays out differently,
points → extra loot is a **spot-specific ratio**. Measure it once at
your spot: note the trash loot before/after an Agris session and the
points consumed — e.g. 20,000 points bought 15,000 extra items →
`20000 / 15000 = 1.33` pts/item. That single number absorbs the spot's
per-kill cost **and** your buff level (+100% vs +150%) automatically.

## How it works (`agris.py`)

```
extra_items = points_used / points_per_item
hours       = (total - extra_items) / hourly_rate
```

- Amounts reuse `/hourly`'s parser: suffixes `k/m/b`, thousands
  separators stripped, NaN/infinity/zero/negative rejected, 1e15 cap.
- `parse_cost()` — the ratio must be a positive finite number (use a
  dot for decimals: `1.33`).
- Errors raise `AgrisError`; `bot.py` turns them into friendly replies.

Tests: `tests/test_agris.py` pins the parsing, the breakdown output,
zero/full-Agris shifts, the extra-exceeds-total guard, and every usage
error.
