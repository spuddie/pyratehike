import pytest

from pyratehike._date_arithmetic import _dp_daycount, _RHDate
from pyratehike.curve import IRCurve
from pyratehike.instrument import FinancialInstrument, SyntheticInstrument
from pyratehike.parameters_settings import RHSettings


class TestInsttypeQuoteDiscountFactorMatDate:
    inst_dict = {
        "insttype": "deposit",
        "quote": "0.02",
        "mat_no": "3",
        "mat_unit": "MO",
        "tenor_m": "3",
        "start_no": "3",
        "start_unit": "MO",
    }

    settings = RHSettings(today_date="2000-01-01", currency="EUR")

    inst1 = FinancialInstrument(inst_dict, settings)
    inst_dict["insttype"] = "fra"
    inst2 = FinancialInstrument(inst_dict, settings)
    inst_dict["insttype"] = "future"
    inst3 = FinancialInstrument(inst_dict, settings)
    inst_dict["insttype"] = "ois"
    inst4 = FinancialInstrument(inst_dict, settings)
    inst_dict["insttype"] = "irs"
    inst5 = FinancialInstrument(inst_dict, settings)
    inst6 = SyntheticInstrument(0.99, _RHDate("2022-02-22"))

    def test_insttype(self):
        assert self.inst1.insttype == "deposit"
        assert self.inst2.insttype == "fra"
        assert self.inst3.insttype == "future"
        assert self.inst4.insttype == "ois"
        assert self.inst5.insttype == "irs"
        assert self.inst6.insttype == "synthetic"

    def test_quote(self):
        assert self.inst1.quote == 0.02
        assert self.inst2.quote == 0.02
        assert self.inst3.quote == 0.02
        assert self.inst4.quote == 0.02
        assert self.inst5.quote == 0.02
        with pytest.raises(AttributeError, match="quote"):
            assert self.inst6.quote == 5

    def test_discount_factor(self):
        with pytest.raises(AttributeError, match="discount_factor"):
            assert self.inst1.discount_factor == 5
        with pytest.raises(AttributeError, match="discount_factor"):
            assert self.inst2.discount_factor == 5
        with pytest.raises(AttributeError, match="discount_factor"):
            assert self.inst3.discount_factor == 5
        with pytest.raises(AttributeError, match="discount_factor"):
            assert self.inst4.discount_factor == 5
        with pytest.raises(AttributeError, match="discount_factor"):
            assert self.inst5.discount_factor == 5
        assert self.inst6.discount_factor == 0.99

    def test_mat_date(self):
        assert str(self.inst1.maturity_date) == "2000-04-04"
        assert (
            str(type(self.inst1.maturity_date))
            == "<class 'pyratehike._date_arithmetic._RHDate'>"
        )
        assert str(self.inst2.maturity_date) == "2000-07-04"
        assert (
            str(type(self.inst2.maturity_date))
            == "<class 'pyratehike._date_arithmetic._RHDate'>"
        )
        assert str(self.inst3.maturity_date) == "2000-07-19"
        assert (
            str(type(self.inst3.maturity_date))
            == "<class 'pyratehike._date_arithmetic._RHDate'>"
        )
        assert str(self.inst4.maturity_date) == "2000-04-04"
        assert (
            str(type(self.inst4.maturity_date))
            == "<class 'pyratehike._date_arithmetic._RHDate'>"
        )
        assert str(self.inst5.maturity_date) == "2000-04-04"
        assert (
            str(type(self.inst5.maturity_date))
            == "<class 'pyratehike._date_arithmetic._RHDate'>"
        )
        assert str(self.inst6.maturity_date) == "2022-02-22"
        assert (
            str(type(self.inst6.maturity_date))
            == "<class 'pyratehike._date_arithmetic._RHDate'>"
        )


