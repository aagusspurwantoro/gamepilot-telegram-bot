import pytest

from agris import AgrisError, cost_run, parse_cost, parse_hours, run


class TestParseCost:
    def test_decimal(self):
        assert parse_cost("1.33") == 1.33

    def test_integer(self):
        assert parse_cost("2") == 2.0

    def test_invalid(self):
        with pytest.raises(AgrisError, match="not a valid"):
            parse_cost("abc")

    def test_nan_and_infinity_rejected(self):
        for text in ("nan", "inf"):
            with pytest.raises(AgrisError, match="not a valid"):
                parse_cost(text)

    def test_not_positive(self):
        for text in ("0", "-1.5"):
            with pytest.raises(AgrisError, match="greater than zero"):
                parse_cost(text)

    def test_too_large(self):
        with pytest.raises(AgrisError, match="too large"):
            parse_cost("9999999")


class TestRun:
    def test_full_breakdown(self):
        reply = run("30k 15k 10k 1.33")
        assert "Total: 30,000 TL" in reply
        assert "Rate: 15,000 TL/hour" in reply
        assert "Agris: 10,000 pts at 1.33 pts/item = +7,519 TL" in reply
        assert "1.5 hours (1h 30m)" in reply

    def test_integer_cost(self):
        reply = run("30k 15k 10k 2")
        assert "at 2 pts/item = +5,000 TL" in reply
        assert "1.67 hours (1h 40m)" in reply

    def test_one_to_one_cost(self):
        reply = run("30k 15k 10k 1")
        assert "+10,000 TL" in reply
        assert "1.33 hours (1h 20m)" in reply

    def test_full_agris_shift(self):
        # every item came doubled by Agris -> zero farming hours
        reply = run("30k 15k 30k 1")
        assert "0 hours (0h 0m)" in reply

    def test_amount_suffixes_and_separators(self):
        reply = run("30,000 15k 10k 1.33")
        assert "Total: 30,000 TL" in reply

    def test_extra_loot_above_total_rejected(self):
        with pytest.raises(AgrisError, match="more than the total"):
            run("10k 15k 20k 1")

    def test_wrong_arg_count_shows_usage(self):
        for args in ("", "30k", "30k 15k 10k", "30k 15k 10k 1.33 5"):
            with pytest.raises(AgrisError, match="usage"):
                run(args)

    def test_garbage_amounts(self):
        with pytest.raises(AgrisError, match="not a valid amount"):
            run("abc 15k 10k 1.33")
        with pytest.raises(AgrisError, match="not a valid amount"):
            run("30k 15k abc 1.33")

    def test_garbage_cost(self):
        with pytest.raises(AgrisError, match="not a valid"):
            run("30k 15k 10k abc")

    def test_zero_rate_rejected(self):
        with pytest.raises(AgrisError, match="greater than zero"):
            run("30k 0 10k 1.33")

    def test_zero_cost_rejected(self):
        with pytest.raises(AgrisError, match="greater than zero"):
            run("30k 15k 10k 0")


class TestParseHours:
    def test_integer_and_decimal(self):
        assert parse_hours("1") == 1.0
        assert parse_hours("1.5") == 1.5

    def test_invalid(self):
        with pytest.raises(AgrisError, match="not a valid"):
            parse_hours("abc")

    def test_nan_and_infinity_rejected(self):
        for text in ("nan", "inf"):
            with pytest.raises(AgrisError, match="not a valid"):
                parse_hours(text)

    def test_not_positive(self):
        with pytest.raises(AgrisError, match="greater than zero"):
            parse_hours("0")


class TestCostRun:
    def test_full_breakdown(self):
        # the calibration example: 1h grind, 40k total, 25k/h normal,
        # 12k points -> 15k extra items -> 0.8 pts/item
        reply = cost_run("40k 25k 1 12k")
        assert "Total: 40,000 TL" in reply
        assert "Rate: 25,000 TL/hour x 1 hour = 25,000 TL" in reply
        assert "Extra from Agris: +15,000 TL" in reply
        assert "Points: 12,000" in reply
        assert "= 0.8 pts/item" in reply
        assert "/agris <total> 25,000 <points> 0.8" in reply

    def test_fractional_hours(self):
        # 55k total, 1.5h at 25k = 37.5k normal, 17.5k extra
        # 20k points / 17.5k = 1.1428... -> 1.14
        reply = cost_run("55k 25k 1.5 20k")
        assert "x 1.5 hours = 37,500 TL" in reply
        assert "Extra from Agris: +17,500 TL" in reply
        assert "= 1.14 pts/item" in reply

    def test_exact_ratio_no_decimals(self):
        # extra = 20k, points = 40k -> exactly 2
        reply = cost_run("45k 25k 1 40k")
        assert "= 2 pts/item" in reply

    def test_no_extra_loot_rejected(self):
        # total == rate x hours -> Agris added nothing
        with pytest.raises(AgrisError, match="no extra loot"):
            cost_run("25k 25k 1 12k")

    def test_negative_extra_rejected(self):
        with pytest.raises(AgrisError, match="no extra loot"):
            cost_run("20k 25k 1 12k")

    def test_wrong_arg_count_shows_usage(self):
        for args in ("", "40k 25k 1", "40k 25k 1 12k 5"):
            with pytest.raises(AgrisError, match="usage"):
                cost_run(args)

    def test_garbage_inputs(self):
        with pytest.raises(AgrisError, match="not a valid amount"):
            cost_run("abc 25k 1 12k")
        with pytest.raises(AgrisError, match="not a valid"):
            cost_run("40k 25k abc 12k")
        with pytest.raises(AgrisError, match="not a valid amount"):
            cost_run("40k 25k 1 abc")

    def test_zero_hours_rejected(self):
        with pytest.raises(AgrisError, match="greater than zero"):
            cost_run("40k 25k 0 12k")
