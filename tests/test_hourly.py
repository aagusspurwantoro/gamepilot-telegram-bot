import pytest

from hourly import HourlyError, parse_amount, run


class TestParseAmount:
    def test_plain_number(self):
        assert parse_amount("55000") == 55_000

    def test_suffixes(self):
        assert parse_amount("55k") == 55_000
        assert parse_amount("1.5m") == 1_500_000
        assert parse_amount("2K") == 2_000

    def test_thousands_separators(self):
        assert parse_amount("55,000") == 55_000

    def test_invalid(self):
        with pytest.raises(HourlyError, match="not a valid amount"):
            parse_amount("abc")

    def test_nan_rejected(self):
        with pytest.raises(HourlyError, match="not a valid amount"):
            parse_amount("nan")

    def test_infinity_rejected(self):
        with pytest.raises(HourlyError, match="not a valid amount"):
            parse_amount("inf")

    def test_not_positive(self):
        with pytest.raises(HourlyError, match="greater than zero"):
            parse_amount("0")

    def test_too_large(self):
        with pytest.raises(HourlyError, match="too large"):
            parse_amount("9999999b")


class TestRun:
    def test_full_breakdown(self):
        reply = run("55k 15k")
        assert "Total: 55,000 TL" in reply
        assert "Rate: 15,000 TL/hour" in reply
        assert "3.67 hours (3h 40m)" in reply

    def test_exact_hours(self):
        assert "8 hours (8h 0m)" in run("120k 15k")

    def test_singular_hour(self):
        assert "1 hour (1h 0m)" in run("15k 15k")

    def test_minutes_rounding(self):
        # 10k / 15k = 0.6667h = exactly 40 minutes
        assert "(0h 40m)" in run("10k 15k")

    def test_minute_carry(self):
        # a result like 59.6 minutes must carry to the next hour
        assert "(2h 0m)" in run("29900 15000")

    def test_zero_rate_rejected(self):
        with pytest.raises(HourlyError, match="greater than zero"):
            run("55k 0")

    def test_wrong_arg_count_shows_usage(self):
        for args in ("", "55k", "55k 15k 5k"):
            with pytest.raises(HourlyError, match="usage"):
                run(args)

    def test_garbage_amount(self):
        with pytest.raises(HourlyError, match="not a valid amount"):
            run("abc 15k")
