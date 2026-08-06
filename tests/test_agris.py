import pytest

from agris import AgrisError, parse_cost, run


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
