import pytest

from pyratehike.parameters_settings import RHSettings, rh_params


class TestParameters:
    def test_defaults(self):
        assert rh_params.root_find_tol == 1e-12
        assert rh_params.root_find_interval_radius == 1e-1
        assert rh_params.spline_df_convergence_tol == 1e-12
        assert rh_params.spline_max_sweeps == 10


class TestSettings:
    def test_currency(self):
        s_eur = RHSettings(currency="GBP", today_date="2022-02-22")
        assert s_eur.currency == "GBP"
        s_eur = RHSettings(currency="EUR", today_date="2022-02-22")
        assert s_eur.currency == "EUR"
        with pytest.raises(
            ValueError,
            match="Input Error: currency should be EUR or GBP, got XXX.",
        ):
            s_xxx = RHSettings(currency="XXX", today_date="2022-02-22")

    def test_interpolation_method(self):
        s_bessel = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            interpolation_method="bessel",
        )
        assert s_bessel.interpolation_method == "bessel"
        s_linear = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            interpolation_method="linear",
        )
        assert s_linear.interpolation_method == "linear"
        with pytest.raises(
            ValueError,
            match="Input Error: interpolation_method should be linear or bessel, got XXX.",
        ):
            s_xxx = RHSettings(
                currency="GBP",
                today_date="2022-02-22",
                interpolation_method="XXX",
            )

    def test_interpolation_data_type(self):
        s_zero = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            interpolation_data_type="zero",
        )
        assert s_zero.interpolation_data_type == "zero"
        s_df = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            interpolation_data_type="df",
        )
        assert s_df.interpolation_data_type == "df"
        s_logdf = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            interpolation_data_type="logdf",
        )
        assert s_logdf.interpolation_data_type == "logdf"
        with pytest.raises(
            ValueError,
            match="Input Error: interpolation_data_type should be zero, df or logdf, got XXX.",
        ):
            s_xxx = RHSettings(
                currency="GBP",
                today_date="2022-02-22",
                interpolation_data_type="XXX",
            )

    def test_re_anchoring(self):
        s_no = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            re_anchoring="no",
        )
        assert s_no.re_anchoring == "no"
        s_date = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            re_anchoring="date",
        )
        assert s_date.re_anchoring == "date"
        s_11 = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            re_anchoring="11",
        )
        assert s_11.re_anchoring == "11"
        s_ontn = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            re_anchoring="ONTN",
        )
        assert s_ontn.re_anchoring == "ONTN"
        with pytest.raises(
            ValueError,
            match="Input Error: re_anchoring should be no, date, 11 or ONTN, got XXX.",
        ):
            s_xxx = RHSettings(
                currency="GBP",
                today_date="2022-02-22",
                re_anchoring="XXX",
            )

    def test_spline_correction(self):
        s_no = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            spline_correction="no",
        )
        assert s_no.spline_correction == "no"
        s_linear = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            spline_correction="linear",
        )
        assert s_linear.spline_correction == "linear"
        s_natural = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            spline_correction="natural",
        )
        assert s_natural.spline_correction == "natural"
        with pytest.raises(
            ValueError,
            match="Input Error: spline_correction should be no, linear or natural, got XXX.",
        ):
            s_xxx = RHSettings(
                currency="GBP",
                today_date="2022-02-22",
                spline_correction="XXX",
            )

    def test_synthetic_instruments(self):
        s_no = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            synthetic_instruments="no",
        )
        assert s_no.synthetic_instruments == "no"
        s_ois = RHSettings(
            currency="GBP",
            today_date="2022-02-22",
            synthetic_instruments="OIS",
        )
        assert s_ois.synthetic_instruments == "OIS"
        with pytest.raises(
            ValueError,
            match="Input Error: synthetic_instruments should be no or OIS, got XXX.",
        ):
            s_xxx = RHSettings(
                currency="GBP",
                today_date="2022-02-22",
                synthetic_instruments="XXX",
            )
