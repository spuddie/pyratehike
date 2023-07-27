"""definition of an interest rate curve object

This module defines the class IRCurve.
"""

# pylint: disable = too-many-lines

from typing import List, Optional, Tuple

from matplotlib.pyplot import show, subplots, title  # type: ignore [import]
from scipy.optimize import brentq  # type: ignore [import]

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
from pyratehike._general import _Dispatcher
from pyratehike._interpolation import (
    _dp_interpolation_data_type,
    _InterpolationDataType,
    _InterpolationMethod,
)
from pyratehike.instrument import FinancialInstrument
from pyratehike.parameters_settings import RHSettings, rh_params

__all__: List[str] = ["IRCurve"]


class _BootstrapInfo:
    """class _BootstrapInfo

    attributes
    ----------
    discount_factor_convergence : float
        the discount factor update difference in the last iteration
    function_evaluations : int
        the number of function evaluations
    iterations : int
        the number of iterations performed
    """

    # pylint: disable=too-few-public-methods

    __slots__ = (
        "function_evaluations",
        "discount_factor_convergence",
        "iterations",
    )
    discount_factor_convergence: float
    function_evaluations: int
    iterations: int

    def __init__(
        self,
        discount_factor_convergence: float,
        function_evaluations: int,
        iterations: int,
    ) -> None:
        """constructor for class _BootstrapInfo

        parameters
        ----------
        discount_factor_convergence : float
            the discount factor update difference in the last iteration
        function_evaluations : int
            the number of function evaluations
        iterations : int
            the number of iterations performed

        returns
        -------
        None
        """

        self.discount_factor_convergence = discount_factor_convergence
        self.function_evaluations = function_evaluations
        self.iterations = iterations


class _ReAnchorMethod:  # pragma: no cover
    """class for re-anchoring functionality

    Abstract Base Class.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def re_anchor(
        curve: "IRCurve", depo_spot_next: Optional[FinancialInstrument]
    ) -> None:
        """re-anchoring method.

        parameters
        ----------
        curve : IRCurve
            the curve to re-anchor
        depo_spot_next : FinancialInstrument, optional
            the spot-next depo, only used in ReAnchorMethodONTN

        returns
        -------
        None
        """

        raise NotImplementedError


class _ReAnchorMethodNo(_ReAnchorMethod):
    """class for re-anchoring functionality

    This implementation does not re-anchor the curve.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def re_anchor(
        curve: "IRCurve", depo_spot_next: Optional[FinancialInstrument]
    ) -> None:
        curve.spot_date_orig = curve.spot_date


class _ReAnchorMethodDate(_ReAnchorMethod):
    """class for re-anchoring functionality

    This implementation only resets the spot date of the curve to the
    today date, times and discount factors are not changed.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def re_anchor(
        curve: "IRCurve", depo_spot_next: Optional[FinancialInstrument]
    ) -> None:
        curve.spot_date_orig = curve.spot_date
        curve.spot_date = curve.today_date


class _ReAnchorMethod11(_ReAnchorMethod):
    """class for re-anchoring functionality

    This implementation resets the spot date of the curve to the
    today date, and prepends discount factors of 1 on the two business
    days before the original spot date.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def re_anchor(
        curve: "IRCurve", depo_spot_next: Optional[FinancialInstrument]
    ) -> None:
        disc_factors_orig: List[float] = curve.get_discount_factors()
        dates_orig: List[_RHDate] = curve.get_dates()
        curve.spot_date_orig = curve.spot_date
        curve.spot_date = curve.today_date
        tomorrow: _RHDate = curve.next_date(
            curve.today_date,
            _Period(1, "DY"),
        )[0]
        times_new: List[float] = [
            curve.daycount(t) for t in [curve.spot_date, tomorrow] + dates_orig
        ]
        curve.set_times(times_new)
        curve.update_all_discount_factors([1, 1] + disc_factors_orig)


