from math import exp, log
from pathlib import Path

import pytest

from pyratehike._date_arithmetic import _dp_daycount, _RHDate
from pyratehike.curve import IRCurve
from pyratehike.instrument import FinancialInstrument
from pyratehike.list_of_instruments import ListOfInstruments
from pyratehike.metrics import benchmark
from pyratehike.parameters_settings import RHSettings

data_path = Path(__file__).parent.parent / "pyratehike/data"
ibor_path = data_path / "ibor.csv"
ois_path = data_path / "ois.csv"


class TestAttributes:
    today1 = "2001-01-01"
    today2 = "2001-01-29"

    def test_curve(self):
        c1 = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today1,
                currency="EUR",
                interpolation_data_type="zero",
                interpolation_method="linear",
                re_anchoring="no",
            ),
        )
        assert c1._calendar == "TARGET"
        assert str(c1.spot_date) == "2001-01-03"
        assert (
            str(type(c1._interpolation_data_type))
            == "<class 'pyratehike._interpolation._InterpolationDataTypeZero'>"
        )
        assert (
            str(type(c1._interpolation_method._spline_correction))
            == "<class 'pyratehike._interpolation._SplineCorrectionNo'>"
        )
        assert (
            str(type(c1._interpolation_method._interpolation_coefficients))
            == "<class 'pyratehike._interpolation._InterpolationCoefficientsLinear'>"
        )
        assert (
            str(type(c1._anchoring))
            == "<class 'pyratehike.curve._ReAnchorMethodNo'>"
        )

        c2 = IRCurve(
            "SONIA",
            RHSettings(
                today_date=self.today1,
                currency="GBP",
                interpolation_data_type="df",
                interpolation_method="bessel",
                spline_correction="linear",
                re_anchoring="date",
            ),
        )
        assert c2._calendar == "UK"
        assert str(c2.spot_date) == "2001-01-01"
        assert (
            str(type(c2._interpolation_data_type))
            == "<class 'pyratehike._interpolation._InterpolationDataTypeDf'>"
        )
        assert (
            str(type(c2._interpolation_method._spline_correction))
            == "<class 'pyratehike._interpolation._SplineCorrectionLinear'>"
        )
        assert (
            str(type(c2._interpolation_method._interpolation_coefficients))
            == "<class 'pyratehike._interpolation._InterpolationCoefficientsBessel'>"
        )
        assert (
            str(type(c2._anchoring))
            == "<class 'pyratehike.curve._ReAnchorMethodDate'>"
        )

        c3 = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today1,
                currency="EUR",
                interpolation_data_type="logdf",
                interpolation_method="linear",
                spline_correction="natural",
                re_anchoring="11",
                spot_date=self.today2,
            ),
        )
        assert c3._calendar == "TARGET"
        assert str(c3.spot_date) == "2001-01-29"
        assert (
            str(type(c3._interpolation_data_type))
            == "<class 'pyratehike._interpolation._InterpolationDataTypeLogdf'>"
        )
        assert (
            str(type(c3._interpolation_method._spline_correction))
            == "<class 'pyratehike._interpolation._SplineCorrectionNatural'>"
        )
        assert (
            str(type(c3._interpolation_method._interpolation_coefficients))
            == "<class 'pyratehike._interpolation._InterpolationCoefficientsLinear'>"
        )
        assert (
            str(type(c3._anchoring))
            == "<class 'pyratehike.curve._ReAnchorMethod11'>"
        )

        c4 = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today1,
                currency="EUR",
                interpolation_data_type="logdf",
                interpolation_method="linear",
                re_anchoring="ONTN",
            ),
        )
        assert c4._calendar == "TARGET"
        assert str(c4.spot_date) == "2001-01-03"
        assert (
            str(type(c4._interpolation_data_type))
            == "<class 'pyratehike._interpolation._InterpolationDataTypeLogdf'>"
        )
        assert (
            str(type(c4._interpolation_method._spline_correction))
            == "<class 'pyratehike._interpolation._SplineCorrectionNo'>"
        )
        assert (
            str(type(c4._interpolation_method._interpolation_coefficients))
            == "<class 'pyratehike._interpolation._InterpolationCoefficientsLinear'>"
        )
        assert (
            str(type(c4._anchoring))
            == "<class 'pyratehike.curve._ReAnchorMethodONTN'>"
        )


