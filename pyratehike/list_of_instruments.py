"""This module defines a class for a list of instruments, together
with some helper classes to add synthetics.
"""

from csv import DictReader
from math import exp
from typing import List, Optional

from pyratehike._date_arithmetic import _RHDate
from pyratehike._general import _Dispatcher
from pyratehike.curve import IRCurve
from pyratehike.instrument import FinancialInstrument, SyntheticInstrument
from pyratehike.parameters_settings import RHSettings

__all__: List[str] = ["ListOfInstruments"]


class _AddSynthetics:  # pragma: no cover
    """A class for adding synthetics to a ListOfInstruments.

    Abstract Base Class
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def calc_synthetics(
        instruments: List[FinancialInstrument],
        settings: RHSettings,
        discount_curve: Optional[IRCurve],
    ) -> List[SyntheticInstrument]:
        """Static method for determining the list of synthetic instruments.

        Parameters
        ----------
        instruments : list of FinancialInstrument
            the list of instruments to which you want to add synthetics
        settings : RHSettings
            the settings to be used
        discount_curve : IRCurve, optional
            the discount curve to use in the process, not necessary
            for "no" synthetics

        Returns
        -------
        list of SyntheticInstrument
            the list of synthetics to be passed to
            ListOfInstrument.add_synthetics. The base
            class returns an empty list.

        """

        raise NotImplementedError


class _AddSyntheticsNo(_AddSynthetics):
    """A class for adding "no" synthetics to a ListOfInstruments."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def calc_synthetics(
        instruments: List[FinancialInstrument],
        settings: RHSettings,
        discount_curve: Optional[IRCurve],
    ) -> List[SyntheticInstrument]:
        # pylint: disable=unused-argument

        return []


class _AddSyntheticsOIS(_AddSynthetics):
    """A class for adding synthetics to a list of instruments.

    This class adds synthetics to an IBOR curve using an OIS curve.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def calc_synthetics(
        instruments: List[FinancialInstrument],
        settings: RHSettings,
        discount_curve: Optional[IRCurve],
    ) -> List[SyntheticInstrument]:
        if discount_curve is None:
            raise ValueError("_AddSyntheticsOIS: discount curve is not set.")
        curve_aux: IRCurve = IRCurve("AUX", settings)
        curve_aux.bootstrap([instruments[0]])
        zero_rate: float = curve_aux.get_zero_rates(pillars=[1])[0]
        yearfraction = curve_aux.get_time(1)
        times_discount_curve: List[float] = [
            discount_curve.get_time(k)
            for k in range(1, discount_curve.n_pillars)
        ]
        stub_times_discount: List[float] = [
            t for t in times_discount_curve if t < yearfraction
        ]
        discount_rates: List[float] = discount_curve.get_zero_rates(
            times=stub_times_discount
        )
        discount_rate_0: float = discount_curve.get_zero_rates(
            times=[yearfraction]
        )[0]
        stub_rates: List[float] = [
            d + (zero_rate - discount_rate_0) / yearfraction * t
            for d, t in zip(discount_rates, stub_times_discount)
        ]
        stub_dates: List[_RHDate] = discount_curve.get_dates(
            stub_times_discount
        )
        stub_times_forecast: List[float] = [
            curve_aux.daycount(d) for d in stub_dates
        ]
        return [
            SyntheticInstrument(exp(-r * t), m)
            for r, t, m in zip(stub_rates, stub_times_forecast, stub_dates)
            if t is not None
        ]


_dp_add_synthetics: _Dispatcher[_AddSynthetics] = _Dispatcher(_AddSynthetics())
"""dispatcher to choose the method for adding synthetics.

_dp_add_synthetics.dispatch() and _dp_add_synthetics.dispatch("no") return the default
class _AddSynthetics; _dp_add_synthetics.dispatch("ois") returns the class
_AddSyntheticsOIS.
"""
_dp_add_synthetics.set_method("no", _AddSyntheticsNo())
_dp_add_synthetics.set_method("OIS", _AddSyntheticsOIS())


class ListOfInstruments:
    """a list of instruments used as input to the bootstrapping algorithm.

    A CSV file is read for a list of instruments.
    The _AddSynthetics class is used to create the list of
    synthetic instruments.

    examples
    --------
    >>> settings_ois = RHSettings(
    ...     today_date = "2023-07-06",
    ...     interpolation_data_type = "logdf",
    ...     interpolation_method = "linear",
    ...     currency = "EUR",
    ... )
    >>> from pathlib import Path
    >>> ois_path = Path(__file__).parent / 'data/ois.csv'
    >>> list_ois = ListOfInstruments(settings_ois, ois_path)

    >>> curve_ois = IRCurve("ESTR", settings_ois)
    >>> curve_ois.bootstrap(list_ois.instruments)
    >>> settings_ibor = RHSettings(
    ...     today_date = "2023-07-06",
    ...     interpolation_data_type = "logdf",
    ...     interpolation_method = "linear",
    ...     currency = "EUR",
    ...     synthetic_instruments = "OIS",
    ... )
    >>> ibor_path = Path(__file__).parent / 'data/ibor.csv'
    >>> list_ibor = ListOfInstruments(
    ...     settings_ibor, ibor_path, curve_ois
    ... )
    """

    # pylint: disable=too-few-public-methods

    __slots__ = (
        "_add_synthetics",
        "market_instruments",
        "_synthetic_instruments",
    )
    _add_synthetics: _AddSynthetics
    market_instruments: List[FinancialInstrument]
    _synthetic_instruments: List[SyntheticInstrument]

    def __init__(
        self,
        settings: RHSettings,
        csv_path: str,
        discount_curve: Optional[IRCurve] = None,
    ) -> None:
        """constructor for ListOfFiles.

        creates a ListOfFiles object using a csv input. The input
        should have the structure as documented in the constructor
        of FinancialInstrument.

        If required by the settings, and if a discount is provided,
        synthetic instruments will be added.

        parameters
        ----------
        settings : RHSettings
            the settings to be used when constructing the instruments
        csv_path : str, optional
            the path to the csv input file
        discount_curve : IRCurve, optional
            an interest rate curve, can be used to calculate the
            synthetic instruments

        returns
        -------
        None
        """

        self._add_synthetics = _dp_add_synthetics.dispatch(
            settings.synthetic_instruments
        )
        with open(csv_path, encoding="utf-8") as csv_file:
            instrument_reader = DictReader(csv_file)
            self.market_instruments = [
                FinancialInstrument(inst, settings)
                for inst in instrument_reader
            ]
        self._synthetic_instruments = self._add_synthetics.calc_synthetics(
            self.market_instruments, settings, discount_curve
        )

    @property
    def instruments(self) -> List[FinancialInstrument]:
        """the instruments contained in the object.

        parameters
        ----------
        (no parameters)

        returns
        -------
        list of FinancialInstrument
            the synthetic and market instruments contained in the
            object
        """

        return self._synthetic_instruments + self.market_instruments
