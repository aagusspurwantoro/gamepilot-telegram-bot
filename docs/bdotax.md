# /bdotax — BDO Central Market Tax Calculator

Computes how much silver a seller actually receives from a Central Market
sale, after tax and all collection bonuses.

## Usage

```
/bdotax <price> [vp] [ring] [fame1|fame2|fame3|<fame points>]
```

- `<price>` — sale price. Accepts plain numbers (`5000000`), thousands
  separators (`1,000,000`), and suffixes: `k` (thousand), `m` (million),
  `b` (billion), `t` (trillion). Examples: `500k`, `100m`, `1.5b`.
- `vp` — include if you have an active Value Pack, omit if not.
- `ring` — include if using a Rich Merchant's Ring or Old Moon Trade
  Pass, omit if not. (The two do not stack with each other; veliainn.com
  likewise offers a single combined "Merchant Ring / Trade Pass" toggle.)
- Fame — either a preset tier (`fame1`, `fame2`, `fame3`) **or** your raw
  Family Fame points as shown in-game on the My Information window (P),
  e.g. `4500`. Raw points are resolved to a tier automatically.
- With **no flags**, the reply shows both the plain result and the
  with-Value-Pack result side by side.

## Examples

```
/bdotax 100m                  -> plain + with Value Pack comparison
/bdotax 1.5b vp               -> Value Pack only
/bdotax 5m vp ring 4500       -> VP + ring, fame points 4500 -> +1.0%
/bdotax 100m vp ring fame3    -> all bonuses via preset
```

## Mechanics (verified against official sources, Aug 2026)

| Rule | Value | Source |
|---|---|---|
| Central Market commission | 30% | [PA Wiki — Central Market](https://www.naeu.playblackdesert.com/en-us/Wiki?wikiNo=47) |
| Territory tax | 5% | same |
| **Total tax** | **35% — seller collects 65%** | same |
| Value Pack | +30% **of the after-tax 65%** → 84.5% total | same ("It says 30%, but it's 30% of the already taxed amount") |
| Rich Merchant's Ring / Old Moon Trade Pass | +5% of the after-tax amount | same |
| Family Fame 1,000–3,999 | +0.5% of silver collected | official patch notes / [BDFoundry](https://www.blackdesertfoundry.com/family-fame-guide/) |
| Family Fame 4,000–6,999 | +1.0% | same |
| Family Fame 7,000+ | +1.5% | same |

### How the bonuses combine

All bonuses are percentages **of the after-tax profit** (the "Silver
Collected" amount), added together — matching the community-standard
model used by veliainn.com and bdolytics.com:

```
profit     = price × 0.65
total      = profit × (1 + vp + ring + fame)
max rate   = 0.65 × (1 + 0.30 + 0.05 + 0.015) = 88.725%
```

## Implementation notes (`bdotax.py`)

- `parse_price()` — suffix/separator parsing; rejects empty, non-numeric,
  zero/negative, NaN (`float("nan")` parses successfully and NaN
  comparisons are always False, so it needs an explicit `math.isnan`
  check), and values above 1e15.
- `fame_tier()` — maps raw points to a tier: `>=7000 → 3`,
  `>=4000 → 2`, `>=1000 → 1`, else `0`.
- `parse_flags()` — case-insensitive; last fame flag wins; a bare number
  is treated as fame points. Unknown tokens raise a friendly error
  listing valid options.
- `breakdown()` — pure math, returns the full dict (price, tax, profit,
  each bonus, total, effective rate).
- `format_breakdown()` — human-readable lines; the fame line shows points
  and resolved percentage, e.g. `Family Fame (4,500 pts, +1.0%)`, or a
  `no bonus (below 1000)` note. Tax/profit labels derive from
  `BASE_RATE` so they cannot go stale.
- Errors raise `BdoTaxError`; `bot.py` turns them into friendly replies.

Tests: `tests/test_bdotax.py` pins the parsing, tier boundaries
(999/1000/3999/4000/6999/7000), and exact rates (65%, 84.5%, 88.725%).
