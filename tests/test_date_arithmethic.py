from datetime import date
from typing import List

import pytest

from pyratehike._date_arithmetic import (
    _dp_busday_adjust,
    _dp_daycount,
    _dp_next_date,
    _Period,
    _RHDate,
)


class TestDaycount:
    start_date1 = _RHDate("2019-11-30")
    start_date2 = _RHDate("2019-12-31")
    mat_date = _RHDate("2020-05-31")

    def test_act365(self):
        dc = _dp_daycount.dispatch("ACT/365")
        assert dc.daycount(self.start_date1, self.mat_date) == 183 / 365
        assert dc.daycount(self.start_date2, self.mat_date) == 152 / 365
        assert str(dc.get_end_date(self.start_date1, 1 / 365)) == "2019-12-01"
        assert str(dc.get_end_date(self.start_date2, 10 / 365)) == "2020-01-10"

    def test_act360(self):
        dc = _dp_daycount.dispatch("ACT/360")
        assert dc.daycount(self.start_date1, self.mat_date) == 183 / 360
        assert dc.daycount(self.start_date2, self.mat_date) == 152 / 360
        with pytest.raises(NotImplementedError):
            assert str(dc.get_end_date(self.start_date1, 1 / 360)) == "x"
            assert str(dc.get_end_date(self.start_date2, 10 / 360)) == "x"

    def test_30e360(self):
        dc = _dp_daycount.dispatch("30E/360")
        assert dc.daycount(self.start_date1, self.mat_date) == 1 / 2
        assert dc.daycount(self.start_date2, self.mat_date) == 1 - 7 / 12
        with pytest.raises(NotImplementedError):
            assert str(dc.get_end_date(self.start_date1, 1 / 360)) == "x"
            assert str(dc.get_end_date(self.start_date2, 10 / 360)) == "x"


class TestBusdayAdjust:
    date1 = _RHDate("2022-04-30")
    date2 = _RHDate("2022-12-25")
    date3 = _RHDate("2023-03-29")
    date4 = _RHDate("2002-03-30")

    def test_default(self):
        ba = _dp_busday_adjust.dispatch()
        with pytest.raises(NotImplementedError):
            assert str(ba.busday_adjust(None, self.date1)) == "2022-05-02"
        with pytest.raises(NotImplementedError):
            assert str(ba.busday_adjust(None, self.date2)) == "2022-12-26"
        with pytest.raises(NotImplementedError):
            assert str(ba.busday_adjust(None, self.date3)) == str(self.date3)

    def test_follow_eur(self):
        ba = _dp_busday_adjust.dispatch("follow")
        assert str(ba.busday_adjust("TARGET", self.date1)) == "2022-05-02"
        assert str(ba.busday_adjust("TARGET", self.date2)) == "2022-12-27"
        assert str(ba.busday_adjust("TARGET", self.date3)) == str(self.date3)

    def test_modfollow_eur(self):
        ba = _dp_busday_adjust.dispatch("modfollow")
        assert str(ba.busday_adjust("TARGET", self.date1)) == "2022-04-29"
        assert str(ba.busday_adjust("TARGET", self.date2)) == "2022-12-27"
        assert str(ba.busday_adjust("TARGET", self.date3)) == str(self.date3)
        assert str(ba.busday_adjust("TARGET", self.date4)) == "2002-03-28"

    def test_follow_uk(self):
        ba = _dp_busday_adjust.dispatch("follow")
        assert str(ba.busday_adjust("UK", self.date1)) == "2022-05-03"
        assert str(ba.busday_adjust("UK", self.date2)) == "2022-12-28"
        assert str(ba.busday_adjust("UK", self.date3)) == str(self.date3)

    def test_modfollow_uk(self):
        ba = _dp_busday_adjust.dispatch("modfollow")
        assert str(ba.busday_adjust("UK", self.date1)) == "2022-04-29"
        assert str(ba.busday_adjust("UK", self.date2)) == "2022-12-28"
        assert str(ba.busday_adjust("UK", self.date3)) == str(self.date3)


