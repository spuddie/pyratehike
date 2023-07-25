from math import log
from pathlib import Path

import pytest

from pyratehike.curve import IRCurve
from pyratehike.list_of_instruments import (
    ListOfInstruments,
    _dp_add_synthetics,
)
from pyratehike.parameters_settings import RHSettings

data_path = Path(__file__).parent.parent / "pyratehike/data"
ibor_path = data_path / "ibor.csv"
ois_path = data_path / "ois.csv"


class TestAddSynthetics:
    settings = RHSettings(
        today_date="2023-07-06",
        currency="EUR",
        interpolation_data_type="zero",
        interpolation_method="linear",
    )
    list_ibor = ListOfInstruments(settings, ibor_path)
    curve_ois = IRCurve("ESTR", settings)
    curve_ibor = IRCurve("EUR6M", settings)
    curve_ibor.bootstrap(list_ibor.instruments)
    z1 = curve_ibor.get_zero_rates(pillars=[1])[0]
    t1 = curve_ibor.get_time(1)
    curve_ois._interpolation_method._times = [
        0,
        t1 / 4,
        2 * t1 / 4,
        3 * t1 / 4,
        t1,
    ]
    curve_ois._interpolation_method._coefficients = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    curve_ois._interpolation_method.n_pillars_set = 5

    def test_add_synthetics_no(self):
        as_no = _dp_add_synthetics.dispatch("no")
        snt_no = as_no.calc_synthetics(
            self.list_ibor.instruments, self.settings, None
        )
        assert snt_no == []

    def test_add_synthetics_ois(self):
        as_ois = _dp_add_synthetics.dispatch("OIS")
        snt_ois = as_ois.calc_synthetics(
            self.list_ibor.instruments, self.settings, self.curve_ois
        )
        for i, snt in enumerate(snt_ois):
            act = -log(snt.discount_factor) / (i + 1) ** 2 / self.t1 * 4**2
            assert act == pytest.approx(self.z1)

    def test_add_synthetics_ois_error(self):
        as_ois = _dp_add_synthetics.dispatch("OIS")
        with pytest.raises(
            ValueError, match="_AddSyntheticsOIS: discount curve is not set."
        ):
            snt_ois = as_ois.calc_synthetics(
                self.list_ibor.instruments, self.settings, None
            )
