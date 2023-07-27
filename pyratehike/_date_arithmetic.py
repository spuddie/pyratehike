"""module with helper functions for date arithmetic"""

from datetime import date, timedelta
from typing import TYPE_CHECKING, List, Optional, Union

from pyratehike._general import _check_inputs, _Dispatcher
from pyratehike._holiday_offset import _holiday_offset

if TYPE_CHECKING:
    from pyratehike.curve import IRCurve
    from pyratehike.instrument import FinancialInstrument


__all__: List[str] = []


class _RHDate:
    """class representing a date within pyratehike.

    implementation note: hesitated between extending date, or using a
    date member; chosen for the latter.
    """

    __slots__ = ("_datum",)
    _datum: date

    def __init__(
        self, date_string: Optional[str] = None, date_: Optional[date] = None
    ) -> None:
        """constructor for _RHDate.

        precedence : date_string, date_. One of the two needs to be
        provided.

        parameters
        ----------
        date_string : str, optional
            a date, formatted as an ISO string
        date_ : date, optional
            a date object

        returns
        -------
        None
        """

        if date_string is not None:
            self._datum: date = date.fromisoformat(date_string)
        elif date_ is not None:
            self._datum = date_
        else:
            raise ValueError(
                "_RHDate: either date_string or date needs to be set."
            )

    @property
    def date(self) -> date:
        """getter method for the date.

        parameters
        ----------
        (no parameters)

        returns
        -------
        date
            the date embedded in the object
        """

        return self._datum

    @property
    def day(self) -> int:
        """getter method for the day-of-month.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the day-of-month of the date embedded in the object
        """

        return self.date.day

    @property
    def month(self) -> int:
        """getter method for the month.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the month of the date embedded in the object
        """

        return self.date.month

    @property
    def weekday(self) -> int:
        """getter method for the weekday.

        monday = 1, sunday = 7

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the weekday of the date embedded in the object
        """

        return self.date.isoweekday()

    @property
    def year(self) -> int:
        """getter method for the year.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the year of the date embedded in the object
        """

        return self.date.year

    def __str__(self) -> str:
        """convert the object to a string.

        calls str on the member object of type date, which represents
        the date as yyyy-mm-dd.

        parameters
        ----------
        (no parameters)

        returns
        -------
        str
            the date embedded in the object represented as string
        """

        return str(self.date)

    def add_days(self, offset: int) -> "_RHDate":
        """add a number of days to an _RHDate object.

        parameters
        ----------
        offset : int
            the offset in days to be applied

        returns
        -------
        _RHDate
            the shifted date
        """

        return self.add_delta(timedelta(days=offset))

    def add_delta(self, offset: timedelta) -> "_RHDate":
        """add a general offset to an _RHDate object.

        parameters
        ----------
        offset : timedelta
            the offset to be applied

        returns
        -------
        _RHDate
            the shifted date
        """

        return _RHDate(date_=self.date + offset)

    def sub_rhdate(self, start: "_RHDate") -> int:
        """the difference between this _RHDate and another _RHDate in
        days

        parameters
        ----------
        start : _RHDate
            the start date

        returns
        -------
        int
            the difference in days
        """

        return (self.date - start.date).days


class _Period:
    """class representing a period, which is an integer number of
    days, weeks, months or years.
    """

    # pylint: disable=too-few-public-methods

    __slots__ = (
        "number",
        "unit",
    )
    number: int
    unit: str

    def __init__(self, number: int, unit: str) -> None:
        """constructor for _Period.

        parameters
        ----------
        number : int
            the number of units represented by the object
        unit : str
            the unit of the period, can be "DY", "WK", "MO", "YR"

        returns
        -------
        None
        """

        _check_inputs("unit", ["DY", "WK", "MO", "YR"], unit)
        self.number = number
        self.unit = unit


class _BusdayAdjust:
    """class to do business day adjustments.

    Abstract Base Class
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def busday_adjust(calendar: str, datum: _RHDate) -> _RHDate:
        """function to adjust a date to a business date.

        parameters
        ----------
        calendar : str
            which calendar to use to check for holidays
        datum : _RHDate
            the date to adjust

        returns
        -------
        _RHDate
            the adjusted date
        """

        raise NotImplementedError


class _BusdayAdjustFollow(_BusdayAdjust):
    """class to do business day adjustments.

    Implements the Following convention.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def busday_adjust(calendar: str, datum: _RHDate) -> _RHDate:
        weekday: int = datum.weekday
        if weekday < 6:
            result: _RHDate = datum
        else:
            result = datum.add_days(8 - weekday)
        hol_offset: Optional[int] = _holiday_offset(calendar, result)
        if hol_offset is not None:
            result = result.add_days(hol_offset)
        return result