class TestGetData:
    today = "2000-12-31"
    c1 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c1._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c1._interpolation_method._times = [0, 1, 2]
    c1._interpolation_method.n_pillars_set = 3

    c2 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="bessel",
            spot_date=today,
        ),
    )
    c2._interpolation_method._coefficients = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 11, 12],
    ]
    c2._interpolation_method._times = [0, 1, 2]
    c2._interpolation_method.n_pillars_set = 3

    def test_get_data(self):
        data11, times11 = self.c1._get_data()
        data12, times12 = self.c2._get_data()
        expdata1 = [1, 2, 3]
        exptimes1 = [0, 1, 2]
        assert data11 == expdata1
        assert times11 == exptimes1
        assert data12 == expdata1
        assert times12 == exptimes1

        expdata2 = [2, 3]
        exptimes2 = [1, 2]
        data21, times21 = self.c1._get_data(pillars=exptimes2)
        data22, times22 = self.c2._get_data(pillars=exptimes2)
        assert data21 == expdata2
        assert times21 == exptimes2
        assert data22 == expdata2
        assert times22 == exptimes2

        expdata31 = [1, 1 + 0.3 * 4, 2 + 0.3 * 5, 3]
        expdata32 = [
            1,
            1 + 0.3 * 4 + 0.3**2 * 7 + 0.3**3 * 10,
            2 + 0.3 * 5 + 0.3**2 * 8 + 0.3**3 * 11,
            3,
        ]
        exptimes3 = [-1, 0.3, 1.3, 2.3]
        data31, times31 = self.c1._get_data(times=exptimes3)
        data32, times32 = self.c2._get_data(times=exptimes3)
        assert data31 == pytest.approx(expdata31)
        assert times31 == exptimes3
        assert data32 == pytest.approx(expdata32)
        assert times32 == exptimes3

        input4 = [
            _RHDate("2000-12-31").add_days(180),
            _RHDate("2001-12-31").add_days(180),
        ]
        exptimes4 = [180 / 365, 1 + 180 / 365]
        expdata41 = [1 + 180 / 365 * 4, 2 + 180 / 365 * 5]
        expdata42 = [
            1 + 180 / 365 * 4 + (180 / 365) ** 2 * 7 + (180 / 365) ** 3 * 10,
            2 + 180 / 365 * 5 + (180 / 365) ** 2 * 8 + (180 / 365) ** 3 * 11,
        ]
        data41, times41 = self.c1._get_data(dates=input4)
        data42, times42 = self.c2._get_data(dates=input4)
        assert times41 == exptimes4
        assert data41 == pytest.approx(expdata41)
        assert data42 == pytest.approx(expdata42)
        assert times42 == exptimes4

    def test_get_data_deriv(self):
        data11, times11 = self.c1._get_data(derivative=True)
        data12, times12 = self.c2._get_data(derivative=True)
        expdata1 = [4, 5, 6]
        exptimes1 = [0, 1, 2]
        assert data11 == expdata1
        assert times11 == exptimes1
        assert data12 == expdata1
        assert times12 == exptimes1

        expdata2 = [5, 6]
        exptimes2 = [1, 2]
        data21, times21 = self.c1._get_data(pillars=exptimes2, derivative=True)
        data22, times22 = self.c2._get_data(pillars=exptimes2, derivative=True)
        assert data21 == expdata2
        assert times21 == exptimes2
        assert data22 == expdata2
        assert times22 == exptimes2

        expdata31 = [4, 4, 5, 6]
        expdata32 = [
            4,
            4 + 0.3 * 7 * 2 + 0.3**2 * 10 * 3,
            5 + 0.3 * 8 * 2 + 0.3**2 * 11 * 3,
            6,
        ]
        exptimes3 = [-1, 0.3, 1.3, 2.3]
        data31, times31 = self.c1._get_data(times=exptimes3, derivative=True)
        data32, times32 = self.c2._get_data(times=exptimes3, derivative=True)
        assert data31 == pytest.approx(expdata31)
        assert times31 == exptimes3
        assert data32 == pytest.approx(expdata32)
        assert times32 == exptimes3

        input4 = [
            _RHDate("2000-12-31").add_days(180),
            _RHDate("2001-12-31").add_days(180),
        ]
        exptimes4 = [180 / 365, 1 + 180 / 365]
        expdata41 = [4, 5]
        expdata42 = [
            4 + (180 / 365) * 7 * 2 + (180 / 365) ** 2 * 10 * 3,
            5 + (180 / 365) * 8 * 2 + (180 / 365) ** 2 * 11 * 3,
        ]
        data41, times41 = self.c1._get_data(dates=input4, derivative=True)
        data42, times42 = self.c2._get_data(dates=input4, derivative=True)
        assert times41 == exptimes4
        assert data41 == pytest.approx(expdata41)
        assert data42 == pytest.approx(expdata42)
        assert times42 == exptimes4


