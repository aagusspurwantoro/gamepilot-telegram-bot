import pytest

from hours import HoursError, parse_durations, run


class TestParseDurations:
    def test_hours_and_minutes(self):
        assert parse_durations("25h 40m") == [1540]

    def test_compact_and_spaced_forms(self):
        assert parse_durations("25h40m") == [1540]
        assert parse_durations("25 h 40 m") == [1540]

    def test_multiple_durations(self):
        assert parse_durations("50h 5h 14m") == [3000, 314]

    def test_minutes_only(self):
        assert parse_durations("45m") == [45]

    def test_decimal_hours(self):
        assert parse_durations("1.5h") == [90]

    def test_bare_number_is_hours(self):
        assert parse_durations("50") == [3000]

    def test_minutes_leading_duration(self):
        assert parse_durations("40m 50h") == [40, 3000]

    def test_garbage_rejected(self):
        for text in ("abc", "25hx", "x50h", "10k"):
            with pytest.raises(HoursError, match="not a valid duration"):
                parse_durations(text)

    def test_empty_rejected(self):
        with pytest.raises(HoursError, match="missing duration"):
            parse_durations("   ")

    def test_zero_rejected(self):
        with pytest.raises(HoursError, match="greater than zero"):
            parse_durations("0h")

    def test_too_large_rejected(self):
        with pytest.raises(HoursError, match="too large"):
            parse_durations("999999999h")


class TestRun:
    def test_full_breakdown(self):
        reply = run("25h 40m/50h 5h 14m")
        assert "Current: 25h 40m / 50h" in reply
        assert "Added: +5h 14m" in reply
        assert "= 30h 54m / 50h (61.8%)" in reply
        assert "Remaining: 19h 6m" in reply

    def test_spaces_around_slash_tolerated(self):
        assert run("25h 40m / 50h 5h 14m") == run("25h 40m/50h 5h 14m")

    def test_compact_form(self):
        reply = run("1h30m/10h 1h15m")
        assert "Current: 1h 30m / 10h" in reply
        assert "Added: +1h 15m" in reply
        assert "= 2h 45m / 10h (27.5%)" in reply

    def test_bare_goal_is_hours(self):
        assert "= 6h / 50h (12%)" in run("1h/50 5h")

    def test_decimal_hours(self):
        assert "= 2h / 4h (50%)" in run("1.5h/4h 0.5h")

    def test_minutes_after_goal_merge_into_it(self):
        # 'm' parts attach to the preceding 'h' part, so "10h 45m" is one
        # duration (the goal) and there is nothing left for the added part.
        with pytest.raises(HoursError, match="usage"):
            run("1h/10h 45m")

    def test_goal_reached_exactly(self):
        reply = run("25h/50h 25h")
        assert "(100%)" in reply
        assert "Goal reached!" in reply
        assert "Remaining" not in reply

    def test_goal_exceeded(self):
        reply = run("49h/50h 2h")
        assert "Goal reached!" in reply
        assert "Remaining" not in reply

    def test_missing_slash_shows_usage(self):
        with pytest.raises(HoursError, match="usage"):
            run("25h 40m 50h")

    def test_missing_added_shows_usage(self):
        with pytest.raises(HoursError, match="usage"):
            run("25h/50h")

    def test_two_current_durations_shows_usage(self):
        with pytest.raises(HoursError, match="usage"):
            run("1h 2h/50h 5h")

    def test_garbage_duration(self):
        with pytest.raises(HoursError, match="not a valid duration"):
            run("abc/50h 5h")
