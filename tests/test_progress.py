import pytest

from progress import ProgressError, parse_amount, run


class TestParseAmount:
    def test_bare_number_is_billions(self):
        assert parse_amount("463") == 463.0
        assert parse_amount("5.1") == 5.1

    def test_suffixes(self):
        assert parse_amount("463b") == 463.0
        assert parse_amount("500m") == 0.5
        assert parse_amount("5100m") == 5.1
        assert parse_amount("2B") == 2.0

    def test_thousands_separators(self):
        assert parse_amount("1,000m") == 1.0

    def test_invalid(self):
        with pytest.raises(ProgressError, match="not a valid amount"):
            parse_amount("abc")

    def test_nan_and_infinity_rejected(self):
        for text in ("nan", "inf"):
            with pytest.raises(ProgressError, match="not a valid amount"):
                parse_amount(text)

    def test_not_positive(self):
        with pytest.raises(ProgressError, match="greater than zero"):
            parse_amount("0")

    def test_too_large(self):
        with pytest.raises(ProgressError, match="too large"):
            parse_amount("9999999")


class TestRun:
    def test_full_breakdown(self):
        reply = run("463/500 5.1")
        assert "Current: 463 B / 500 B" in reply
        assert "Added: +5.1 B" in reply
        assert "= 468.1 B / 500 B (93.6%)" in reply
        assert "Remaining: 31.9 B" in reply

    def test_suffix_mixed_input(self):
        reply = run("450b/500b 5100m")
        assert "Current: 450 B / 500 B" in reply
        assert "Added: +5.1 B" in reply

    def test_goal_reached_exactly(self):
        reply = run("495/500 5")
        assert "(100%)" in reply
        assert "Goal reached!" in reply
        assert "Remaining" not in reply

    def test_goal_exceeded(self):
        reply = run("495/500 10")
        assert "Goal reached!" in reply
        assert "Remaining" not in reply

    def test_decimal_formatting(self):
        # no trailing zeros, no float noise
        assert "= 10 B / 20 B (50%)" in run("5/20 5")

    def test_missing_slash_shows_usage(self):
        with pytest.raises(ProgressError, match="usage"):
            run("463 5.1")

    def test_wrong_arg_count_shows_usage(self):
        for args in ("", "463/500", "463/500 5.1 2"):
            with pytest.raises(ProgressError, match="usage"):
                run(args)

    def test_garbage_amount(self):
        with pytest.raises(ProgressError, match="not a valid amount"):
            run("abc/500 5.1")
        with pytest.raises(ProgressError, match="not a valid amount"):
            run("463/500 abc")