class TestGetters:
    today = "2000-12-31"

    c1 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c1._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c1._interpolation_method._times = [0, 1, 2]
    c1._interpolation_method.n_pillars_set = 3

    c2 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="df",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c2._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c2._interpolation_method._times = [0, 1, 2]
    c2._interpolation_method.n_pillars_set = 3

    c3 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="logdf",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c3._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c3._interpolation_method._times = [0, 1, 2]
    c3._interpolation_method.n_pillars_set = 3

    c4 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="bessel",
            spot_date=today,
        ),
    )
    c4._interpolation_method._coefficients = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 11, 12],
    ]
    c4._interpolation_method._times = [0, 1, 2]
    c4._interpolation_method.n_pillars_set = 3

    c5 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="df",
            interpolation_method="bessel",
            spot_date=today,
        ),
    )
    c5._interpolation_method._coefficients = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 11, 12],
    ]
    c5._interpolation_method._times = [0, 1, 2]
    c5._interpolation_method.n_pillars_set = 3

    c6 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="logdf",
            interpolation_method="bessel",
            spot_date=today,
        ),
    )
    c6._interpolation_method._coefficients = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 11, 12],
    ]
    c6._interpolation_method._times = [0, 1, 2]
    c6._interpolation_method.n_pillars_set = 3

    def test_get_discount_factors(self):
        assert self.c1.get_discount_factors() == [
            exp(-1 * 0),
            exp(-2 * 1),
            exp(-3 * 2),
        ]
        assert self.c2.get_discount_factors() == [1, 2, 3]
        assert self.c3.get_discount_factors() == [exp(1), exp(2), exp(3)]
        assert self.c4.get_discount_factors() == [
            exp(-1 * 0),
            exp(-2 * 1),
            exp(-3 * 2),
        ]
        assert self.c5.get_discount_factors() == [1, 2, 3]
        assert self.c6.get_discount_factors() == [exp(1), exp(2), exp(3)]

    def test_get_zero_rates(self):
        assert self.c1.get_zero_rates() == [1, 2, 3]
        assert self.c2.get_zero_rates(pillars=[1, 2]) == [
            -log(2) / 1,
            -log(3) / 2,
        ]
        assert self.c3.get_zero_rates(pillars=[1, 2]) == [-2 / 1, -3 / 2]
        assert self.c4.get_zero_rates() == [1, 2, 3]
        assert self.c5.get_zero_rates(pillars=[1, 2]) == [
            -log(2) / 1,
            -log(3) / 2,
        ]
        assert self.c6.get_zero_rates(pillars=[1, 2]) == [-2 / 1, -3 / 2]

    def test_get_insta_forwards(self):
        assert self.c1.get_insta_forwards() == [
            1 + 4 * 0,
            2 + 5 * 1,
            3 + 6 * 2,
        ]
        assert self.c2.get_insta_forwards() == [-4 / 1, -5 / 2, -6 / 3]
        assert self.c3.get_insta_forwards() == [-4, -5, -6]
        assert self.c4.get_insta_forwards() == [
            1 + 4 * 0,
            2 + 5 * 1,
            3 + 6 * 2,
        ]
        assert self.c5.get_insta_forwards() == [-4 / 1, -5 / 2, -6 / 3]
        assert self.c6.get_insta_forwards() == [-4, -5, -6]

    def test_get_dates(self):
        assert [str(d) for d in self.c1.get_dates()] == [
            "2000-12-31",
            "2001-12-31",
            "2002-12-31",
        ]
        assert [str(d) for d in self.c1.get_dates([1 / 365, 10 / 365])] == [
            "2001-01-01",
            "2001-01-10",
        ]


