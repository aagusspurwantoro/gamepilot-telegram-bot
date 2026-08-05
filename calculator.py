"""Safe arithmetic expression evaluator.

Parses expressions with the ast module and evaluates only whitelisted
math operations — never uses eval(), so user input cannot execute code.

Supported:
  Operators:  +  -  *  /  //  %  ** (or ^)  parentheses  unary minus
  Functions:  sqrt abs round floor ceil sin cos tan log ln exp pow
  Constants:  pi  e

Commas: outside parentheses a comma is a decimal separator (2,5 -> 2.5);
inside parentheses it separates function arguments (pow(2,10), round(3.14159, 2)).
"""

import ast
import math

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
        return func(*args)

    raise CalculatorError("unsupported expression")


def _format_result(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _normalize(expression: str) -> str:
    """Prepare an expression for parsing.

    '^' becomes '**'. A comma outside parentheses is a decimal separator
    and becomes a dot; a comma inside parentheses is a function-argument
    separator and is left alone, so pow(2,10) and round(3.14159, 2) work.
    """
    expression = expression.strip().replace("^", "**")
    chars = []
    depth = 0
    for ch in expression:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            ch = "."
        chars.append(ch)
    return "".join(chars)


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
