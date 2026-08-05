import pytest

from calculator import CalculatorError, calculate


class TestArithmetic:
    def test_precedence(self):
        assert calculate("2+2*5") == "12"

    def test_parentheses(self):
        assert calculate("(10-4)/3") == "2"

    def test_caret_is_power(self):
        assert calculate("sqrt(16) + 3^2") == "13"

    def test_floor_div_and_mod(self):
        assert calculate("7//2") == "3"
        assert calculate("5%3") == "2"

    def test_unary_minus(self):
        assert calculate("-5 + 2") == "-3"

    def test_constants(self):
        assert calculate("2*pi*5").startswith("31.4159")

    def test_int_like_floats_format_as_int(self):
        assert calculate("4/2") == "2"

    def test_non_integer_floats_keep_decimals(self):
        assert calculate("1/3").startswith("0.333")


class TestFunctions:
    def test_pow_two_arguments(self):
        # regression: comma-inside-parens was turned into a decimal dot,
        # making pow(2,10) a one-argument call that crashed
        assert calculate("pow(2,10)") == "1024"

    def test_round_with_digits(self):
        assert calculate("round(3.14159, 2)") == "3.14"

    def test_single_arg_functions(self):
        assert calculate("abs(-3)") == "3"
        assert calculate("floor(2.7)") == "2"
        assert calculate("ceil(2.1)") == "3"
        assert calculate("log(100)") == "2"


class TestDecimalComma:
    def test_comma_outside_parens_is_decimal(self):
        assert calculate("2,5*4") == "10"

    def test_comma_with_parenthesized_term(self):
        assert calculate("2,5*(3+2)") == "12.5"

    def test_comma_inside_parens_is_argument_separator(self):
        # (2,5) parses as a tuple, which is not a number
        with pytest.raises(CalculatorError):
            calculate("(2,5)")


class TestThousandsSeparators:
    # comma input -> grouped output (see TestOutputFollowsInputStyle)
    def test_single_group(self):
        assert calculate("100,000+5") == "100,005"

    def test_multiple_groups(self):
        assert calculate("1,000,000") == "1,000,000"

    def test_bdo_scale_numbers(self):
        # 5 billion written the way players type it
        assert calculate("5,000,000,000") == "5,000,000,000"

    def test_three_digits_after_comma_reads_as_thousands(self):
        # documented ambiguity: exactly-3-digit groups win over decimal
        assert calculate("1,000") == "1,000"

    def test_thousands_in_expression(self):
        assert calculate("1,000,000/2") == "500,000"

    def test_short_group_stays_decimal(self):
        assert calculate("2,55") == "2.55"

    def test_four_digit_group_stays_decimal(self):
        # 1,0000 is not a valid thousands group -> decimal comma -> 1.0000
        assert calculate("1,0000") == "1"


class TestOutputFollowsInputStyle:
    def test_comma_input_groups_result(self):
        assert calculate("1,000,000+252,432") == "1,252,432"

    def test_multiplication_grouped(self):
        assert calculate("252,432*2") == "504,864"

    def test_no_comma_input_stays_plain(self):
        assert calculate("1000000+252432") == "1252432"

    def test_decimal_comma_input_also_groups(self):
        assert calculate("2,5*1000") == "2,500"

    def test_paren_comma_does_not_group(self):
        # the comma in pow(2,10) is an argument separator, not number style
        assert calculate("pow(2,10)") == "1024"

    def test_non_integer_result_ungrouped(self):
        # grouping applies to whole numbers; decimals print as-is
        assert calculate("1,000,000/3").startswith("333333.333")


class TestErrors:
    def test_empty(self):
        with pytest.raises(CalculatorError, match="empty"):
            calculate("")

    def test_division_by_zero(self):
        with pytest.raises(CalculatorError, match="division by zero"):
            calculate("1/0")

    def test_exponent_too_large(self):
        with pytest.raises(CalculatorError, match="exponent"):
            calculate("9**9**9")

    def test_pow_function_exponent_too_large(self):
        # regression: the exponent cap only guarded the ** operator, so
        # pow(10, 10**8) computed a 100M-digit integer and hung the bot
        with pytest.raises(CalculatorError, match="exponent"):
            calculate("pow(10,100000000)")

    def test_function_result_capped(self):
        # function returns go through the same magnitude check as operators
        with pytest.raises(CalculatorError, match="too large"):
            calculate("exp(700)")

    def test_number_too_large(self):
        with pytest.raises(CalculatorError, match="too large"):
            calculate("10**100")

    def test_out_of_domain(self):
        with pytest.raises(CalculatorError, match="math error"):
            calculate("sqrt(-1)")

    def test_unknown_function(self):
        with pytest.raises(CalculatorError, match="unknown function"):
            calculate("hack(1)")

    def test_names_other_than_constants_rejected(self):
        with pytest.raises(CalculatorError):
            calculate("open")

    def test_unsupported_syntax(self):
        with pytest.raises(CalculatorError):
            calculate("[1,2,3]")

    def test_no_code_execution(self):
        with pytest.raises(CalculatorError):
            calculate("__import__('os').system('id')")

    def test_deep_nesting_handled_gracefully(self):
        with pytest.raises(CalculatorError):
            calculate("(" * 500 + "1" + ")" * 500)