class TestUpdateDiscountFactor:
    today = "2000-12-31"

    c1 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="df",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c1._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c1._interpolation_method._times = [0, 1, 2]
    c1._interpolation_method.n_pillars_set = 3

    c2 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="logdf",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c2._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c2._interpolation_method._times = [0, 1, 2]
    c2._interpolation_method.n_pillars_set = 3

    c3 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c3._interpolation_method._coefficients = [[1, 2, 3], [4, 5, 6]]
    c3._interpolation_method._times = [0, 1, 2]
    c3._interpolation_method.n_pillars_set = 3

    def test_update_discount_factor(self):
        self.c1._update_discount_factor(0.9, 1)
        assert self.c1._interpolation_method._coefficients[0] == [1, 0.9, 3]
        assert self.c1.get_discount_factors(pillars=[1]) == [0.9]
        self.c1._update_discount_factor(0.9, 2)
        assert self.c1._interpolation_method._coefficients[0] == [1, 0.9, 0.9]
        assert self.c1.get_discount_factors() == [1, 0.9, 0.9]
        self.c2._update_discount_factor(0.9, 1)
        assert self.c2._interpolation_method._coefficients[0] == [
            1,
            log(0.9),
            3,
        ]
        assert self.c2.get_discount_factors(pillars=[1]) == [0.9]
        self.c2._update_discount_factor(0.9, 2)
        assert self.c2._interpolation_method._coefficients[0] == [
            1,
            log(0.9),
            log(0.9),
        ]
        assert self.c2.get_discount_factors(pillars=[1, 2]) == [0.9, 0.9]
        self.c3._update_discount_factor(0.9, 1)
        assert self.c3._interpolation_method._coefficients[0] == [
            1,
            -log(0.9),
            3,
        ]
        assert self.c3.get_discount_factors(pillars=[1]) == [0.9]
        self.c3._update_discount_factor(0.9, 2)
        assert self.c3._interpolation_method._coefficients[0] == [
            1,
            -log(0.9),
            -log(0.9) / 2,
        ]
        assert self.c3.get_discount_factors(pillars=[1, 2]) == [0.9, 0.9]

    def test_update_all_discount_factors(self):
        self.c1.update_all_discount_factors([0.9, 0.9, 0.9])
        assert self.c1._interpolation_method._coefficients[0] == [
            0.9,
            0.9,
            0.9,
        ]
        assert self.c1.get_discount_factors() == [0.9, 0.9, 0.9]
        self.c2.update_all_discount_factors([0.9, 0.9, 0.9])
        assert self.c2._interpolation_method._coefficients[0] == [
            log(0.9),
            log(0.9),
            log(0.9),
        ]
        assert self.c2.get_discount_factors(pillars=[1, 2]) == [0.9, 0.9]
        self.c3.update_all_discount_factors([0.9, 0.9, 0.9])
        assert self.c3._interpolation_method._coefficients[0] == [
            0,
            -log(0.9),
            -log(0.9) / 2,
        ]
        assert self.c3.get_discount_factors(pillars=[1, 2]) == [0.9, 0.9]


class TestBenchmark:
    today = "2000-12-31"

    c1 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c1._interpolation_method._coefficients = [[1, 2, 3, 4, 5, 6]]
    c1._interpolation_method._times = [0, 1, 2, 3, 4, 5]
    c1._interpolation_method.n_pillars_set = 6

    c2 = IRCurve(
        "ESTR",
        RHSettings(
            today_date=today,
            currency="EUR",
            interpolation_data_type="df",
            interpolation_method="linear",
            spot_date=today,
        ),
    )
    c2._interpolation_method._coefficients = [[1, 2, 3, 4, 5, 6]]
    c2._interpolation_method._times = [0, 1, 2, 3, 4, 5]
    c2._interpolation_method.n_pillars_set = 6

    def test_benchmark(self):
        assert benchmark(self.c1, benchmark_zeros=[2, 3, 4, 5, 6]) == [
            0,
            0,
            0,
            0,
            0,
        ]
        assert benchmark(
            self.c1, benchmark_zeros=[2, 4, 6], pillars=[1, 3, 5]
        ) == [0, 0, 0]
        assert benchmark(
            self.c2, benchmark_discount_factors=[2, 3, 4, 5, 6]
        ) == [0, 0, 0, 0, 0]
        assert benchmark(
            self.c2, benchmark_discount_factors=[2, 4, 6], pillars=[1, 3, 5]
        ) == [
            0,
            0,
            0,
        ]