class _BusdayAdjustModfollow(_BusdayAdjust):
    """class to do business day adjustments.

    Implements the ModFollowing convention.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def busday_adjust(calendar: str, datum: _RHDate) -> _RHDate:
        result: _RHDate = _BusdayAdjustFollow.busday_adjust(calendar, datum)
        if result.month != datum.month:
            weekday: int = datum.weekday
            result = datum.add_days(5 - weekday)
            hol_offset: Optional[int] = _holiday_offset(calendar, result)
            while hol_offset is not None:
                result = result.add_days(-1)
                hol_offset = _holiday_offset(calendar, result)
        return result


_dp_busday_adjust: _Dispatcher[_BusdayAdjust] = _Dispatcher(_BusdayAdjust())
"""dispatcher to choose the method for business day adjustments.

_dp_busday_adjust.dispatch("follow") returns the class 
_BusdayAdjustFollow; _dp_busday_adjust.dispatch("modfollow") 
returns the class _BusdayAdjustModFollow; 
"""
_dp_busday_adjust.set_method("follow", _BusdayAdjustFollow())
_dp_busday_adjust.set_method("modfollow", _BusdayAdjustModfollow())


class _NextDate:
    """class to move dates forward.

    2 specialized subclasses exist: _NextDateEndOfMonth and
    _NextDateFuture; this class implements the default treatment.
    """

    @staticmethod
    def calc_next_date(
        object_: Union["FinancialInstrument", "IRCurve"],
        datum: _RHDate,
        period: _Period,
        length: int = 1,
        adjust: bool = True,
    ) -> List[_RHDate]:
        """move dates forward

        the first parameter is an object, which needs to have a
        "busday_adjust" function.

        parameters
        ----------
        object_ : FinancialInstrument or IRCurve
            the object for which to do the calculations
        datum : _RHDate
            the date to start from
        period : _Period
            the period to move
        length : int, optional
            the length of the output, default: 1
        adjust : bool, optional
            should the results be adjusted to fall on business days?
            default: True

        returns
        -------
        list of _RHDate
            a list of dates of length "length", with each date one
            period further in time, adjusted to be a business day if
            requested.
        """

        if period.unit == "DY":
            results: List[_RHDate] = [
                datum.add_delta(timedelta(days=period.number * (k + 1)))
                for k in range(length)
            ]
        elif period.unit == "WK":
            results = [
                datum.add_delta(timedelta(weeks=period.number * (k + 1)))
                for k in range(length)
            ]
        elif period.unit == "MO":
            months: List[int] = [
                (datum.month - 1 + period.number * (k + 1)) % 12 + 1
                for k in range(length)
            ]
            years: List[int] = [
                datum.year + (datum.month - 1 + period.number * (k + 1)) // 12
                for k in range(length)
            ]
            results = [
                _RHDate(date_=date(year, month, datum.day))
                for year, month in zip(years, months)
            ]
        elif period.unit == "YR":
            results = [
                _RHDate(
                    date_=date(
                        datum.year + period.number * (k + 1),
                        datum.month,
                        datum.day,
                    )
                )
                for k in range(length)
            ]
        if adjust:
            results = [object_.busday_adjust(r) for r in results]
        return results

    @staticmethod
    def apply_spot_lag(
        object_: Union["FinancialInstrument", "IRCurve"],
        today: _RHDate,
        currency: str,
    ) -> _RHDate:
        """method to apply the spot lag, which is 2 business days for
        EUR and 0 days for GBP

        parameters
        ----------
        object_ : FinancialInstrument or IRCurve
            the object for which to do the calculations
        today : _RHDate
            the date to start from
        currency : str
            the currency of object_

        returns
        -------
        _RHDate
            the spot date
        """

        spot_date: _RHDate = today
        if currency == "EUR":
            period: _Period = _Period(1, "DY")
            spot_date = object_.next_date(spot_date, period)[0]
            spot_date = object_.next_date(spot_date, period)[0]
        return spot_date


class _NextDateEndOfMonth(_NextDate):
    """class to move dates forward.

    This implementation moves dates to the end of a month.
    """

    @staticmethod
    def calc_next_date(
        object_: Union["FinancialInstrument", "IRCurve"],
        datum: _RHDate,
        period: _Period,
        length: int = 1,
        adjust: bool = True,
    ) -> List[_RHDate]:
        if period.unit == "MO":
            months: List[int] = [
                (datum.month + period.number * (k + 1)) % 12 + 1
                for k in range(length)
            ]
            years: List[int] = [
                datum.year + (datum.month + period.number * (k + 1)) // 12
                for k in range(length)
            ]
            results: List[_RHDate] = [
                _RHDate(date_=date(year, month, 1)).add_days(-1)
                for year, month in zip(years, months)
            ]
        elif period.unit == "YR":
            year: int = datum.year
            if datum.month == 12:
                year = year + 1
            results = [
                _RHDate(
                    date_=date(
                        year + period.number * (k + 1), datum.month % 12 + 1, 1
                    )
                ).add_days(-1)
                for k in range(length)
            ]
        if adjust:
            results = [object_.busday_adjust(r) for r in results]
        return results


class _NextDateFuture(_NextDate):
    """class to move dates forward.

    This implementation moves dates to the third wednesday of a month,
    as is necessary for futures.
    """

    @staticmethod
    def calc_next_date(
        object_: Union["FinancialInstrument", "IRCurve"],
        datum: _RHDate,
        period: _Period,
        length: int = 1,
        adjust: bool = True,
    ) -> List[_RHDate]:
        if period.unit == "MO":
            months: List[int] = [
                (datum.month - 1 + period.number * (k + 1)) % 12 + 1
                for k in range(length)
            ]
            years: List[int] = [
                datum.year + (datum.month - 1 + period.number * (k + 1)) // 12
                for k in range(length)
            ]
            results: List[_RHDate] = [
                _RHDate(date_=date(year, month, 21))
                for year, month in zip(years, months)
            ]
        elif period.unit == "YR":
            results = [
                _RHDate(
                    date_=date(
                        datum.year + period.number * (k + 1),
                        (datum.month - 1) % 12 + 1,
                        21,
                    )
                ).add_days(-1)
                for k in range(length)
            ]
        results = [r.add_days(-((r.weekday - 3) % 7)) for r in results]
        if adjust:
            results = [object_.busday_adjust(r) for r in results]
        return results


_dp_next_date: _Dispatcher[_NextDate] = _Dispatcher(_NextDate())
"""dispatcher to choose the method for moving dates forward.

