"""definition of FinancialInstrument and Syntheticinstrument,
together with some helper classes."""

from typing import TYPE_CHECKING, Dict, List

from pyratehike._date_arithmetic import (
    _BusdayAdjust,
    _Daycount,
    _dp_busday_adjust,
    _dp_daycount,
    _dp_next_date,
    _NextDate,
    _Period,
    _RHDate,
)
from pyratehike._general import _check_inputs, _Dispatcher
from pyratehike.parameters_settings import RHSettings

if TYPE_CHECKING:
    from pyratehike.curve import IRCurve

__all__: List[str] = ["FinancialInstrument", "SyntheticInstrument"]


class _Fixing:  # pragma: no cover
    """class providing a fixing method.

    Abstract Base Class
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def fixing(instrument: "FinancialInstrument", curve: "IRCurve") -> float:
        """fixing of a Financial Instrument.

        Determining the fair insterest rate for the instrument based
        on an interest rate curve.


        parameters
        ----------
        instrument : FinancialInstrument
            a financial instrument
        curve : IRCurve
            an interest rate curve

        returns
        -------
        float
            the fair interest rate
        """

        raise NotImplementedError


class _FixingDeposit(_Fixing):
    """class providing a fixing method for deposits."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def fixing(instrument: "FinancialInstrument", curve: "IRCurve") -> float:
        dates: List[_RHDate] = [instrument.spot_date, instrument.maturity_date]
        discount_factors: List[float] = curve.get_discount_factors(dates=dates)
        yearfraction: float = instrument.daycount(dates)[0]
        return (discount_factors[0] / discount_factors[1] - 1) / yearfraction


class _FixingFRA(_Fixing):
    """class providing a fixing method for Forward Rate Agreements and
    futures."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def fixing(instrument: "FinancialInstrument", curve: "IRCurve") -> float:
        dates: List[_RHDate] = [
            instrument.start_date,
            instrument.maturity_date,
        ]
        discount_factors: List[float] = curve.get_discount_factors(dates=dates)
        yearfraction: float = instrument.daycount(dates)[0]
        return (discount_factors[0] / discount_factors[1] - 1) / yearfraction


class _FixingIRS(_Fixing):
    """class providing a fixing method for interest rate swaps."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def fixing(instrument: "FinancialInstrument", curve: "IRCurve") -> float:
        dates_fix: List[_RHDate] = [
            instrument.spot_date
        ] + instrument.fix_schedule
        dates_float: List[_RHDate] = [
            instrument.spot_date
        ] + instrument.float_schedule
        forecast_float_dfs: List[float] = curve.get_discount_factors(
            dates=dates_float
        )
        curve = curve.get_discount_curve()
        discount_fix_dfs: List[float] = curve.get_discount_factors(
            dates=instrument.fix_schedule
        )
        discount_float_dfs: List[float] = curve.get_discount_factors(
            dates=instrument.float_schedule
        )
        yearfractions: List[float] = instrument.daycount(dates_fix)
        accrual_factor: float = sum(
            dfd * yf for dfd, yf in zip(discount_fix_dfs, yearfractions)
        )
        discounted_cashflows: float = sum(
            (ffd1 / ffd2 - 1) * dfd
            for ffd1, ffd2, dfd in zip(
                forecast_float_dfs[:-1],
                forecast_float_dfs[1:],
                discount_float_dfs,
            )
        )
        return discounted_cashflows / accrual_factor


class _FixingOIS(_Fixing):
    """class providing a fixing method for overnight interest swaps."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def fixing(instrument: "FinancialInstrument", curve: "IRCurve") -> float:
        dates: List[_RHDate] = [
            instrument.spot_date
        ] + instrument.payment_schedule
        discount_factors: List[float] = curve.get_discount_factors(dates=dates)
        yearfractions: List[float] = instrument.daycount(dates)
        accrual_factor: float = sum(
            df * yf for df, yf in zip(discount_factors[1:], yearfractions)
        )
        return (discount_factors[0] - discount_factors[-1]) / accrual_factor


_dp_fixing: _Dispatcher[_Fixing] = _Dispatcher(_Fixing())
"""dispatcher to choose the fixing method.