class TestCalcSchedule:
    @staticmethod
    def helper_inst_dict(insttype: str, mat_unit: str, mat_no: str) -> dict:
        return {
            "insttype": insttype,
            "quote": 0.02,
            "tenor_m": 3,
            "mat_no": mat_no,
            "mat_unit": mat_unit,
        }

    spot_date = "2001-01-01"
    settings = RHSettings(today_date=spot_date, currency="EUR")

    def test_tenor(self):
        inst1 = FinancialInstrument(
            self.helper_inst_dict("irs", "MO", "9"), self.settings
        )
        inst1.spot_date = _RHDate(self.spot_date)
        actual1 = inst1._calc_schedule_tenor()
        expected1 = ["2001-04-02", "2001-07-02", "2001-10-01"]
        assert [str(act) for act in actual1] == expected1

        inst2 = FinancialInstrument(
            self.helper_inst_dict("irs", "YR", "1"), self.settings
        )
        inst2.spot_date = _RHDate(self.spot_date)
        actual2 = inst2._calc_schedule_tenor()
        expected2 = ["2001-04-02", "2001-07-02", "2001-10-01", "2002-01-02"]
        assert [str(act) for act in actual2] == expected2

        with pytest.raises(
            ValueError,
            match="Input Error: unit should be DY, WK, MO or YR, got XX.",
        ):
            inst3 = FinancialInstrument(
                self.helper_inst_dict("irs", "XX", "1"), self.settings
            )

    def test_yearly(self):
        inst1 = FinancialInstrument(
            self.helper_inst_dict("ois", "DY", "8"), self.settings
        )
        assert str(inst1._calc_schedule_yearly()[0]) == str(
            inst1.maturity_date
        )

        inst2 = FinancialInstrument(
            self.helper_inst_dict("ois", "WK", "8"), self.settings
        )
        assert str(inst2._calc_schedule_yearly()[0]) == str(
            inst2.maturity_date
        )

        inst3 = FinancialInstrument(
            self.helper_inst_dict("ois", "MO", "6"), self.settings
        )
        assert str(inst3._calc_schedule_yearly()[0]) == str(
            inst3.maturity_date
        )

        inst4 = FinancialInstrument(
            self.helper_inst_dict("ois", "MO", "18"), self.settings
        )
        actual4 = inst4._calc_schedule_yearly()
        expected4 = ["2001-07-03", "2002-07-03"]
        assert [str(act) for act in actual4] == expected4

        inst5 = FinancialInstrument(
            self.helper_inst_dict("ois", "YR", "1"), self.settings
        )
        assert str(inst5._calc_schedule_yearly()[0]) == str(
            inst5.maturity_date
        )

        inst6 = FinancialInstrument(
            self.helper_inst_dict("ois", "YR", "3"), self.settings
        )
        actual6 = inst6._calc_schedule_yearly()
        expected6 = ["2002-01-03", "2003-01-03", "2004-01-05"]
        assert [str(act) for act in actual6] == expected6