class TestAnchoring:
    today = "2022-02-22"
    list_ois = ListOfInstruments(
        RHSettings(
            today_date=today,
            currency="EUR",
        ),
        ois_path,
    )

    def test_anchoring(self):
        c_nono = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today,
                currency="EUR",
                interpolation_data_type="zero",
                interpolation_method="linear",
            ),
        )
        c_nono.bootstrap(self.list_ois.instruments)
        times_nono = c_nono._interpolation_method._times
        dates_nono = [str(d) for d in c_nono.get_dates()]
        df_nono = c_nono.get_discount_factors()

        c_no = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today,
                currency="EUR",
                interpolation_data_type="zero",
                interpolation_method="linear",
                re_anchoring="no",
            ),
        )
        c_no.bootstrap(self.list_ois.instruments)
        c_no.re_anchor()
        times_no = c_no._interpolation_method._times
        dates_no = [str(d) for d in c_no.get_dates()]
        df_no = c_no.get_discount_factors()

        c_date = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today,
                currency="EUR",
                interpolation_data_type="zero",
                interpolation_method="linear",
                re_anchoring="date",
            ),
        )
        c_date.bootstrap(self.list_ois.instruments)
        c_date.re_anchor()
        times_date = c_date._interpolation_method._times
        dates_date = [str(d) for d in c_date.get_dates()]
        df_date = c_date.get_discount_factors()

        c_11 = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today,
                currency="EUR",
                interpolation_data_type="zero",
                interpolation_method="linear",
                re_anchoring="11",
            ),
        )
        c_11.bootstrap(self.list_ois.instruments)
        c_11.re_anchor()
        times_11 = c_11._interpolation_method._times
        dates_11 = [str(d) for d in c_11.get_dates()]
        df_11 = c_11.get_discount_factors()

        c_ontn = IRCurve(
            "ESTR",
            RHSettings(
                today_date=self.today,
                currency="EUR",
                interpolation_data_type="zero",
                interpolation_method="linear",
                re_anchoring="ONTN",
            ),
        )
        c_ontn.bootstrap(self.list_ois.instruments)
        c_ontn.re_anchor(self.list_ois.instruments[0])
        times_ontn = c_ontn._interpolation_method._times
        dates_ontn = [str(d) for d in c_ontn.get_dates()]
        df_ontn = c_ontn.get_discount_factors()

        assert str(c_nono.spot_date) == "2022-02-24"
        assert str(c_no.spot_date) == "2022-02-24"
        assert str(c_date.spot_date) == str(self.today)
        assert str(c_11.spot_date) == str(self.today)
        assert str(c_ontn.spot_date) == str(self.today)

        with pytest.raises(AttributeError, match="spot_date_orig"):
            assert str(c_nono.spot_date_orig) == "2022-02-24"
        assert str(c_no.spot_date_orig) == "2022-02-24"
        assert str(c_date.spot_date_orig) == "2022-02-24"
        assert str(c_11.spot_date_orig) == "2022-02-24"
        assert str(c_ontn.spot_date_orig) == "2022-02-24"

        assert dates_no == dates_nono
        assert times_no == times_nono
        assert times_date == times_nono
        assert dates_11[2:] == dates_nono
        assert dates_ontn[2:] == dates_nono
        assert times_11 == times_ontn

        assert df_no == df_nono
        assert df_date == df_nono
        assert df_11 == [1, 1] + df_nono
        assert df_ontn[2:] == pytest.approx([df_ontn[2] * d for d in df_nono])

    def test_anchoring_ontn_parameter(self):
        settings = RHSettings(
            today_date=self.today,
            currency="EUR",
            interpolation_data_type="zero",
            interpolation_method="linear",
            re_anchoring="ONTN",
        )
        c_ontn = IRCurve("ESTR", settings)
        c_ontn.bootstrap(self.list_ois.instruments)

        depo_2dy = FinancialInstrument(
            {
                "insttype": "deposit",
                "mat_no": 2,
                "mat_unit": "DY",
                "quote": "0.01",
            },
            settings,
        )
        depo_1wk = FinancialInstrument(
            {
                "insttype": "deposit",
                "mat_no": 1,
                "mat_unit": "WK",
                "quote": "0.01",
            },
            settings,
        )

        with pytest.raises(
            ValueError,
            match="_AnchorMethodONTN: depo_spot_next cannot be None.",
        ):
            c_ontn.re_anchor()
        with pytest.raises(
            ValueError,
            match="_AnchorMethodONTN: depo_spot_next needs to be an overnight deposit.",
        ):
            c_ontn.re_anchor(self.list_ois.instruments[2])
        with pytest.raises(
            ValueError,
            match="_AnchorMethodONTN: depo_spot_next needs to be an overnight deposit.",
        ):
            c_ontn.re_anchor(depo_2dy)
        with pytest.raises(
            ValueError,
            match="_AnchorMethodONTN: depo_spot_next needs to be an overnight deposit.",
        ):
            c_ontn.re_anchor(depo_1wk)