_dp_spline_correction.dispatch("xxx") returns the class for instrument type
xxx = deposit, fra, future, irs, or ois.
"""
_dp_fixing.set_method("deposit", _FixingDeposit())
_dp_fixing.set_method("fra", _FixingFRA())
_dp_fixing.set_method("future", _FixingFRA())
_dp_fixing.set_method("irs", _FixingIRS())
_dp_fixing.set_method("ois", _FixingOIS())


class FinancialInstrument:
    """represents a financial instrument.

    examples
    --------
    >>> settings = RHSettings(
    ...     today_date = "2023-07-06",
    ...     currency = "EUR"
    ... )
    >>> inst_dict = {
    ...     "quote": "0.01",
    ...     "mat_no": "1",
    ...     "mat_unit": "WK",
    ...     "insttype": "deposit",
    ... }
    >>> depo1w = FinancialInstrument(inst_dict, settings)
    """

    # pylint: disable=too-many-instance-attributes

    __slots__ = (
        "_busday_adjuster",
        "_next_date",
        "_calendar",
        "_currency",
        "_daycounter",
        "discount_factor",
        "_fixing",
        "fix_schedule",
        "float_schedule",
        "insttype",
        "maturity_date",
        "_maturity_period",
        "payment_schedule",
        "quote",
        "spot_date",
        "start_date",
        "_start_period",
        "_tenor_months",
        "_today_date",
    )

    _busday_adjuster: _BusdayAdjust
    _next_date: _NextDate
    _calendar: str
    _currency: str
    _daycounter: _Daycount
    discount_factor: float
    _fixing: _Fixing
    fix_schedule: List[_RHDate]
    float_schedule: List[_RHDate]
    insttype: str
    maturity_date: _RHDate
    _maturity_period: _Period
    payment_schedule: List[_RHDate]
    quote: float
    spot_date: _RHDate
    start_date: _RHDate
    _start_period: _Period
    _tenor_months: int
    _today_date: _RHDate

    def __init__(
        self, inst_dict: Dict[str, str], settings: RHSettings
    ) -> None:
        """constructor of FinancialInstrument.

        parameters
        ----------
        inst_dict : dict(str, str)
            dictionary of instrument specific information with the
            following structure:

            quote: the market quote
            mat_no: numeric component of maturity
            mat_unit: unit for maturity (YR, MO, WK, DY)
            insttype: instrument type (deposit, ois, fra, future, irs)
            start_no: numeric component of start delay, for forward
                starting instruments
            start_unit: unit for start delay (YR, MO, WK, DY) for
                forward starting instruments
            tenor_m: tenor in months, for irs

        settings : RHSettings
            global information for the instrument

        returns
        -------
        None
        """

        # pylint: disable=too-many-branches

        # initial next_date & busday_adjust
        self._next_date = _dp_next_date.dispatch()
        self._busday_adjuster = _dp_busday_adjust.dispatch("follow")

        # instrument attributes
        self.insttype = inst_dict["insttype"]
        self.quote = float(inst_dict["quote"])
        self._maturity_period = _Period(
            int(inst_dict["mat_no"]), inst_dict["mat_unit"]
        )
        if self.insttype in ("fra", "future"):
            self._start_period = _Period(
                int(inst_dict["start_no"]), inst_dict["start_unit"]
            )

        # settings
        self._today_date = settings.today_date
        self._currency = settings.currency

        # fixing
        self._fixing = _dp_fixing.dispatch(self.insttype)

        # calendar, daycount
        if self._currency == "EUR":
            self._calendar = "TARGET"
            if self.insttype == "irs":
                self._daycounter = _dp_daycount.dispatch("30E/360")
            else:
                self._daycounter = _dp_daycount.dispatch("ACT/360")
        elif self._currency == "GBP":
            self._calendar = "UK"
            self._daycounter = _dp_daycount.dispatch("ACT/365")

        # spot
        self.spot_date = self._next_date.apply_spot_lag(
            self, self._today_date, self._currency
        )

        # next_date
        if self.insttype == "future":
            self._next_date = _dp_next_date.dispatch("future")
        elif self.spot_date.month != self.busday_adjust(
            self.spot_date.add_days(1)
        ).month and (self._maturity_period.unit in ("YR", "MO")):
            self._next_date = _dp_next_date.dispatch("end_of_month")

        # rolling conventions
        if self._maturity_period.unit in ("DY", "WK"):
            self._busday_adjuster = _dp_busday_adjust.dispatch("follow")
        else:
            self._busday_adjuster = _dp_busday_adjust.dispatch("modfollow")

        # maturity_date, start_date
        if self.insttype in ("fra", "future"):
            if self.insttype == "fra":
                ref_date: _RHDate = self.spot_date
            elif self.insttype == "future":
                ref_date = self._today_date
            self.start_date = self.next_date(ref_date, self._start_period)[0]
            self.maturity_date = self.next_date(
                ref_date,
                _Period(
                    self._maturity_period.number + self._start_period.number,
                    self._maturity_period.unit,
                ),
            )[0]
        else:
            self.maturity_date = self.next_date(
                self.spot_date, self._maturity_period
            )[0]

        # schedule
        if self.insttype == "ois":
            self.payment_schedule = self._calc_schedule_yearly()
        elif self.insttype == "irs":
            self._tenor_months = int(inst_dict["tenor_m"])
            self.float_schedule = self._calc_schedule_tenor()
            if self._currency == "EUR":
                self.fix_schedule = self._calc_schedule_yearly()
            elif self._currency == "GBP":
                self.fix_schedule = self.float_schedule

    def busday_adjust(self, datum: _RHDate) -> _RHDate:
        """move a date to the next business date.

        calls upon the busday_adjust function of the _busday_adjuster
        attribute.

        parameters
        ----------
        datum : _RHDate
            the date to adjust

        returns
        -------
        _RHDate
            the adjusted date
        """

        return self._busday_adjuster.busday_adjust(self._calendar, datum)

    def next_date(
        self,
        datum: _RHDate,
        period: _Period,
        length: int = 1,
        adjust: bool = True,
    ) -> List[_RHDate]:
        """calculate future dates.

        calls upon the calc_next_date function of the _calc_next_date
        attribute.

        parameters
        ----------
        datum : _RHDate
            the date to start from
        period : _Period
            represents the period to move forward
        length : int, optional
            the length of the output list (default: 1)
        adjust : bool, optional
            should the results be adjusted to business days (default: True)

        returns
        -------
        list of _RHDate
            the calculate dates
        """

        return self._next_date.calc_next_date(
            self, datum, period, length, adjust
        )

    def daycount(self, dates: List[_RHDate]) -> List[float]:
        """calculate the year fraction between every element of the
        input list.

        calls upon the daycount function of the _daycounter attribute.

        parameters
        ----------
        dates : list of _RHDate
            the dates

        returns
        -------
        list of float
            the year fractions
        """
        return [
            self._daycounter.daycount(dates[i], dates[i + 1])
            for i in range(len(dates) - 1)
        ]

    def fixing(self, curve: "IRCurve") -> float:
        """fixing of a Financial Instrument.

        Determining the fair insterest rate for the instrument based
        on an interest rate curve.

        parameters
        ----------
        curve : IRCurve
            an interest rate curve

        returns
        -------
        float
            the fair interest rate

        examples
        --------
        >>> from pathlib import Path
        >>> from pyratehike import IRCurve, ListOfInstruments

        >>> settings = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR"
        ... )
        >>> curve_ois = IRCurve("ESTR", settings)
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)

        >>> f1 = list_ois.instruments[5].fixing(curve_ois)

        >>> inst_dict = {
        ...     "quote": "0.01",
        ...     "mat_no": "1",
        ...     "mat_unit": "WK",
        ...     "insttype": "deposit",
        ... }
        >>> depo1w = FinancialInstrument(inst_dict, settings)
        >>> f2 = depo1w.fixing(curve_ois)
        """

        return self._fixing.fixing(self, curve)

    def _calc_schedule_tenor(self) -> List[_RHDate]:
        """calculate payment schedule based on tenor.

        parameters
        ----------
        (no parameters)

        returns
        -------
        list of _RHDate
            the payment schedule
        """

        _check_inputs(
            "_maturity_period.unit", ["MO", "YR"], self._maturity_period.unit
        )
        if self._maturity_period.unit == "MO":
            mat_months: int = self._maturity_period.number
        elif self._maturity_period.unit == "YR":
            mat_months = self._maturity_period.number * 12
        return self.next_date(
            self.spot_date,
            _Period(self._tenor_months, "MO"),
            length=mat_months // self._tenor_months,
        )

    def _calc_schedule_yearly(self) -> List[_RHDate]:
        """calculate yearly payment schedule.

        parameters
        ----------
        (no parameters)

        returns
        -------
        list of _RHDate
            the payment schedule
        """

        if (
            (
                self._maturity_period.unit == "YR"
                and self._maturity_period.number == 1
            )
            or (
                self._maturity_period.unit == "MO"
                and self._maturity_period.number <= 12
            )
            or (self._maturity_period.unit in ("WK", "DY"))
        ):
            return [self.maturity_date]
        _check_inputs(
            "_maturity_period.unit", ["MO", "YR"], self._maturity_period.unit
        )
        if self._maturity_period.unit == "YR":
            return self.next_date(
                self.spot_date,
                _Period(1, self._maturity_period.unit),
                length=self._maturity_period.number,
            )
        # self._maturity_period.unit == "MO"
        # and self._maturity_period.number > 12
        payment_date: List[_RHDate] = self.next_date(
            self.spot_date,
            _Period(
                self._maturity_period.number - 12, self._maturity_period.unit
            ),
        )
        return payment_date + [self.maturity_date]


class SyntheticInstrument(FinancialInstrument):
    """class for synthetic instruments.

    set up as subclass of FinancialInstrument, so that they can easily
    coexist in ListOfInstruments.
    """

    # pylint: disable=super-init-not-called

    def __init__(self, discount_factor: float, maturity_date: _RHDate) -> None:
        """constructor of SyntheticInstrument

        parameters
        ----------
        discount_factor : float
            discount factor
        maturity_date : _RHDate
            the maturity date

        returns
        -------
        None
        """

        self.insttype = "synthetic"
        self.discount_factor = discount_factor
        self.maturity_date = maturity_date