_dp_next_date.dispatch() returns the default class _NextDate; 
_dp_next_date.dispatch("end_of_month") returns the class 
_NextDateEndOfMonth; _dp_next_date.dispatch("future") 
returns the class _NextDateFuture.
"""
_dp_next_date.set_method("end_of_month", _NextDateEndOfMonth())
_dp_next_date.set_method("future", _NextDateFuture())


class _Daycount:  # pragma: no cover
    """helper class to calculate year fractions

    Abstract Base Class.
    """

    @staticmethod
    def daycount(date_start: _RHDate, date_end: _RHDate) -> float:
        """method to calculate year fractions.

        parameters
        ----------
        date_start : _RHDate
            the start date of the period
        date_end : _RHDate
            the end date of the period

        returns
        -------
        float
            the year fraction

        examples
        --------
        >>> o_act365 = _dp_daycount.dispatch("ACT/365")
        >>> d1 = o_act365.daycount(_RHDate("2022-02-22"),_RHDate("2022-12-10"))
        >>> o_act360 = _dp_daycount.dispatch("ACT/360")
        >>> d2 = o_act360.daycount(_RHDate("2022-02-22"),_RHDate("2022-12-10"))
        >>> o_30e360 = _dp_daycount.dispatch("30E/360")
        >>> d3 = o_30e360.daycount(_RHDate("2022-02-22"),_RHDate("2022-12-10"))
        """

        raise NotImplementedError

    @staticmethod
    def get_end_date(date_start: _RHDate, yearfraction: float) -> _RHDate:
        """method to move a date forward by a year fraction

        parameters
        ----------
        date_start : _RHDate
            the start date of the period
        yearfraction : float
            the year fraction of the period

        returns
        -------
        _RHDate
            the end date of the period
        """

        raise NotImplementedError


class _DaycountAct365(_Daycount):
    """helper class to calculate year fractions

    Implementation for convention ACT/365: the actual number of days
    in the period, divided by 365.
    """

    @staticmethod
    def daycount(date_start: _RHDate, date_end: _RHDate) -> float:
        return date_end.sub_rhdate(date_start) / 365

    @staticmethod
    def get_end_date(date_start: _RHDate, yearfraction: float) -> _RHDate:
        return date_start.add_days(round(yearfraction * 365))


class _DaycountAct360(_Daycount):
    """helper class to calculate year fractions

    Implementation for convention ACT/360: the actual number of days
    in the period, divided by 360.
    """

    # pylint: disable=abstract-method

    @staticmethod
    def daycount(date_start: _RHDate, date_end: _RHDate) -> float:
        return date_end.sub_rhdate(date_start) / 360


class _Daycount30E360(_Daycount):
    """helper class to calculate year fractions

    Implementation for convention 30E/365:
    year(date_to) - year(date_from)
    + 1/12 (month(date_to) - month(date_from))
    + 1/360 (day(date_to) - day(date_from));
    when the day = 31, it is corrected to 30.
    """

    # pylint: disable=abstract-method

    @staticmethod
    def daycount(date_start: _RHDate, date_end: _RHDate) -> float:
        year_start = date_start.year
        month_start = date_start.month
        day_start = date_start.day
        year_end = date_end.year
        month_end = date_end.month
        day_end = date_end.day
        if day_start == 31:
            day_start = 30
        if day_end == 31:
            day_end = 30
        return (
            year_end
            - year_start
            + (month_end - month_start) / 12
            + (day_end - day_start) / 360
        )


_dp_daycount: _Dispatcher[_Daycount] = _Dispatcher(_Daycount())
"""dispatcher to choose the convention for calculating year fractions.

_dp_daycount.dispatch("ACT/365") returns the class _DaycountAct365; 
_dp_daycount.dispatch("ACT/360") returns the class _DaycountAct360; 
_dp_daycount.dispatch("30E/360") returns the class _Daycount30E360. 
"""
_dp_daycount.set_method("ACT/365", _DaycountAct365())
_dp_daycount.set_method("ACT/360", _DaycountAct360())
_dp_daycount.set_method("30E/360", _Daycount30E360())