class TestNextDate:
    date1 = _RHDate("2022-04-30")
    date2 = _RHDate("2022-12-25")
    per3d = _Period(3, "DY")
    per3w = _Period(3, "WK")
    per3m = _Period(3, "MO")
    per3y = _Period(3, "YR")

    class testClass:
        ba = _dp_busday_adjust.dispatch("follow")

        def busday_adjust(self, datum: _RHDate) -> _RHDate:
            return self.ba.busday_adjust(None, datum)

    test_inst = testClass()

    def test_default(self):
        cnd = _dp_next_date.dispatch()
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3d, adjust=False
                )[0]
            )
            == "2022-05-03"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3w, adjust=False
                )[0]
            )
            == "2022-05-21"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3m, adjust=False
                )[0]
            )
            == "2022-07-30"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3y, adjust=False
                )[0]
            )
            == "2025-04-30"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3d)[0])
            == "2022-05-03"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3w)[0])
            == "2022-05-23"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3m)[0])
            == "2022-08-01"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3y)[0])
            == "2025-04-30"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3d, adjust=False
                )[0]
            )
            == "2022-12-28"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3w, adjust=False
                )[0]
            )
            == "2023-01-15"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3m, adjust=False
                )[0]
            )
            == "2023-03-25"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3y, adjust=False
                )[0]
            )
            == "2025-12-25"
        )

    def test_end_of_month(self):
        cnd = _dp_next_date.dispatch("end_of_month")
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3m, adjust=False
                )[0]
            )
            == "2022-07-31"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3y, adjust=False
                )[0]
            )
            == "2025-04-30"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3m)[0])
            == "2022-08-01"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3y)[0])
            == "2025-04-30"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3m, adjust=False
                )[0]
            )
            == "2023-03-31"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3y, adjust=False
                )[0]
            )
            == "2025-12-31"
        )

    def test_future(self):
        cnd = _dp_next_date.dispatch("future")
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3m, adjust=False
                )[0]
            )
            == "2022-07-20"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date1, self.per3y, adjust=False
                )[0]
            )
            == "2025-04-16"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3m)[0])
            == "2022-07-20"
        )
        assert (
            str(cnd.calc_next_date(self.test_inst, self.date1, self.per3y)[0])
            == "2025-04-16"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3m, adjust=False
                )[0]
            )
            == "2023-03-15"
        )
        assert (
            str(
                cnd.calc_next_date(
                    self.test_inst, self.date2, self.per3y, adjust=False
                )[0]
            )
            == "2025-12-17"
        )


class TestDateProps:
    def test_day(self):
        assert _RHDate("2000-01-01").day == 1
        assert _RHDate("2000-01-10").day == 10
        assert _RHDate("2000-01-15").day == 15
        assert _RHDate("2000-01-20").day == 20
        assert _RHDate("2000-01-25").day == 25
        assert _RHDate("2000-01-31").day == 31

    def test_weekday(self):
        assert _RHDate("2023-06-05").weekday == 1
        assert _RHDate("2023-06-06").weekday == 2
        assert _RHDate("2023-06-07").weekday == 3
        assert _RHDate("2023-06-08").weekday == 4
        assert _RHDate("2023-06-09").weekday == 5
        assert _RHDate("2023-06-10").weekday == 6
        assert _RHDate("2023-06-11").weekday == 7

    def test_month(self):
        assert _RHDate("2000-01-01").month == 1
        assert _RHDate("2000-03-10").month == 3
        assert _RHDate("2000-05-15").month == 5
        assert _RHDate("2000-10-20").month == 10
        assert _RHDate("2000-12-31").month == 12

    def test_year(self):
        assert _RHDate("2001-01-01").year == 2001
        assert _RHDate("2010-01-01").year == 2010
        assert _RHDate("2015-01-01").year == 2015
        assert _RHDate("2020-01-01").year == 2020
        assert _RHDate("2025-01-01").year == 2025
        assert _RHDate("2031-01-01").year == 2031

    def test_err(self):
        assert str(_RHDate("2000-01-01")) == "2000-01-01"
        assert (
            str(_RHDate(date_=date.fromisoformat("2000-01-01")))
            == "2000-01-01"
        )
        with pytest.raises(
            ValueError,
            match="_RHDate: either date_string or date needs to be set.",
        ):
            assert str(_RHDate()) == "2000-01-01"