class _ReAnchorMethodONTN(_ReAnchorMethod):
    """class for re-anchoring functionality

    This implementation resets the spot date of the curve to the
    today date, calculates the discount factors for the overnight and
    the spot-next deposit and prepends those to the curve. The other
    discount factors are multiplied by these extra discount factors.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def re_anchor(
        curve: "IRCurve", depo_spot_next: Optional[FinancialInstrument]
    ) -> None:
        if depo_spot_next is None:
            raise ValueError(
                "_AnchorMethodONTN: depo_spot_next cannot be None."
            )
        if depo_spot_next.insttype != "deposit" or str(
            depo_spot_next.spot_date.add_days(1)
        ) != str(depo_spot_next.maturity_date):
            raise ValueError(
                "_AnchorMethodONTN: depo_spot_next needs to be an overnight deposit."
            )
        disc_factors_orig: List[float] = curve.get_discount_factors()
        dates_orig: List[_RHDate] = curve.get_dates()
        curve.spot_date_orig = curve.spot_date
        curve.spot_date = curve.today_date
        tomorrow: _RHDate = curve.next_date(
            curve.today_date,
            _Period(1, "DY"),
        )[0]
        times_new: List[float] = [
            curve.daycount(t) for t in [curve.spot_date, tomorrow] + dates_orig
        ]
        yearfractions = depo_spot_next.daycount(
            [curve.spot_date, tomorrow, curve.spot_date_orig]
        )
        disc_factor_overnight = 1 / (
            depo_spot_next.quote * yearfractions[0] + 1
        )
        disc_factor_tomorrow_next = 1 / (
            depo_spot_next.quote * yearfractions[1] + 1
        )
        curve.set_times(times_new)
        curve.update_all_discount_factors(
            [1, disc_factor_overnight]
            + [
                d * disc_factor_overnight * disc_factor_tomorrow_next
                for d in disc_factors_orig
            ]
        )


_dp_re_anchor_method: _Dispatcher[_ReAnchorMethod] = _Dispatcher(
    _ReAnchorMethod()
)
"""dispatcher to choose the method for re-anchoring.

