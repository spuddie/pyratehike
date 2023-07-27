"""pyRateHike: Ramp Up the Quality of Your Interest Rate Curves.

pyratehike is a package designed to bootstrap interest rate
curves in a multi-curve framework, in
particular IBOR curves and OIS curves. It was created as part of a
master's thesis project, check out the vignette for more details. This
thesis contains all the details on the implementation.

the best start is to check the documentation for IRCurve (in
particular the IRCurve.bootstrap method), FinancialInstrument or 
ListOfInstruments.

The package comes with two example data files: data/ois.csv
representing inputs the ESTR OIS curve and data/ibor.csv representing
inputs for the EURIBOR 3 months curve.

examples
--------
>>> from pyratehike import IRCurve, ListOfInstruments, RHSettings, roundtrip
>>> from pathlib import Path
>>> ibor_path = Path(__file__).parent / 'data/ibor.csv'
>>> ois_path = Path(__file__).parent / 'data/ois.csv'

>>> settings_ois = RHSettings(
...     today_date = "2023-07-06",
...     interpolation_data_type = "logdf",
...     interpolation_method = "linear",
...     currency = "EUR",
... )
>>> list_ois = ListOfInstruments(settings_ois, ois_path)
>>> curve_ois = IRCurve("ESTR", settings_ois)
>>> curve_ois.bootstrap(list_ois.instruments)

>>> settings_ibor = RHSettings(
...     today_date = "2023-07-06",
...     interpolation_data_type = "logdf",
...     interpolation_method = "linear",
...     currency = "EUR",
...     synthetic_instruments = "OIS",
...     re_anchoring = "ONTN",
... )
>>> curve_ibor = IRCurve("EUR3M", settings_ibor)
>>> curve_ibor.set_discount_curve(curve_ois)
>>> list_ibor = ListOfInstruments(
...     settings_ibor, ibor_path, curve_ois
... )
>>> curve_ibor.bootstrap(list_ibor.instruments)
>>> curve_ibor.re_anchor(list_ois.instruments[0])
>>> rt = roundtrip(curve_ibor, list_ibor.market_instruments)
>>> curve_ibor.plot()  # doctest: +SKIP
"""

from typing import List

__all__: List[str] = [
    "benchmark",
    "FinancialInstrument",
    "IRCurve",
    "ListOfInstruments",
    "rh_params",
    "RHSettings",
    "roundtrip",
    "SyntheticInstrument",
]

from pyratehike.curve import IRCurve
from pyratehike.instrument import FinancialInstrument, SyntheticInstrument
from pyratehike.list_of_instruments import ListOfInstruments
from pyratehike.metrics import benchmark, roundtrip
from pyratehike.parameters_settings import RHSettings, rh_params
