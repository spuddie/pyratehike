"""module definining the metrics benchmark and roundtrip."""


from typing import List, Optional

from pyratehike.curve import IRCurve
from pyratehike.instrument import FinancialInstrument


def benchmark(
    curve: IRCurve,
    benchmark_zeros: Optional[List[Optional[float]]] = None,
    benchmark_discount_factors: Optional[List[Optional[float]]] = None,
    pillars: Optional[List[int]] = None,
) -> List[Optional[float]]:
    """the benchmark test for a bootstrapped curve

    parameters
    ----------
    curve : IRCurve
        the bootstrapped curve
    benchmark_zeros : list of float, optional
        a list with zero rates to compare to the curve
    benchmark_discount_factors : list of float, optional
        a list with discount factors to compare to the curve
    pillars : list of int, optional
        a list with pillars for which benchmark values are provided

    returns
    -------
    list of float
        the difference between the benchmark zero rates or the
        benchmark discount factors to the values as returned by the
        bootstrapped curve

    examples
    --------
    >>> from pathlib import Path
    >>> from pyratehike import ListOfInstruments, RHSettings
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
    >>> bm_ois = benchmark(curve_ois, benchmark_zeros=[0, 0, 0], pillars=[2, 5, 8])
    """

    if pillars is None:
        pillars = list(range(1, curve.n_pillars))
    if benchmark_zeros is not None:
        zeros: List[float] = curve.get_zero_rates(pillars=pillars)
        diff: List[Optional[float]] = [
            b - z if b is not None else None
            for b, z in zip(benchmark_zeros, zeros)
        ]
    elif benchmark_discount_factors is not None:
        discount_factors: List[float] = curve.get_discount_factors(
            pillars=pillars
        )
        diff = [
            b - z if b is not None else None
            for b, z in zip(benchmark_discount_factors, discount_factors)
        ]
    return diff


def roundtrip(
    curve: IRCurve, instruments: List[FinancialInstrument]
) -> List[float]:
    """the roundtrip test for bootstrapping

    Compare the fixings of an instrument list to the quotes.
    When used on the instrument list that was used to bootstrap
    the curve, this is called the round-trip test.

    parameters
    ----------
    curve : IRCurve
        the bootstrapped curve
    instruments : list of FinancialInstrument
        the list of instruments used for bootstrapping

    returns
    -------
    list of float
        a list with the roundtrip test error for each market
        instrument in the list of instrument

    examples
    --------
    >>> from pathlib import Path
    >>> from pyratehike import ListOfInstruments, RHSettings
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
    >>> rt_ois = roundtrip(curve_ois, list_ois.market_instruments)
    """

    return [inst.fixing(curve) - inst.quote for inst in instruments]