_dp_re_anchor_method.dispatch("no") returns the class 
_ReAnchorMethodNo; _dp_re_anchor_method.dispatch("date") 
returns the class _ReAnchorMethodDate; 
_dp_re_anchor_method.dispatch("11") returns the class 
_ReAnchorMethod11; _dp_re_anchor_method.dispatch("ONTN") 
returns the class _ReAnchorMethodONTN; 
"""
_dp_re_anchor_method.set_method("no", _ReAnchorMethodNo())
_dp_re_anchor_method.set_method("date", _ReAnchorMethodDate())
_dp_re_anchor_method.set_method("11", _ReAnchorMethod11())
_dp_re_anchor_method.set_method("ONTN", _ReAnchorMethodONTN())


class IRCurve:
    """An IRCurve represents an interest rate curve.

    Its constructor uses a RHSettings object to decide on the
    characteristics. After that, the bootstrap method constructs the
    curve. The main getter methods get_zero_rates,
    get_discount_factors and get_insta_forwards allow to extract
    data.

    examples
    --------
    >>> settings = RHSettings(
    ...     today_date = "2023-07-06",
    ...     interpolation_data_type = "logdf",
    ...     interpolation_method = "linear",
    ...     currency = "EUR"
    ... )
    >>> curve_ois = IRCurve("ESTR", settings)
    """

    # pylint: disable = too-many-instance-attributes

    __slots__ = (
        "_anchoring",
        "bootstrap_info",
        "_calendar",
        "_discount_curve",
        "_interpolation_data_type",
        "_interpolation_method",
        "_name",
        "_settings",
        "spot_date",
        "spot_date_orig",
    )

    _anchoring: _ReAnchorMethod
    bootstrap_info: _BootstrapInfo
    _busday_adjuster: _BusdayAdjust = _dp_busday_adjust.dispatch("follow")
    _calendar: str
    _daycounter: _Daycount = _dp_daycount.dispatch("ACT/365")
    _discount_curve: "IRCurve"
    _name: str
    _interpolation_data_type: _InterpolationDataType
    _interpolation_method: _InterpolationMethod
    _next_date: _NextDate = _dp_next_date.dispatch()
    _settings: RHSettings
    spot_date_orig: _RHDate
    spot_date: _RHDate

    def __init__(self, name: str, settings: RHSettings) -> None:
        """constructor for IRCurve.

        parameters
        ----------
        name : str
            a name for the curve
        settings : RHSettings
            the settings to use

        returns
        -------
        None
        """

        self._name = name
        self._settings = settings
        self._interpolation_data_type = _dp_interpolation_data_type.dispatch(
            self._settings.interpolation_data_type
        )
        self._interpolation_method = _InterpolationMethod(
            self._settings.interpolation_method,
            self._settings.spline_correction,
        )
        if self._settings.currency == "EUR":
            self._calendar = "TARGET"
        elif self._settings.currency == "GBP":
            self._calendar = "UK"
        try:
            self.spot_date = self._settings.spot_date
        except AttributeError:
            self.spot_date = self._next_date.apply_spot_lag(
                self, self._settings.today_date, self._settings.currency
            )
        self._anchoring = _dp_re_anchor_method.dispatch(
            self._settings.re_anchoring
        )

    @property
    def n_pillars(self) -> int:
        """Getter method for _interpolation_method.n_pillars.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the value of _interpolation_method.n_pillars
        """

        return self._interpolation_method.n_pillars

    @property
    def today_date(self) -> _RHDate:
        """Getter method for _settings.today_date.

        parameters
        ----------
        (no parameters)

        returns
        -------
        _RHDate
            the value of _settings.today_date
        """

        return self._settings.today_date

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

        calls upon the calc_next_date function of the _next_date
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

    def daycount(self, target_date: _RHDate) -> float:
        """calculate the year fraction from the spot date to the
        target date.

        calls upon the daycount function of the _daycounter attribute.

        parameters
        ----------
        target_date : _RHDate
            the second date

        returns
        -------
        float
            the year fraction
        """

        return self._daycounter.daycount(self.spot_date, target_date)

    def bootstrap(self, instrument_list: List[FinancialInstrument]) -> None:
        """bootstrap the curve

        parameters
        ----------
        instrument_list : list of FinancialInstrument
            the instrument list to use for bootstrapping

        returns
        -------
        None

        examples
        --------
        >>> settings_ois = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR",
        ... )
        >>> curve_ois = IRCurve("ESTR", settings_ois)

        >>> from pyratehike import ListOfInstruments
        >>> from pathlib import Path
        >>> ibor_path = Path(__file__).parent / 'data/ibor.csv'
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings_ois, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)

        >>> settings_ibor = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR",
        ...     synthetic_instruments = "OIS",
        ... )
        >>> curve_ibor = IRCurve("EUR3M", settings_ibor)

        >>> curve_ibor.set_discount_curve(curve_ois)
        >>> list_ibor = ListOfInstruments(
        ...     settings_ibor, ibor_path, curve_ois
        ... )
        >>> curve_ibor.bootstrap(list_ibor.instruments)
        """

        times: List[float] = [
            self.daycount(inst.maturity_date) for inst in instrument_list
        ]
        self._interpolation_method.set_times(times)
        self._update_discount_factor(1, 0)
        iteration: int = 1
        prev_dfs: List[float] = [0 for _ in range(self.n_pillars)]
        discount_factor_convergence: float = 1
        function_evaluations: int = 0
        while (
            iteration <= self._interpolation_method.max_sweeps
            and discount_factor_convergence
            > rh_params.spline_df_convergence_tol
        ):
            for i, inst in enumerate(instrument_list):
                if inst.insttype == "synthetic":
                    self._update_discount_factor(inst.discount_factor, i + 1)
                else:
                    if iteration == 1:
                        guess = self.get_discount_factors(pillars=[i])[0]
                    else:
                        guess = self.get_discount_factors(pillars=[i + 1])[0]
                    _, root_res = brentq(
                        self._try_pillar,
                        guess * (1 - rh_params.root_find_interval_radius),
                        guess * (1 + rh_params.root_find_interval_radius),
                        args=(i + 1, inst),
                        xtol=rh_params.root_find_tol,
                        full_output=True,
                    )
                    self._update_discount_factor(root_res.root, i + 1)
                    function_evaluations += root_res.function_calls
            iteration += 1
            next_dfs = self.get_discount_factors()
            discount_factor_convergence = max(
                abs(p - n) for p, n in zip(prev_dfs, next_dfs)
            )
            prev_dfs = next_dfs
        self.bootstrap_info = _BootstrapInfo(
            discount_factor_convergence, function_evaluations, iteration - 1
        )

    def re_anchor(
        self, depo_spot_next: Optional[FinancialInstrument] = None
    ) -> None:
        """re-anchoring method.

        parameters
        ----------
        depo_spot_next : FinancialInstrument, optional
            the spot-next depo, only used in ReAnchorMethodONTN

        returns
        -------
        None

        examples
        --------
        >>> settings = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR",
        ...     re_anchoring = "ONTN",
        ... )
        >>> curve_ois = IRCurve("ESTR", settings)
        >>> from pyratehike import ListOfInstruments
        >>> from pathlib import Path
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)
        >>> curve_ois.re_anchor(list_ois.instruments[0])
        """

        self._anchoring.re_anchor(self, depo_spot_next)

    def _get_data(
        self,
        dates: Optional[List[_RHDate]] = None,
        times: Optional[List[float]] = None,
        pillars: Optional[List[int]] = None,
        derivative: bool = False,
    ) -> Tuple[List[float], List[float]]:
        """get the raw data.

        order of precedence: pillars, dates, times. If all are
        missing, the raw data for all pillars are returned.

        parameters
        ----------
        dates: list of _RHDate, optional
            the dates for which the raw data are required
        times: list of float, optional
            the times for which the raw data are required
        pillars: list of int, optional
            the pillars for which the raw data are required

        returns
        -------
        list of float
            the raw data
        list of float
            the times
        """

        if dates is not None:
            times = [self.daycount(datum) for datum in dates]
        data, times = self._interpolation_method.get_data(
            times=times, pillars=pillars, derivative=derivative
        )
        return data, times

    def get_dates(self, times: Optional[List[float]] = None) -> List[_RHDate]:
        """get the pillar dates for the curve.

        parameters
        ----------
        times: list of float or None
            request dates for specific year fractions; if None the
            pillar dates are returned

        returns
        -------
        list of _RHDate
        """

        if times is None:
            times = [self.get_time(k) for k in range(self.n_pillars)]
        return [
            self._daycounter.get_end_date(self.spot_date, t) for t in times
        ]

    def get_discount_curve(self) -> "IRCurve":
        """get the associated discount curve.

        parameters
        ----------
        (no paramters)

        returns
        -------
        IRCurve
            The discount curve associated to the object.
            If no discount curve is associated, this means endogenous
            discounting is used and self is returned.
        """

        try:
            return self._discount_curve
        except AttributeError:
            return self

    def get_discount_factors(
        self,
        dates: Optional[List[_RHDate]] = None,
        times: Optional[List[float]] = None,
        pillars: Optional[List[int]] = None,
    ) -> List[float]:
        """get the discount factors.

        order of precedence: pillars, dates, times. If all are
        missing, the discount factors for all pillars are returned.

        parameters
        ----------
        dates: list of _RHDate, optional
            the dates for which the discount factors are required
        times: list of float, optional
            the times for which the discount factors are required
        pillars: list of int, optional
            the pillars for which the discount factors are required

        returns
        -------
        list of float
            the discount factors.

        examples
        --------
        >>> settings = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR"
        ... )
        >>> curve_ois = IRCurve("ESTR", settings)
        >>> from pyratehike import ListOfInstruments
        >>> from pathlib import Path
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)

        >>> df_all = curve_ois.get_discount_factors()
        >>> df_123 = curve_ois.get_discount_factors(pillars=[1,2,3])
        """

        data, times = self._get_data(dates=dates, times=times, pillars=pillars)
        return self._interpolation_data_type.data_to_discount_factor(
            data, times
        )

    def get_insta_forwards(
        self,
        dates: Optional[List[_RHDate]] = None,
        times: Optional[List[float]] = None,
        pillars: Optional[List[int]] = None,
    ) -> List[float]:
        """get the instantaneous forward rates.

        order of precedence: pillars, dates, times. If all are
        missing, the instantaneous forward rates for all pillars are returned.

        parameters
        ----------
        dates: list of _RHDate, optional
            the dates for which the instantaneous forward rates are required
        times: list of float, optional
            the times for which the instantaneous forward rates are required
        pillars: list of int, optional
            the pillars for which the instantaneous forward rates are required

        returns
        -------
        list of float
            the instantaneous forward rates.

        examples
        --------
        >>> settings = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR"
        ... )
        >>> curve_ois = IRCurve("ESTR", settings)
        >>> from pyratehike import ListOfInstruments
        >>> from pathlib import Path
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)

        >>> if_all = curve_ois.get_insta_forwards()
        >>> if_123 = curve_ois.get_insta_forwards(pillars=[1,2,3])
        """

        derivative, _ = self._get_data(
            dates=dates, times=times, pillars=pillars, derivative=True
        )
        data, times = self._get_data(dates=dates, times=times, pillars=pillars)
        return self._interpolation_data_type.data_to_insta_forward(
            data, derivative, times
        )

    def get_time(self, pillar: int) -> float:
        """get the year fraction associated with a pillar.

        parameters
        ----------
        pillar : int
            the pillar for which the information is required

        returns
        -------
        float
            the year fraction required
        """

        return self._interpolation_method.get_time(pillar)

    def get_zero_rates(
        self,
        dates: Optional[List[_RHDate]] = None,
        times: Optional[List[float]] = None,
        pillars: Optional[List[int]] = None,
    ) -> List[float]:
        """get the zero rates.

        order of precedence: pillars, dates, times. If all are
        missing, the zero rates for all pillars are returned.

        parameters
        ----------
        dates: list of _RHDate, optional
            the dates for which the zero rates are required
        times: list of float, optional
            the times for which the zero rates are required
        pillars: list of int, optional
            the pillars for which the zero rates are required

        returns
        -------
        list of float
            the zero rates.

        examples
        --------
        >>> settings = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR"
        ... )
        >>> curve_ois = IRCurve("ESTR", settings)
        >>> from pyratehike import ListOfInstruments
        >>> from pathlib import Path
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)

        >>> zero_all = curve_ois.get_zero_rates()
        >>> zero_123 = curve_ois.get_zero_rates(pillars=[1,2,3])
        """

        data, times = self._get_data(dates=dates, times=times, pillars=pillars)
        return self._interpolation_data_type.data_to_zero_coupon_rate(
            data, times
        )

    def set_discount_curve(self, curve: "IRCurve") -> None:
        """set the associated discount curve.

        parameters
        ----------
        curve : IRCurve
            the associated discount curve

        returns
        -------
        None
        """

        self._discount_curve = curve

    def update_all_discount_factors(
        self, discount_factors: List[float]
    ) -> None:
        """update all discount factors.

        parameters
        ----------
        dfs : list of float
            the discount factors

        returns
        -------
        None
        """

        discount_factor_data = [
            self._interpolation_data_type.discount_factor_to_data(
                df, self.get_time(i)
            )
            for i, df in enumerate(discount_factors)
        ]
        self._interpolation_method.update_all_pillars(discount_factor_data)

    def _update_discount_factor(
        self, discount_factor: float, pillar: int
    ) -> None:
        """update a discount factor.

        parameters
        ----------
        discount_factor : float
            the discount factor
        pillar : int
            the pillar for which to update

        returns
        -------
        None
        """

        df_data = self._interpolation_data_type.discount_factor_to_data(
            discount_factor, self.get_time(pillar)
        )
        self._interpolation_method.update_pillar(df_data, pillar)

    def _try_pillar(
        self,
        discount_factor: float,
        pillar: int,
        instrument: FinancialInstrument,
    ) -> float:
        """try a pillar: update a discount factor and determine the
        fixing error for a FinancialInstrument.

        parameters
        ----------
        discount_factor : float
            the discount factor to try
        pillar : int
            the pillar for which to try
        instrument : FinancialInstrument
            the financial instrument for which the fixing should be
            matched

        returns
        -------
        float
            the difference between the fixing of the instrument using
            the updated curve, and the market quote
        """

        self._update_discount_factor(discount_factor, pillar)
        return instrument.quote - instrument.fixing(self)

    def set_times(self, times: List[float]) -> None:
        """method for setting the times of the curve.

        calls the set_times method of the _interpolation_method
        object. The interpolation coefficients are initialized at
        None.

        parameters
        ----------
        times : list of float
            the times

        returns
        -------
        None
        """

        self._interpolation_method.set_times(times)

    def plot(
        self,
        times: Optional[List[float]] = None,
        max_time: Optional[float] = None,
        n_points: Optional[int] = None,
        forward_period: _Period = _Period(6, "MO"),
    ) -> None:  # pragma: no cover
        """plot the curve

        parameters
        ----------
        times : list of float, optional
            a list of times used as x grid for the plot.
        max_time : float, optional
            the final time to plot. The default value is the end
            point of the curve.
        n_points : int, optional
            the number of points used in the plot. The default value
            is 500.
        forward_period : _Period, optional
            the period used to calculate the discrete forward rates.
            The default value is _Period(6, "MO").

        returns
        -------
        None

        examples
        --------
        >>> settings = RHSettings(
        ...     today_date = "2023-07-06",
        ...     interpolation_data_type = "logdf",
        ...     interpolation_method = "linear",
        ...     currency = "EUR",
        ...     re_anchoring = "ONTN",
        ... )
        >>> curve_ois = IRCurve("ESTR", settings)
        >>> from pyratehike import ListOfInstruments
        >>> from pathlib import Path
        >>> ois_path = Path(__file__).parent / 'data/ois.csv'
        >>> list_ois = ListOfInstruments(settings, ois_path)
        >>> curve_ois.bootstrap(list_ois.instruments)
        >>> curve_ois.re_anchor(list_ois.instruments[0])
        >>> curve_ois.plot(max_time = 10, forward_period = _Period(3, "MO"))  # doctest: +SKIP
        """

        # pylint: disable = too-many-locals, too-many-statements

        # input processing
        if times is None:
            if (
                max_time is None
                or max_time > self.get_time(self.n_pillars - 1) - 0.55
            ):
                max_time = self.get_time(self.n_pillars - 1) - 0.55
            if n_points is None:
                n_points = 500
            times = [max_time / (n_points - 1) * i for i in range(n_points)]
        elif times[-1] > self.get_time(self.n_pillars - 1) - 0.55:
            times = [
                t
                for t in times
                if t <= self.get_time(self.n_pillars - 1) - 0.55
            ]
        period_yearfraction: float = forward_period.number
        if forward_period.unit == "MO":
            period_yearfraction = period_yearfraction / 12
        forward_period_string = (
            f"{forward_period.number}{forward_period.unit[0]}"
        )

        # data
        zero_rates: list[float] = [
            100 * r for r in self.get_zero_rates(times=times)
        ]
        discount_factors: list[float] = self.get_discount_factors(times=times)
        insta_forwards: list[float] = [
            100 * r for r in self.get_insta_forwards(times=times)
        ]
        times_forward: list[float] = [t + period_yearfraction for t in times]
        discount_factors_forward: list[float] = self.get_discount_factors(
            times=times_forward
        )
        discrete_forwards = [
            100 * (d_s / d_f - 1) / period_yearfraction
            for d_s, d_f in zip(discount_factors, discount_factors_forward)
        ]

        # graphics parameters
        colors = ["brown", "chocolate", "darkgreen", "steelblue"]
        ltys = ["-", "--", "-.", ":"]

        # plots
        fig, ax1 = subplots()
        ax1.margins(x=0)
        line_zero = ax1.plot(
            times,
            zero_rates,
            color=colors[0],
            linestyle=ltys[0],
            label="zero rate",
        )
        line_disc_fwd = ax1.plot(
            times,
            discrete_forwards,
            color=colors[1],
            linestyle=ltys[1],
            label=f"{forward_period_string} forward",
        )
        line_insta_fwd = ax1.plot(
            times,
            insta_forwards,
            color=colors[2],
            linestyle=ltys[2],
            label="instantaneous forward",
        )
        ax2 = ax1.twinx()
        line_disc_factor = ax2.plot(
            times,
            discount_factors,
            color=colors[3],
            linestyle=ltys[3],
            label="discount factor",
        )

        # axes, labels
        lines = line_zero + line_disc_fwd + line_insta_fwd + line_disc_factor
        labels = [l.get_label() for l in lines]
        ax1.set_xlabel("time (years)")
        ax1.set_ylabel("interest rate (%)")
        ax2.set_ylabel("discount factor")
        ax1.legend(lines, labels, fontsize=6)
        ax2.yaxis.label.set_color(colors[3])
        ax2.spines["right"].set_edgecolor(colors[3])
        ax2.tick_params(axis="y", colors=colors[3])

        # title
        try:
            spot_date_orig = str(self.spot_date_orig)
        except AttributeError:
            spot_date_orig = str(self.spot_date)
        title2a: str = f"reference date: {str(self.today_date)}"
        title2b: str = f"spot date: {spot_date_orig}"
        title2c: str = f"re-anchoring: {self._settings.re_anchoring}"
        title2: str = f"{title2a}, {title2b}, {title2c}"
        title3a: str = f"interpolation: {self._settings.interpolation_method}"
        title3b: str = f"{self._settings.interpolation_data_type}"
        title3: str = f"{title3a} on {title3b}"
        title4a: str = f"spline correction: {self._settings.spline_correction}"
        title4b: str = "synthetic instruments"
        title4c: str = f"{self._settings.synthetic_instruments}"
        title4: str = f"{title4a}, {title4b}: {title4c}"
        plot_title: str = f"{title2}\n{title3}\n{title4}"
        fig.suptitle(self._name, fontsize=16)
        title(plot_title, fontsize=10)

        # show
        fig.tight_layout()
        show()