class TestAttributes:
    today1 = "2001-01-01"
    today2 = "2001-01-29"
    today3 = "2001-01-31"

    def test_depo(self):
        inst_dict = {
            "insttype": "deposit",
            "quote": "0.02",
            "mat_no": "3",
            "mat_unit": "MO",
        }

        depo1 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert depo1._calendar == "TARGET"
        assert str(depo1.spot_date) == "2001-01-03"
        assert str(depo1.maturity_date) == "2001-04-03"
        assert (
            str(type(depo1._fixing))
            == "<class 'pyratehike.instrument._FixingDeposit'>"
        )
        assert (
            str(type(depo1._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(depo1._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(depo1._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        depo2 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today2, currency="EUR")
        )
        assert depo2._calendar == "TARGET"
        assert str(depo2.spot_date) == "2001-01-31"
        assert str(depo2.maturity_date) == "2001-04-30"
        assert (
            str(type(depo2._fixing))
            == "<class 'pyratehike.instrument._FixingDeposit'>"
        )
        assert (
            str(type(depo2._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(depo2._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(depo2._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        depo3 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="GBP")
        )
        assert depo3._calendar == "UK"
        assert str(depo3.spot_date) == "2001-01-01"
        assert str(depo3.maturity_date) == "2001-04-02"
        assert (
            str(type(depo3._fixing))
            == "<class 'pyratehike.instrument._FixingDeposit'>"
        )
        assert (
            str(type(depo3._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(depo3._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(depo3._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        depo4 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today3, currency="GBP")
        )
        assert depo4._calendar == "UK"
        assert str(depo4.spot_date) == "2001-01-31"
        assert str(depo4.maturity_date) == "2001-04-30"
        assert (
            str(type(depo4._fixing))
            == "<class 'pyratehike.instrument._FixingDeposit'>"
        )
        assert (
            str(type(depo4._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(depo4._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(depo4._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        inst_dict["mat_unit"] = "DY"
        depo5 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert depo5._calendar == "TARGET"
        assert str(depo5.spot_date) == "2001-01-03"
        assert str(depo5.maturity_date) == "2001-01-08"
        assert (
            str(type(depo5._fixing))
            == "<class 'pyratehike.instrument._FixingDeposit'>"
        )
        assert (
            str(type(depo5._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(depo5._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(depo5._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustFollow'>"
        )

    def test_fra(self):
        inst_dict = {
            "insttype": "fra",
            "quote": "0.02",
            "mat_no": "3",
            "mat_unit": "MO",
            "start_no": "3",
            "start_unit": "MO",
        }

        fra1 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert fra1._calendar == "TARGET"
        assert str(fra1.spot_date) == "2001-01-03"
        assert str(fra1.start_date) == "2001-04-03"
        assert str(fra1.maturity_date) == "2001-07-03"
        assert (
            str(type(fra1._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(fra1._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(fra1._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(fra1._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        fra2 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today2, currency="EUR")
        )
        assert fra2._calendar == "TARGET"
        assert str(fra2.spot_date) == "2001-01-31"
        assert str(fra2.start_date) == "2001-04-30"
        assert str(fra2.maturity_date) == "2001-07-31"
        assert (
            str(type(fra2._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(fra2._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(fra2._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(fra2._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        fra3 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="GBP")
        )
        assert fra3._calendar == "UK"
        assert str(fra3.spot_date) == "2001-01-01"
        assert str(fra3.start_date) == "2001-04-02"
        assert str(fra3.maturity_date) == "2001-07-02"
        assert (
            str(type(fra3._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(fra3._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(fra3._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(fra3._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        fra4 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today3, currency="GBP")
        )
        assert fra4._calendar == "UK"
        assert str(fra4.spot_date) == "2001-01-31"
        assert str(fra4.start_date) == "2001-04-30"
        assert str(fra4.maturity_date) == "2001-07-31"
        assert (
            str(type(fra4._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(fra4._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(fra4._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(fra4._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

    def test_future(self):
        inst_dict = {
            "insttype": "future",
            "quote": "0.02",
            "mat_no": "3",
            "mat_unit": "MO",
            "start_no": "3",
            "start_unit": "MO",
        }

        future1 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert future1._calendar == "TARGET"
        assert str(future1.spot_date) == "2001-01-03"
        assert str(future1.start_date) == "2001-04-18"
        assert str(future1.maturity_date) == "2001-07-18"
        assert (
            str(type(future1._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(future1._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(future1._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateFuture'>"
        )
        assert (
            str(type(future1._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        future2 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today2, currency="EUR")
        )
        assert future2._calendar == "TARGET"
        assert str(future2.spot_date) == "2001-01-31"
        assert str(future2.start_date) == "2001-04-18"
        assert str(future2.maturity_date) == "2001-07-18"
        assert (
            str(type(future2._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(future2._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(future2._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateFuture'>"
        )
        assert (
            str(type(future2._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        future3 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="GBP")
        )
        assert future3._calendar == "UK"
        assert str(future3.spot_date) == "2001-01-01"
        assert str(future3.start_date) == "2001-04-18"
        assert str(future3.maturity_date) == "2001-07-18"
        assert (
            str(type(future3._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(future3._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(future3._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateFuture'>"
        )
        assert (
            str(type(future3._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        future4 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today3, currency="GBP")
        )
        assert future4._calendar == "UK"
        assert str(future4.spot_date) == "2001-01-31"
        assert str(future4.start_date) == "2001-04-18"
        assert str(future4.maturity_date) == "2001-07-18"
        assert (
            str(type(future4._fixing))
            == "<class 'pyratehike.instrument._FixingFRA'>"
        )
        assert (
            str(type(future4._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(future4._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateFuture'>"
        )
        assert (
            str(type(future4._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

    def test_ois(self):
        inst_dict = {
            "insttype": "ois",
            "quote": "0.02",
            "mat_no": "3",
            "mat_unit": "MO",
        }

        ois1 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert ois1._calendar == "TARGET"
        assert str(ois1.spot_date) == "2001-01-03"
        assert str(ois1.maturity_date) == "2001-04-03"
        assert str(ois1.payment_schedule[0]) == str(ois1.maturity_date)
        assert (
            str(type(ois1._fixing))
            == "<class 'pyratehike.instrument._FixingOIS'>"
        )
        assert (
            str(type(ois1._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(ois1._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(ois1._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        ois2 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today2, currency="EUR")
        )
        assert ois2._calendar == "TARGET"
        assert str(ois2.spot_date) == "2001-01-31"
        assert str(ois2.maturity_date) == "2001-04-30"
        assert str(ois2.payment_schedule[0]) == str(ois2.maturity_date)
        assert (
            str(type(ois2._fixing))
            == "<class 'pyratehike.instrument._FixingOIS'>"
        )
        assert (
            str(type(ois2._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(ois2._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(ois2._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        ois3 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="GBP")
        )
        assert ois3._calendar == "UK"
        assert str(ois3.spot_date) == "2001-01-01"
        assert str(ois3.maturity_date) == "2001-04-02"
        assert str(ois3.payment_schedule[0]) == str(ois3.maturity_date)
        assert (
            str(type(ois3._fixing))
            == "<class 'pyratehike.instrument._FixingOIS'>"
        )
        assert (
            str(type(ois3._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(ois3._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(ois3._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        ois4 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today3, currency="GBP")
        )
        assert ois4._calendar == "UK"
        assert str(ois4.spot_date) == "2001-01-31"
        assert str(ois4.maturity_date) == "2001-04-30"
        assert str(ois4.payment_schedule[0]) == str(ois4.maturity_date)
        assert (
            str(type(ois4._fixing))
            == "<class 'pyratehike.instrument._FixingOIS'>"
        )
        assert (
            str(type(ois4._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(ois4._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(ois4._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        inst_dict["mat_unit"] = "DY"
        ois5 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert ois5._calendar == "TARGET"
        assert str(ois5.spot_date) == "2001-01-03"
        assert str(ois5.maturity_date) == "2001-01-08"
        assert str(ois5.payment_schedule[0]) == str(ois5.maturity_date)
        assert (
            str(type(ois5._fixing))
            == "<class 'pyratehike.instrument._FixingOIS'>"
        )
        assert (
            str(type(ois5._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(ois5._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(ois5._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustFollow'>"
        )

        inst_dict["mat_unit"] = "YR"
        ois6 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert ois6._calendar == "TARGET"
        assert str(ois6.spot_date) == "2001-01-03"
        assert str(ois6.maturity_date) == "2004-01-05"
        assert [str(d) for d in ois6.payment_schedule] == [
            "2002-01-03",
            "2003-01-03",
            "2004-01-05",
        ]
        assert (
            str(type(ois6._fixing))
            == "<class 'pyratehike.instrument._FixingOIS'>"
        )
        assert (
            str(type(ois6._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct360'>"
        )
        assert (
            str(type(ois6._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(ois6._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

    def test_irs(self):
        inst_dict = {
            "insttype": "irs",
            "quote": "0.02",
            "tenor_m": "6",
            "mat_no": "6",
            "mat_unit": "MO",
        }

        irs1 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert irs1._calendar == "TARGET"
        assert str(irs1.spot_date) == "2001-01-03"
        assert str(irs1.maturity_date) == "2001-07-03"
        assert str(irs1.fix_schedule[0]) == str(irs1.maturity_date)
        assert str(irs1.float_schedule[0]) == str(irs1.maturity_date)
        assert (
            str(type(irs1._fixing))
            == "<class 'pyratehike.instrument._FixingIRS'>"
        )
        assert (
            str(type(irs1._daycounter))
            == "<class 'pyratehike._date_arithmetic._Daycount30E360'>"
        )
        assert (
            str(type(irs1._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(irs1._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        irs2 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today2, currency="EUR")
        )
        assert irs2._calendar == "TARGET"
        assert str(irs2.spot_date) == "2001-01-31"
        assert str(irs2.maturity_date) == "2001-07-31"
        assert str(irs2.fix_schedule[0]) == str(irs2.maturity_date)
        assert str(irs2.float_schedule[0]) == str(irs2.maturity_date)
        assert (
            str(type(irs2._fixing))
            == "<class 'pyratehike.instrument._FixingIRS'>"
        )
        assert (
            str(type(irs2._daycounter))
            == "<class 'pyratehike._date_arithmetic._Daycount30E360'>"
        )
        assert (
            str(type(irs2._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(irs2._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        irs3 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="GBP")
        )
        assert irs3._calendar == "UK"
        assert str(irs3.spot_date) == "2001-01-01"
        assert str(irs3.maturity_date) == "2001-07-02"
        assert str(irs3.fix_schedule[0]) == str(irs3.maturity_date)
        assert str(irs3.float_schedule[0]) == str(irs3.maturity_date)
        assert (
            str(type(irs3._fixing))
            == "<class 'pyratehike.instrument._FixingIRS'>"
        )
        assert (
            str(type(irs3._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(irs3._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(irs3._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        irs4 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today3, currency="GBP")
        )
        assert irs4._calendar == "UK"
        assert str(irs4.spot_date) == "2001-01-31"
        assert str(irs4.maturity_date) == "2001-07-31"
        assert str(irs4.fix_schedule[0]) == str(irs4.maturity_date)
        assert str(irs4.float_schedule[0]) == str(irs4.maturity_date)
        assert (
            str(type(irs4._fixing))
            == "<class 'pyratehike.instrument._FixingIRS'>"
        )
        assert (
            str(type(irs4._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(irs4._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDateEndOfMonth'>"
        )
        assert (
            str(type(irs4._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        inst_dict["mat_unit"] = "YR"
        inst_dict["mat_no"] = "3"
        irs5 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="EUR")
        )
        assert irs5._calendar == "TARGET"
        assert str(irs5.spot_date) == "2001-01-03"
        assert str(irs5.maturity_date) == "2004-01-05"
        assert [str(d) for d in irs5.fix_schedule] == [
            "2002-01-03",
            "2003-01-03",
            "2004-01-05",
        ]
        assert [str(d) for d in irs5.float_schedule] == [
            "2001-07-03",
            "2002-01-03",
            "2002-07-03",
            "2003-01-03",
            "2003-07-03",
            "2004-01-05",
        ]
        assert (
            str(type(irs5._fixing))
            == "<class 'pyratehike.instrument._FixingIRS'>"
        )
        assert (
            str(type(irs5._daycounter))
            == "<class 'pyratehike._date_arithmetic._Daycount30E360'>"
        )
        assert (
            str(type(irs5._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(irs5._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )

        inst_dict["mat_unit"] = "YR"
        inst_dict["mat_no"] = "3"
        irs6 = FinancialInstrument(
            inst_dict, RHSettings(today_date=self.today1, currency="GBP")
        )
        assert irs6._calendar == "UK"
        assert str(irs6.spot_date) == "2001-01-01"
        assert str(irs6.maturity_date) == "2004-01-02"
        assert [str(d) for d in irs6.fix_schedule] == [
            "2001-07-02",
            "2002-01-02",
            "2002-07-01",
            "2003-01-02",
            "2003-07-01",
            "2004-01-02",
        ]
        assert [str(d) for d in irs6.float_schedule] == [
            "2001-07-02",
            "2002-01-02",
            "2002-07-01",
            "2003-01-02",
            "2003-07-01",
            "2004-01-02",
        ]
        assert (
            str(type(irs6._fixing))
            == "<class 'pyratehike.instrument._FixingIRS'>"
        )
        assert (
            str(type(irs6._daycounter))
            == "<class 'pyratehike._date_arithmetic._DaycountAct365'>"
        )
        assert (
            str(type(irs6._next_date))
            == "<class 'pyratehike._date_arithmetic._NextDate'>"
        )
        assert (
            str(type(irs6._busday_adjuster))
            == "<class 'pyratehike._date_arithmetic._BusdayAdjustModfollow'>"
        )


class TestFixing:
    today = "2001-01-10"
    settings_gbp = RHSettings(
        today_date=today,
        currency="GBP",
        interpolation_data_type="df",
        interpolation_method="linear",
        spot_date=today,
    )
    settings_eur = RHSettings(
        today_date=today,
        currency="EUR",
        interpolation_data_type="df",
        interpolation_method="linear",
        spot_date=today,
    )

    c1 = IRCurve("SONIA", settings_gbp)
    c1._interpolation_method._coefficients = [
        [1, 0.99, 0.99, 0.98, 0.98, 0.97, 0.97, 0.96],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    c1._interpolation_method._times = [0, 0.1, 0.7, 0.9, 1.1, 1.3, 1.6, 1.7]
    c1._interpolation_method.n_pillars_set = 8

    c2 = IRCurve("SONIA", settings_gbp)
    c2._interpolation_method._coefficients = [
        [1, 0.995, 0.995, 0.985, 0.985, 0.975, 0.975, 0.965],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    c2._interpolation_method._times = [0, 0.1, 0.7, 0.9, 1.1, 1.3, 1.6, 1.7]
    c2._interpolation_method.n_pillars_set = 8

    c3 = IRCurve("SONIA", settings_gbp)
    c3._interpolation_method._coefficients = [
        [1, 0.99, 0.99, 0.98, 0.98, 0.97, 0.97, 0.96],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    c3._interpolation_method._times = [0, 0.1, 0.7, 0.9, 1.1, 1.3, 1.6, 1.7]
    c3._interpolation_method.n_pillars_set = 8
    c3._discount_curve = c2

    def test_depo(self):
        inst_dict = {
            "insttype": "deposit",
            "quote": "0.02",
            "mat_no": "6",
            "mat_unit": "MO",
        }
        depo = FinancialInstrument(inst_dict, self.settings_gbp)
        depo._daycounter = _dp_daycount.dispatch("30E/360")
        f1 = depo.fixing(self.c1)
        f3 = depo.fixing(self.c3)
        assert f1 == (1 / 0.99 - 1) * 2
        assert f3 == (1 / 0.99 - 1) * 2

    def test_fra(self):
        inst_dict = {
            "insttype": "fra",
            "quote": "0.02",
            "start_no": "6",
            "start_unit": "MO",
            "mat_no": "6",
            "mat_unit": "MO",
        }
        fra = FinancialInstrument(inst_dict, self.settings_gbp)
        fra._daycounter = _dp_daycount.dispatch("30E/360")
        f1 = fra.fixing(self.c1)
        f3 = fra.fixing(self.c3)
        assert f1 == (0.99 / 0.98 - 1) * 2
        assert f3 == (0.99 / 0.98 - 1) * 2

    def test_future(self):
        inst_dict = {
            "insttype": "future",
            "quote": "0.02",
            "start_no": "6",
            "start_unit": "MO",
            "mat_no": "6",
            "mat_unit": "MO",
        }
        future = FinancialInstrument(inst_dict, self.settings_gbp)
        future._daycounter = _dp_daycount.dispatch("30E/360")
        future.start_date = _RHDate("2001-07-10")
        future.maturity_date = _RHDate("2002-01-10")
        f1 = future.fixing(self.c1)
        f3 = future.fixing(self.c3)
        assert f1 == (0.99 / 0.98 - 1) * 2
        assert f3 == (0.99 / 0.98 - 1) * 2

    def test_ois(self):
        inst_dict = {
            "insttype": "ois",
            "quote": "0.02",
            "mat_no": "18",
            "mat_unit": "MO",
        }
        ois = FinancialInstrument(inst_dict, self.settings_gbp)
        ois._daycounter = _dp_daycount.dispatch("30E/360")
        f1 = ois.fixing(self.c1)
        f3 = ois.fixing(self.c3)
        assert f1 == (1 - 0.97) / (0.5 * 0.99 + 0.97)
        assert f3 == (1 - 0.97) / (0.5 * 0.99 + 0.97)

    def test_irs_gbp(self):
        inst_dict = {
            "insttype": "irs",
            "quote": "0.02",
            "mat_no": "2",
            "tenor_m": "6",
            "mat_unit": "YR",
        }
        irs = FinancialInstrument(inst_dict, self.settings_gbp)
        irs._daycounter = _dp_daycount.dispatch("30E/360")
        f1 = irs.fixing(self.c1)
        f3 = irs.fixing(self.c3)
        assert f1 == (
            (1 / 0.99 - 1) * 0.99
            + (0.99 / 0.98 - 1) * 0.98
            + (0.98 / 0.97 - 1) * 0.97
            + (0.97 / 0.96 - 1) * 0.96
        ) / (0.5 * (0.99 + 0.98 + 0.97 + 0.96))
        assert f3 == (
            (1 / 0.99 - 1) * 0.995
            + (0.99 / 0.98 - 1) * 0.985
            + (0.98 / 0.97 - 1) * 0.975
            + (0.97 / 0.96 - 1) * 0.965
        ) / (0.5 * (0.995 + 0.985 + 0.975 + 0.965))

    def test_irs_eur(self):
        inst_dict = {
            "insttype": "irs",
            "quote": "0.02",
            "mat_no": "2",
            "tenor_m": "6",
            "mat_unit": "YR",
        }
        irs = FinancialInstrument(inst_dict, self.settings_eur)
        irs.spot_date = _RHDate("2001-01-10")
        irs.maturity_date = _RHDate("2003-01-10")
        irs.fix_schedule = [_RHDate("2002-01-10"), _RHDate("2003-01-10")]
        irs.float_schedule = [
            _RHDate("2001-07-10"),
            _RHDate("2002-01-10"),
            _RHDate("2002-07-10"),
            _RHDate("2003-01-10"),
        ]
        f1 = irs.fixing(self.c1)
        f3 = irs.fixing(self.c3)
        assert f1 == (
            (1 / 0.99 - 1) * 0.99
            + (0.99 / 0.98 - 1) * 0.98
            + (0.98 / 0.97 - 1) * 0.97
            + (0.97 / 0.96 - 1) * 0.96
        ) / (0.98 + 0.96)
        assert f3 == (
            (1 / 0.99 - 1) * 0.995
            + (0.99 / 0.98 - 1) * 0.985
            + (0.98 / 0.97 - 1) * 0.975
            + (0.97 / 0.96 - 1) * 0.965
        ) / (0.985 + 0.965)
