# Calculator — Safe Math Expression Evaluator

In a **private chat**, any plain text message is evaluated as a math
expression. In groups the bot never responds to regular chatter —
commands only.

## Supported syntax

| Category | What works |
|---|---|
| Operators | `+` `-` `*` `/` `//` `%` `**` or `^` (power), parentheses, unary minus |
| Functions | `sqrt` `abs` `round` `floor` `ceil` `sin` `cos` `tan` `log` (base 10) `ln` `exp` `pow` |
| Constants | `pi`, `e` |

```
2+2*5              -> 12
(10-4)/3           -> 2
sqrt(16) + 3^2     -> 13
pow(2,10)          -> 1024
round(3.14159, 2)  -> 3.14
2*pi*5             -> 31.4159...
```

Results that are whole numbers print as integers (`4/2` → `2`),
everything else keeps its decimals.

## Comma semantics

Deliberately different from `/bdotax`, matching each community's
convention:

- **Outside parentheses** a comma is a decimal separator:
  `2,5*4` → `10` (= 2.5 × 4).
- **Inside parentheses** it separates function arguments:
  `pow(2,10)`, `round(3.14159, 2)`.

`_normalize()` tracks parenthesis depth to decide which is which —
this is why `pow(2,10)` works instead of becoming a broken
one-argument call.

## How it works (`calculator.py`)

The evaluator **never uses `eval()`**. The expression is parsed with
Python's `ast` module and walked node by node; only whitelisted node
types, operators, functions, and constants are allowed — anything else
(attribute access, names like `open`, lists, calls to unknown
functions) raises `CalculatorError`.

### Safety limits

User input can reach this code from anyone who messages the bot, so
resource exhaustion is guarded explicitly:

| Guard | Limit | Why |
|---|---|---|
| `_MAX_EXPONENT` | 100 | `9**9**9` would never finish computing |
| `_MAX_ABS_VALUE` | 1e15 | rejects absurd magnitudes like `10**100` |
| `pow()` exponent cap | same 100 | builtin `pow` computes exact big integers — `pow(10, 10**8)` hung the event loop for minutes before this guard existed |
| Function results | pass through `_check` | functions can't exceed the magnitude cap that operators respect |
| Parser nesting limit | (CPython built-in) | 500-deep parentheses raise `SyntaxError`, converted to a friendly error |

### Error mapping

Internal exceptions become user-friendly `CalculatorError` messages:
`ZeroDivisionError` → "division by zero", domain/overflow →
"math error (check the input range)", wrong argument counts →
"wrong arguments: …", unparsable input → "I couldn't parse that
expression". `bot.py` replies with the message plus a `/help` pointer.

Tests: `tests/test_calculator.py` covers precedence, functions, decimal
commas, every error path, the injection attempt
(`__import__('os').system('id')` → rejected), deep nesting, and the
`pow()` DoS regression.
