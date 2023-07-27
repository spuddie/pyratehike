# pyratehike <img src="doc/logo-pyratehike.png" align="right" height="200" />
## Ramp up the quality of your interest rate curves

<!-- badges: start -->
[![check-code](https://github.com/spuddie/pyratehike/actions/workflows/check-code.yaml/badge.svg)](https://github.com/spuddie/pyratehike/actions/workflows/check-code.yaml)
[![unit-tests](https://github.com/spuddie/pyratehike/actions/workflows/unit-tests.yaml/badge.svg)](https://github.com/spuddie/pyratehike/actions/workflows/unit-tests.yaml)
<!-- badges: end -->

pyratehike is a package develop to bootstrap zero coupon curves, in
particular IBOR curves and OIS curves. It was created as part of a
master's thesis project, check out the 
[vignette](MastersThesis.md)
for more details. This
thesis contains all the details on the implementation. The package is
also reasonably documented.

## R vs python
An R implementation also exists, more info on the creation history
and the difference can be found in 
[R-vs-python.md](R-vs-python.md).

## Installation
To install the package use the command `pip install
git+https://github.com/spuddie/pyratehike`.

## Example session
```python
from pyratehike import IRCurve, ListOfInstruments, RHSettings, roundtrip

settings_ois = RHSettings(
    today_date = "2023-07-06",
    interpolation_data_type = "logdf",
    interpolation_method = "linear",
    currency = "EUR",
)
list_ois = ListOfInstruments(settings_ois, "data/ois.csv")
curve_ois = IRCurve("ESTR", settings_ois)
curve_ois.bootstrap(list_ois.instruments)

settings_ibor = RHSettings(
    today_date = "2023-07-06",
    interpolation_data_type = "logdf",
    interpolation_method = "linear",
    currency = "EUR",
    synthetic_instruments = "OIS",
    re_anchoring = "ONTN",
)
curve_ibor = IRCurve("EUR3M", settings_ibor)
curve_ibor.set_discount_curve(curve_ois)
list_ibor = ListOfInstruments(
    settings_ibor, 'data/ibor.csv', curve_ois
)
curve_ibor.bootstrap(list_ibor.instruments)
curve_ibor.re_anchor(list_ois.instruments[0])

roundtrip(curve_ibor, list_ibor.market_instruments)
```
[-4.85722573273506e-17, -1.5959455978986625e-16, 3.400058012914542e-16, 7.73686670285656e-16, 1.5959455978986625e-16, -7.28583859910259e-17, -2.949029909160572e-16, 1.700029006457271e-16, 1.0755285551056204e-16, 3.469446951953614e-17, 2.498001805406602e-16, -8.673617379884035e-16, 2.5326962749261384e-16, 0.0, -1.5612511283791264e-16, 0.0, -3.469446951953614e-18, -6.938893903907228e-18, 4.163336342344337e-17, 3.122502256758253e-17, 2.42861286636753e-17, 0.0, 6.938893903907228e-18, -4.753142324176451e-16, 1.0408340855860843e-17, -1.9532986339498848e-15, -1.2614909117303341e-14, -6.938893903907228e-18, -1.3877787807814457e-17]
```python
curve_ibor.plot()
```
![example plot curve ibor](doc/example-curve-ibor.png)
