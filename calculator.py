"""Safe arithmetic expression evaluator.

Parses expressions with the ast module and evaluates only whitelisted
math operations — never uses eval(), so user input cannot execute code.

Supported:
  Operators:  +  -  *  /  //  %  ** (or ^)  parentheses  unary minus
  Functions:  sqrt abs round floor ceil sin cos tan log ln exp pow
  Constants:  pi  e

Commas: a comma-grouped number like 1,000,000 is read as thousands
separators; any other comma outside parentheses is a decimal separator
(2,5 -> 2.5). Inside parentheses commas separate function arguments
(pow(2,10), round(3.14159, 2)).
"""

import ast
import math
import re

_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "exp": math.exp,
    "pow": pow,
}

_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}

_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}

_UNARY_OPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}

_MAX_ABS_VALUE = 1e15  # reject absurd values like 9**9**9 before computing
_MAX_EXPONENT = 100


class CalculatorError(Exception):
    """Raised when an expression cannot be evaluated safely."""


def _check(value: float) -> float:
    if abs(value) > _MAX_ABS_VALUE:
        raise CalculatorError("number is too large")
    return value


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return _check(node.value)
        raise CalculatorError("only numbers are allowed")

    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise CalculatorError("exponent is too large")
        return _check(_BIN_OPS[type(node.op)](left, right))

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate(node.operand))

    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func = _FUNCTIONS.get(node.func.id)
        if func is None:
            raise CalculatorError(f"unknown function: {node.func.id}")
        args = [_evaluate(arg) for arg in node.args]
        # pow() must respect the same limits as the ** operator: builtin
        # pow computes exact big integers, so pow(10, 10**8) would hang
        # the event loop for minutes without an exponent cap.
        if func is pow and len(args) == 2 and abs(args[1]) > _MAX_EXPONENT:
            raise CalculatorError("exponent is too large")
        return _check(func(*args))

    raise CalculatorError("unsupported expression")


def _format_result(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


_THOUSANDS_RE = re.compile(r"\d{1,3}(?:,\d{3})+")


def _normalize(expression: str) -> str:
    """Prepare an expression for parsing.

    '^' becomes '**'. Inside parentheses commas are function-argument
    separators and are left alone. Outside parentheses, a number with
    comma groups of exactly three digits (1,000,000) is thousands
    separators and they are stripped; any other comma is a decimal
    separator and becomes a dot (2,5 -> 2.5).
    """
    expression = expression.strip().replace("^", "**")
    out = []
    token = []  # current run of digits/commas at depth 0
    depth = 0

    def flush() -> None:
        if not token:
            return
        text = "".join(token)
        token.clear()
        if _THOUSANDS_RE.fullmatch(text):
            out.append(text.replace(",", ""))
        else:
            out.append(text.replace(",", "."))

    for ch in expression:
        if ch == "(":
            flush()
            depth += 1
            out.append(ch)
        elif ch == ")":
            flush()
            depth = max(0, depth - 1)
            out.append(ch)
        elif depth == 0 and ch in "0123456789,":
            token.append(ch)
        else:
            flush()
            out.append(ch)
    flush()
    return "".join(out)


def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression, returning the formatted result.

    Raises CalculatorError with a user-friendly message on any problem.
    """
    expression = _normalize(expression)
    if not expression:
        raise CalculatorError("empty expression")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise CalculatorError("I couldn't parse that expression")

    try:
        result = _evaluate(tree)
    except CalculatorError:
        raise
    except ZeroDivisionError:
        raise CalculatorError("division by zero")
    except (ValueError, OverflowError):
        raise CalculatorError("math error (check the input range)")
    except TypeError as exc:
        raise CalculatorError(f"wrong arguments: {exc}")

    return _format_result(result)
