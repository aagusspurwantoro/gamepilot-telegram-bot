import pytest

from bdotax import BdoTaxError, breakdown, fame_tier, parse_flags, parse_price, run


class TestParsePrice:
    def test_plain_number(self):
        assert parse_price("5000000") == 5_000_000

    def test_suffixes(self):
        assert parse_price("500k") == 500_000
        assert parse_price("100m") == 100_000_000
        assert parse_price("1.5b") == 1_500_000_000
        assert parse_price("2T") == 2_000_000_000_000

    def test_thousands_separators(self):
        # note: unlike the calculator, /bdotax treats commas as
        # thousands separators, not decimal commas
        assert parse_price("1,000,000") == 1_000_000

    def test_invalid(self):
        with pytest.raises(BdoTaxError):
            parse_price("abc")

    def test_not_positive(self):
        for text in ("0", "-50"):
            with pytest.raises(BdoTaxError, match="greater than zero"):
                parse_price(text)

    def test_too_large(self):
        with pytest.raises(BdoTaxError, match="too large"):
            parse_price("9999t")

    def test_nan_rejected(self):
        # NaN comparisons are always False, so it slips past the
        # <= 0 and > 1e15 guards unless checked explicitly
        with pytest.raises(BdoTaxError, match="not a valid price"):
            parse_price("nan")


class TestParseFlags:
    def test_defaults_all_off(self):
        assert parse_flags([]) == {
            "vp": False,
            "ring": False,
            "fame": 0,
            "fame_points": None,
        }

    def test_all_flags(self):
        assert parse_flags(["vp", "ring", "fame3"]) == {
            "vp": True,
            "ring": True,
            "fame": 3,
            "fame_points": None,
        }

    def test_case_insensitive(self):
        assert parse_flags(["VP", "FAME1"])["fame"] == 1

    def test_unknown_flag(self):
        with pytest.raises(BdoTaxError, match="unknown option"):
            parse_flags(["xyz"])

    def test_last_fame_flag_wins(self):
        assert parse_flags(["fame1", "fame3"])["fame"] == 3

    def test_raw_fame_points_resolve_to_tier(self):
        assert parse_flags(["4500"]) == {
            "vp": False,
            "ring": False,
            "fame": 2,
            "fame_points": 4500,
        }


class TestFameTier:
    @pytest.mark.parametrize(
        "points, tier",
        [
            (0, 0),
            (999, 0),
            (1000, 1),
            (3999, 1),
            (4000, 2),
            (6999, 2),
            (7000, 3),
            (15000, 3),
        ],
    )
    def test_boundaries(self, points, tier):
        assert fame_tier(points) == tier


class TestBreakdown:
    def test_base_rate_65_percent(self):
        result = breakdown(100_000_000)
        assert result["profit"] == 65_000_000
        assert result["total"] == 65_000_000
        assert result["rate"] == pytest.approx(0.65)

    def test_value_pack_84_5_percent(self):
        result = breakdown(100_000_000, vp=True)
        assert result["rate"] == pytest.approx(0.845)

    def test_all_bonuses_stack_additively(self):
        result = breakdown(100_000_000, vp=True, ring=True, fame=3)
        # 0.65 * (1 + 0.30 + 0.05 + 0.015) = 0.88725
        assert result["rate"] == pytest.approx(0.88725)
        assert result["total"] == pytest.approx(88_725_000)

    def test_unknown_fame_tier_gives_no_bonus(self):
        assert breakdown(100_000_000, fame=9)["fame_bonus"] == 0


class TestRun:
    def test_no_flags_shows_plain_and_value_pack(self):
        reply = run("100m")
        assert "84,500,000" in reply
        assert "Value Pack" in reply

    def test_flags_show_single_breakdown(self):
        reply = run("1.5b vp")
        assert "1,267,500,000" in reply
        assert "--- with" not in reply

    def test_empty_args_shows_usage(self):
        with pytest.raises(BdoTaxError, match="usage"):
            run("")

    def test_raw_fame_points_in_output(self):
        reply = run("100m vp 4500")
        assert "4,500 pts" in reply
        assert "+1.0%" in reply

    def test_fame_below_1000_gets_no_bonus(self):
        reply = run("100m 800")
        assert "800 pts" in reply
        assert "no bonus" in reply

    def test_fame_preset_still_works(self):
        reply = run("100m fame3")
        assert "+1.5%" in reply
