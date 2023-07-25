from pathlib import Path

import pytest

from pyratehike.curve import IRCurve
from pyratehike.list_of_instruments import ListOfInstruments
from pyratehike.metrics import roundtrip
from pyratehike.parameters_settings import RHSettings

data_path = Path(__file__).parent.parent / "pyratehike/data"
ibor_path = data_path / "ibor.csv"
ois_path = data_path / "ois.csv"


class TestRoundtrip:
    def helper_roundtrip(self, settings_ois, settings_ibor):
        list_ois = ListOfInstruments(settings_ois, ois_path)
        curve_ois = IRCurve("OIS", settings_ois)
        curve_ois.bootstrap(list_ois.instruments)
        actual_ois = roundtrip(curve_ois, list_ois.market_instruments)
        expected_ois = [0 for _ in actual_ois]
        assert expected_ois == pytest.approx(actual_ois, abs=1e-10)

        list_ibor = ListOfInstruments(settings_ibor, ibor_path, curve_ois)

        curve_ibor_endo = IRCurve("IBOR", settings_ibor)
        curve_ibor_endo.bootstrap(list_ibor.instruments)
        actual_ibor_endo = roundtrip(
            curve_ibor_endo, list_ibor.market_instruments
        )
        expected_ibor = [0 for _ in actual_ibor_endo]
        assert expected_ibor == pytest.approx(actual_ibor_endo)

        curve_ibor_exo = IRCurve("IBOR", settings_ibor)
        curve_ibor_exo.set_discount_curve(curve_ois)
        curve_ibor_exo.bootstrap(list_ibor.instruments)
        actual_ibor_exo = roundtrip(
            curve_ibor_exo, list_ibor.market_instruments
        )
        assert expected_ibor == pytest.approx(actual_ibor_exo)

    def helper_ccy(self, currency):
        settings = RHSettings(
            today_date="2023-07-06",
            interpolation_data_type="logdf",
            interpolation_method="linear",
            currency=currency,
        )

        self.helper_roundtrip(settings, settings)

        settings = RHSettings(
            today_date="2023-07-06",
            interpolation_data_type="df",
            interpolation_method="bessel",
            currency=currency,
        )
        self.helper_roundtrip(settings, settings)

        settings_ois = RHSettings(
            today_date="2023-07-06",
            interpolation_data_type="zero",
            interpolation_method="bessel",
            currency=currency,
        )
        settings_ibor = RHSettings(
            today_date="2023-07-06",
            interpolation_data_type="zero",
            interpolation_method="bessel",
            currency=currency,
            synthetic_instruments="OIS",
        )
        self.helper_roundtrip(settings_ois, settings_ibor)

    def test_all(self):
        self.helper_ccy("EUR")
        self.helper_ccy("GBP")
