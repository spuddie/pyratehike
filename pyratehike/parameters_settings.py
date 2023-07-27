"""parameters & settings for the package

This module defines a class for the package parameters and creates an
instance of this class. Also a class for the settings is created.
"""

from typing import List, Optional

from pyratehike._date_arithmetic import _RHDate
from pyratehike._general import _check_inputs

__all__: List[str] = ["rh_params", "RHSettings"]


class _RHParameters:
    """class for package paramterers

    Attributes
    ----------
    root_find_tol: float
        tolerance for root finding (default: 1e-12)
    root_find_interval_radius: float
        interval radius for root finding (default: 0.1)
    spline_df_convergence_tol: float
        tolerance for the discount factor convergence in the outer loop of
        bootstrapping with spline interpolation (default: 1e-12)
    spline_max_sweeps: int
        maximum number of outer loop interations when bootstrapping
        with spline interpolation (default: 10)
    """

    # pylint: disable=too-few-public-methods

    __slots__ = (
        "root_find_tol",
        "root_find_interval_radius",
        "spline_df_convergence_tol",
        "spline_max_sweeps",
    )
    root_find_tol: float
    root_find_interval_radius: float
    spline_df_convergence_tol: float
    spline_max_sweeps: int

    def __init__(self) -> None:
        """constructor for the _RHParameters class."""
        self.root_find_tol = 1e-12
        self.root_find_interval_radius = 1e-1
        self.spline_df_convergence_tol = 1e-12
        self.spline_max_sweeps = 10


class RHSettings:
    """class for settings

    Attributes
    ----------
    currency : str
        EUR and GBP are currently supported
    interpolation_method : str, optional
        interpolation method (linear or bessel)
    interpolation_data_type : str, optional
        interpolation data type (zero, df, logdf)
    re_anchoring: str, optional
        re-anchoring method to apply (no [default], date, 11, ONTN)
    spline_correction : str, optional
        spline correction (no [default], linear, natural)
    spot_date : _RHDate, optional
        spot date for a curve
    synthetic_instruments : str, optional
        which synthetic instruments to add (no [default], OIS)
    today_date : _RHDate
        today's date
    """

    # pylint: disable=too-few-public-methods, too-many-instance-attributes

    __slots__ = (
        "currency",
        "interpolation_method",
        "interpolation_data_type",
        "re_anchoring",
        "spline_correction",
        "spot_date",
        "synthetic_instruments",
        "today_date",
    )
    currency: str
    interpolation_data_type: str
    interpolation_method: str
    re_anchoring: str
    spline_correction: str
    spot_date: _RHDate
    synthetic_instruments: str
    today_date: _RHDate

    def __init__(
        self,
        currency: str,
        today_date: str,
        interpolation_method: Optional[str] = None,
        interpolation_data_type: Optional[str] = None,
        spot_date: Optional[str] = None,
        re_anchoring: str = "no",
        spline_correction: str = "no",
        synthetic_instruments: str = "no",
    ) -> None:
        """constructor for the _RHSettings class.

        parameters
        ----------
        currency : str
            the currency (currently only EUR and GBP are supported)
        today_date : str
            today's date yyyy-mm-dd
        interpolation_method : str, optional
            the interpolation method (linear, bessel)
        interpolation_data_type: str, optional
            the interpolation data type (zero, df, logdf)
        re_anchoring: str, optional
            re-anchoring method to apply (no [default], date, 11, ONTN)
        spot_date: str, optional
            the spot date yyyy-mm-dd
        spline_correction: str, optional
            the spline correction to apply (no [default], linear, natural)
        synthetic_instruments: str, optional
            the synthetic instruments to add (no [default], OIS)

        returns
        -------
        None

        examples
        --------
        >>> settings = RHSettings(
        ...     currency = "EUR",
        ...     today_date = "2022-02-22",
        ...     interpolation_data_type = "zero",
        ...     interpolation_method = "linear",
        ...     re_anchoring = "ONTN",
        ...     spline_correction = "linear",
        ...     synthetic_instruments = "OIS",
        ...     spot_date = "2022-02-22",
        ... )
        """

        # pylint: disable=too-many-arguments

        _check_inputs("currency", ["EUR", "GBP"], currency)
        self.currency = currency
        if interpolation_method is not None:
            _check_inputs(
                "interpolation_method",
                ["linear", "bessel"],
                interpolation_method,
            )
            self.interpolation_method = interpolation_method
        if interpolation_data_type is not None:
            _check_inputs(
                "interpolation_data_type",
                ["zero", "df", "logdf"],
                interpolation_data_type,
            )
            self.interpolation_data_type = interpolation_data_type
        _check_inputs(
            "re_anchoring", ["no", "date", "11", "ONTN"], re_anchoring
        )
        self.re_anchoring = re_anchoring
        _check_inputs(
            "spline_correction", ["no", "linear", "natural"], spline_correction
        )
        self.spline_correction = spline_correction
        if spot_date is not None:
            self.spot_date = _RHDate(spot_date)
        _check_inputs(
            "synthetic_instruments", ["no", "OIS"], synthetic_instruments
        )
        self.synthetic_instruments = synthetic_instruments
        self.today_date = _RHDate(today_date)


rh_params = _RHParameters()
"""instance of _RHParameters

global variable to be used throughout.
"""
