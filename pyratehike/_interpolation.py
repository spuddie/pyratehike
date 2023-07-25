"""definitions of interpolation functionality.

Class _InterpolationDataType (and subclasses) provide transformation
methods to transform raw data to discount factors and zero rates, and
back. Class _InterpolationMethod calculates interpolation coefficients and
applies the interpolation for the raw data. This latter class uses the
helper classes _SplineCorrection (and subclasses) to apply the required
correction to spline interpolations and
_InterpolationCoefficients (and subclasses) to actually calculate the 
required interpolation coefficients.
"""

# pylint: disable=too-many-lines

from math import exp, log
from typing import List, Optional, Tuple

from pyratehike._general import _Dispatcher
from pyratehike.parameters_settings import rh_params


class _InterpolationDataType:  # pragma: no cover
    """helper class to transform curve data (zero rates, discount
    factors, instantaneous forward rates) to raw data and back.

    Abstract Base Class.
    """

    @staticmethod
    def data_to_discount_factor(
        data: List[float], times: List[float]
    ) -> List[float]:
        """convert data to discount factors.

        parameters
        ----------
        data : list of float
            raw data
        times : list of float
            the times for which the data is defined

        returns
        -------
        list of float
            the discount factors
        """

        raise NotImplementedError

    @staticmethod
    def data_to_insta_forward(
        data: List[float], derivative: List[float], times: List[float]
    ) -> List[float]:
        """convert data to instantaneous forward rates.

        parameters
        ----------
        data : list of float
            raw data
        times : list of float
            the times for which the data is defined

        returns
        -------
        list of float
            the instantaneous forward rates
        """

        raise NotImplementedError

    @staticmethod
    def data_to_zero_coupon_rate(
        data: List[float], times: List[float]
    ) -> List[float]:
        """convert data to zero rates.

        parameters
        ----------
        data : list of float
            raw data
        times : list of float
            the times for which the data is defined

        returns
        -------
        list of float
            the zero rates
        """

        raise NotImplementedError

    @staticmethod
    def discount_factor_to_data(discount_factor: float, time: float) -> float:
        """convert a discount factor to raw data.

        parameters
        ----------
        discount_factor : float
            discount factor
        times : float
            the time for which the discount factor is defined

        returns
        -------
        float
            the raw data
        """

        raise NotImplementedError


class _InterpolationDataTypeZero(_InterpolationDataType):
    """helper class to transform curve data (zero rates, discount
    factors, instantaneous forward rates) to raw data and back when
    the raw data are the zero rates.
    """

    @staticmethod
    def data_to_discount_factor(
        data: List[float], times: List[float]
    ) -> List[float]:
        return [exp(-d * t) for d, t in zip(data, times)]

    @staticmethod
    def data_to_insta_forward(
        data: List[float], derivative: List[float], times: List[float]
    ) -> List[float]:
        return [d + t * dd for d, t, dd in zip(data, times, derivative)]

    @staticmethod
    def data_to_zero_coupon_rate(
        data: List[float], times: List[float]
    ) -> List[float]:
        return data

    @staticmethod
    def discount_factor_to_data(discount_factor: float, time: float) -> float:
        if time == 0:
            return 0
        return -log(discount_factor) / time


class _InterpolationDataTypeDf(_InterpolationDataType):
    """helper class to transform curve data (zero rates, discount
    factors, instantaneous forward rates) to raw data and back when
    the raw data are the discount factors.
    """

    @staticmethod
    def data_to_discount_factor(
        data: List[float], times: List[float]
    ) -> List[float]:
        return data

    @staticmethod
    def data_to_insta_forward(
        data: List[float], derivative: List[float], times: List[float]
    ) -> List[float]:
        return [-dd / d for d, dd in zip(data, derivative)]

    @staticmethod
    def data_to_zero_coupon_rate(
        data: List[float], times: List[float]
    ) -> List[float]:
        return [-log(d) / t if t != 0 else 0 for d, t in zip(data, times)]

    @staticmethod
    def discount_factor_to_data(discount_factor: float, time: float) -> float:
        return discount_factor


class _InterpolationDataTypeLogdf(_InterpolationDataType):
    """helper class to transform curve data (zero rates, discount
    factors, instantaneous forward rates) to raw data and back when
    the raw data are the logarithm of the discount factors.
    """

    @staticmethod
    def data_to_discount_factor(
        data: List[float], times: List[float]
    ) -> List[float]:
        return [exp(d) for d in data]

    @staticmethod
    def data_to_insta_forward(
        data: List[float], derivative: List[float], times: List[float]
    ) -> List[float]:
        return [-dd for dd in derivative]

    @staticmethod
    def data_to_zero_coupon_rate(
        data: List[float], times: List[float]
    ) -> List[float]:
        return [-d / t if t != 0 else 0 for d, t in zip(data, times)]

    @staticmethod
    def discount_factor_to_data(discount_factor: float, time: float) -> float:
        return log(discount_factor)


_dp_interpolation_data_type: _Dispatcher[_InterpolationDataType] = _Dispatcher(
    _InterpolationDataType()
)
"""dispatcher to choose the raw data type.

_dp_interpolation_data_type.dispatch("df") returns the class for the
discount factors; _dp_interpolation_data_type.dispatch("logdf") returns 
the class for the logarithm of the discount factors; 
_dp_interpolation_data_type.dispatch("zero") returns the class for the
zero rates. 
"""
_dp_interpolation_data_type.set_method("df", _InterpolationDataTypeDf())
_dp_interpolation_data_type.set_method("logdf", _InterpolationDataTypeLogdf())
_dp_interpolation_data_type.set_method("zero", _InterpolationDataTypeZero())


class _SplineCorrection:  # pragma: no cover
    """helper class for spline corrections.

    Abstract Base Class.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def apply_spline_correction(
        interpolation_method: "_InterpolationMethod",
    ) -> None:
        """apply the spline correction.

        parameters
        ----------
        interpolation_method : _InterpolationMethod
            the object on which to apply the correction

        returns
        -------
        None
        """

        raise NotImplementedError


class _SplineCorrectionNo(_SplineCorrection):
    """helper class for spline corrections.

    Dummy implementation for "no" corrections.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def apply_spline_correction(
        interpolation_method: "_InterpolationMethod",
    ) -> None:
        pass


class _SplineCorrectionLinear(_SplineCorrection):
    """helper class for spline corrections.

    Implementation for "linear" corrections.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def apply_spline_correction(
        interpolation_method: "_InterpolationMethod",
    ) -> None:
        _InterpolationCoefficientsLinear.calc_coefficient(
            interpolation_method,
            updated_pillar=interpolation_method.n_pillars_set - 1,
        )
        interpolation_method.set_coefficient(
            0, 1, interpolation_method.n_pillars_set - 1
        )
        interpolation_method.set_coefficient(
            0, 2, interpolation_method.n_pillars_set - 2
        )
        interpolation_method.set_coefficient(
            0, 3, interpolation_method.n_pillars_set - 2
        )


class _SplineCorrectionNatural(_SplineCorrection):
    """helper class for spline corrections.

    Implementation for "natural" corrections.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def apply_spline_correction(
        interpolation_method: "_InterpolationMethod",
    ) -> None:
        end_pillar: int = interpolation_method.n_pillars_set - 1
        delta_x: float = interpolation_method.get_time(
            end_pillar
        ) - interpolation_method.get_time(end_pillar - 1)
        delta_y: float = interpolation_method.get_coefficient(
            0, end_pillar
        ) - interpolation_method.get_coefficient(0, end_pillar - 1)
        coeff_b: float = interpolation_method.get_coefficient(
            1, end_pillar - 1
        )
        interpolation_method.set_coefficient(
            0, 1, interpolation_method.n_pillars_set - 1
        )
        interpolation_method.set_coefficient(
            (-2 * coeff_b * delta_x + 3 * delta_y) / delta_x**2,
            2,
            interpolation_method.n_pillars_set - 2,
        )
        interpolation_method.set_coefficient(
            (coeff_b * delta_x - 2 * delta_y) / delta_x**3,
            3,
            interpolation_method.n_pillars_set - 2,
        )


_dp_spline_correction: _Dispatcher[_SplineCorrection] = _Dispatcher(
    _SplineCorrection()
)
"""dispatcher to choose the spline correction.

_dp_spline_correction.dispatch("no") returns the class for "no"
corrections; _dp_spline_correction.dispatch("linear") returns 
the class for the linear correction; _dp_spline_correction.dispatch("natural") 
returns the class for the natural correction. 
"""
_dp_spline_correction.set_method("no", _SplineCorrectionNo())
_dp_spline_correction.set_method("linear", _SplineCorrectionLinear())
_dp_spline_correction.set_method("natural", _SplineCorrectionNatural())


class _InterpolationCoefficients:  # pragma: no cover
    """helper class to calculate interpolation coefficients.

    Abstract Base Class.
    """

    @classmethod
    def calc_coefficient(
        cls,
        interpolation_method: "_InterpolationMethod",
        updated_pillar: Optional[int] = None,
    ) -> None:
        """calculate the interpolation coefficients.

        parameters
        ----------
        interpolation_method : _InterpolationMethod
            the _InterpolationMethod object
        updated_pillar : int, optional
            the pillar that was updated. If missing all interpolation
            coefficients are calculated.

        returns
        -------
        None
        """

        raise NotImplementedError

    @staticmethod
    def n_coefficients() -> int:
        """the number of interpolation coeffcients per pillar.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the requested dimension
        """

        raise NotImplementedError

    @classmethod
    def bootstrap_max_sweeps(cls) -> int:
        """the maximum number of outer iterations to do when
        bootstrapping.

        For linear interpolation this is defined to be 1, since no
        gain is to be obtained by doing multiple outer iterations.
        For spline interpolation the package parameter
        "spline_max_sweeps" is returned.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the maximum number of outer iterations.
        """

        raise NotImplementedError


class _InterpolationCoefficientsLinear(_InterpolationCoefficients):
    """helper class to calculate interpolation coefficients.

    Implementation for linear interpolation.
    """

    @classmethod
    def calc_coefficient(
        cls,
        interpolation_method: "_InterpolationMethod",
        updated_pillar: Optional[int] = None,
    ) -> None:
        if updated_pillar is None:
            update_indices: List[int] = list(
                range(interpolation_method.n_pillars_set)
            )
        elif updated_pillar == 0:
            update_indices = [0]
        else:
            update_indices = list(
                range(
                    max(0, updated_pillar - 1),
                    min(updated_pillar, interpolation_method.n_pillars_set),
                )
            )
        if update_indices[-1] == interpolation_method.n_pillars_set - 1:
            interpolation_method.set_coefficient(
                0, 1, interpolation_method.n_pillars_set - 1
            )
            _ = update_indices.pop()
        for i in update_indices:
            interpolation_method.set_coefficient(
                (
                    interpolation_method.get_coefficient(0, i + 1)
                    - interpolation_method.get_coefficient(0, i)
                )
                / (
                    interpolation_method.get_time(i + 1)
                    - interpolation_method.get_time(i)
                ),
                1,
                i,
            )

    @staticmethod
    def n_coefficients() -> int:
        return 2

    @classmethod
    def bootstrap_max_sweeps(cls) -> int:
        return 1


class _InterpolationCoefficientsSpline(_InterpolationCoefficients):
    """helper class to calculate interpolation coefficients.

    Abstract Base Class for spline interpolation.
    """

    @classmethod
    def calc_coefficient(
        cls,
        interpolation_method: "_InterpolationMethod",
        updated_pillar: Optional[int] = None,
    ) -> None:
        if interpolation_method.n_pillars_set < 3:
            _InterpolationCoefficientsLinear.calc_coefficient(
                interpolation_method, updated_pillar=updated_pillar
            )
        else:
            cls.calc_spline_coeff_b(
                interpolation_method, updated_pillar=updated_pillar
            )
        if updated_pillar is None:
            update_indices: List[int] = list(
                range(interpolation_method.n_pillars_set)
            )
        else:
            update_indices = list(
                range(
                    max(0, updated_pillar - 2),
                    min(
                        updated_pillar + 1, interpolation_method.n_pillars_set
                    ),
                )
            )
        if update_indices[-1] == interpolation_method.n_pillars_set - 1:
            interpolation_method.set_coefficient(
                0, 2, interpolation_method.n_pillars_set - 1
            )
            interpolation_method.set_coefficient(
                0, 3, interpolation_method.n_pillars_set - 1
            )
            _ = update_indices.pop()
            correct_last: bool = True
        else:
            correct_last = False
        denominator: List[float] = [
            interpolation_method.get_time(i + 1)
            - interpolation_method.get_time(i)
            for i in update_indices
        ]
        coeff_m: List[float] = [
            (
                interpolation_method.get_coefficient(0, j + 1)
                - interpolation_method.get_coefficient(0, j)
            )
            / denominator[i]
            for i, j in enumerate(update_indices)
        ]
        for i, j in enumerate(update_indices):
            interpolation_method.set_coefficient(
                (
                    3 * coeff_m[i]
                    - interpolation_method.get_coefficient(1, j + 1)
                    - 2 * interpolation_method.get_coefficient(1, j)
                )
                / denominator[i],
                2,
                j,
            )
            interpolation_method.set_coefficient(
                (
                    -2 * coeff_m[i]
                    + interpolation_method.get_coefficient(1, j + 1)
                    + interpolation_method.get_coefficient(1, j)
                )
                / denominator[i] ** 2,
                3,
                j,
            )
        if correct_last:
            interpolation_method.apply_spline_correction()

    @staticmethod
    def calc_spline_coeff_b(
        interpolation_method: "_InterpolationMethod",
        updated_pillar: Optional[int] = None,
    ) -> None:  # pragma: no cover
        """calculate the "b" coefficient for spline interpolation.

        parameters
        ----------
        interpolation_method : _InterpolationMethod
            the _InterpolationMethod object
        updated_pillar : int, optional
            the pillar that was updated. If missing all coefficients
            are calculated.

        returns
        -------
        None
        """

        raise NotImplementedError

    @staticmethod
    def n_coefficients() -> int:
        return 4

    @classmethod
    def bootstrap_max_sweeps(cls) -> int:
        return rh_params.spline_max_sweeps


class _InterpolationCoefficientsBessel(_InterpolationCoefficientsSpline):
    """helper class to calculate interpolation coefficients.

    Implementation for Bessel interpolation.
    """

    @staticmethod
    def calc_spline_coeff_b(
        interpolation_method: "_InterpolationMethod",
        updated_pillar: Optional[int] = None,
    ) -> None:
        if updated_pillar is None:
            update_indices: List[int] = list(
                range(interpolation_method.n_pillars_set)
            )
        else:
            if updated_pillar <= 2:
                update_start: int = 0
            else:
                update_start = max(updated_pillar - 1, 0)
            if updated_pillar >= interpolation_method.n_pillars_set - 3:
                update_end: int = interpolation_method.n_pillars_set
            else:
                update_end = min(
                    updated_pillar + 1, interpolation_method.n_pillars_set
                )
            update_indices = list(range(update_start, update_end))
        if update_indices[0] == 0:
            times: List[float] = [
                interpolation_method.get_time(i) for i in range(3)
            ]
            coeff_a: List[float] = [
                interpolation_method.get_coefficient(0, i) for i in range(3)
            ]
            interpolation_method.set_coefficient(
                (
                    (times[2] + times[1] - 2 * times[0])
                    * (coeff_a[1] - coeff_a[0])
                    / (times[1] - times[0])
                    - (times[1] - times[0])
                    * (coeff_a[2] - coeff_a[1])
                    / (times[2] - times[1])
                )
                / (times[2] - times[0]),
                1,
                0,
            )
            _ = update_indices.pop(0)
        if update_indices[-1] == interpolation_method.n_pillars_set - 1:
            times = [
                interpolation_method.get_time(
                    interpolation_method.n_pillars_set - 3 + i
                )
                for i in range(3)
            ]
            coeff_a = [
                interpolation_method.get_coefficient(
                    0, interpolation_method.n_pillars_set - 3 + i
                )
                for i in range(3)
            ]
            interpolation_method.set_coefficient(
                (
                    (times[2] - times[1])
                    * (coeff_a[1] - coeff_a[0])
                    / (times[1] - times[0])
                    - (2 * times[2] - times[1] - times[0])
                    * (coeff_a[2] - coeff_a[1])
                    / (times[2] - times[1])
                )
                / (times[2] - times[0]),
                1,
                interpolation_method.n_pillars_set - 1,
            )
            _ = update_indices.pop()
        coeff_a_plus: List[float] = [
            interpolation_method.get_coefficient(0, i + 1)
            for i in update_indices
        ]
        coeff_a = [
            interpolation_method.get_coefficient(0, i) for i in update_indices
        ]
        coeff_a_min: List[float] = [
            interpolation_method.get_coefficient(0, i - 1)
            for i in update_indices
        ]
        times_plus: list[float] = [
            interpolation_method.get_time(i + 1) for i in update_indices
        ]
        times = [interpolation_method.get_time(i) for i in update_indices]
        times_min: list[float] = [
            interpolation_method.get_time(i - 1) for i in update_indices
        ]
        for i, j in enumerate(update_indices):
            interpolation_method.set_coefficient(
                (
                    (times_plus[i] - times[i])
                    * (coeff_a[i] - coeff_a_min[i])
                    / (times[i] - times_min[i])
                    + (times[i] - times_min[i])
                    * (coeff_a_plus[i] - coeff_a[i])
                    / (times_plus[i] - times[i])
                )
                / (times_plus[i] - times_min[i]),
                1,
                j,
            )


_dp_interpolation_coefficients: _Dispatcher[
    _InterpolationCoefficients
] = _Dispatcher(_InterpolationCoefficients())
"""dispatcher to choose the interpolation method.

_dp_spline_correction.dispatch("linear") returns the class for linear 
interpolation; _dp_spline_correction.dispatch("bessel") returns the class 
for Bessel interpolation. 
"""
_dp_interpolation_coefficients.set_method(
    "linear", _InterpolationCoefficientsLinear()
)
_dp_interpolation_coefficients.set_method(
    "bessel", _InterpolationCoefficientsBessel()
)


class _InterpolationMethod:
    """helper class to do the interpolation for an IRCurve."""

    __slots__ = (
        "_coefficients",
        "n_pillars_set",
        "_interpolation_coefficients",
        "_spline_correction",
        "_times",
    )
    _coefficients: List[List[Optional[float]]]
    n_pillars_set: int
    _interpolation_coefficients: _InterpolationCoefficients
    _spline_correction: _SplineCorrection
    _times: List[float]

    def __init__(
        self,
        interpolation_method: str,
        spline_correction: str,
    ) -> None:
        """constructor for _InterpolationMethod.

        parameters
        ----------
        interpolation_method : str
            the interpolation method
        spline_correction : str
            which spline correction to apply

        returns
        -------
        None
        """

        self._coefficients = []
        self._times = []
        self.n_pillars_set = 0
        self._spline_correction = _dp_spline_correction.dispatch(
            spline_correction
        )
        self._interpolation_coefficients = (
            _dp_interpolation_coefficients.dispatch(interpolation_method)
        )

    @property
    def n_coefficients(self) -> int:
        """the number of interpolation coefficients

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the number of interpolation coefficients
        """

        return self._interpolation_coefficients.n_coefficients()

    @property
    def n_pillars(self) -> int:
        """the total number of pillars

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the total number of pillars
        """

        return len(self._times)

    @property
    def max_sweeps(self) -> int:
        """the maximum number of outer loop iterations for
        bootstrapping.

        parameters
        ----------
        (no parameters)

        returns
        -------
        int
            the maximum number of outer loop iterations
        """

        return self._interpolation_coefficients.bootstrap_max_sweeps()

    def apply_spline_correction(self) -> None:
        """Apply the spline corrections.

        calls _spline_correction.apply_spline_corrections()

        parameters
        ----------
        (no parameters)

        returns
        -------
        None
        """

        self._spline_correction.apply_spline_correction(self)

    def _calc_coefficients(self, updated_pillar: Optional[int] = None) -> None:
        """Calculate the interpolation coefficients

        calls _interpolation_coefficients.calc_coefficient()

        parameters
        ----------
        updated_pillar : int, optional
            the updated pillar. If missing all interpolation
            coefficients are calculated.

        returns
        -------
        None
        """

        self._interpolation_coefficients.calc_coefficient(self, updated_pillar)

    @staticmethod
    def _find_coefficient(
        times: List[float],
        target: float,
        coefficients: List[List[Optional[float]]],
    ) -> Tuple[Optional[float], List[Optional[float]]]:
        """find the interpolation coefficients

        For a target time and a list of input times, the target is
        located within a specific interval and the respective
        interpolation coefficients are returned.

        parameters
        ----------
        times : list of float
            list of times for lookup
        target : float
            the target time
        coefficients : list of list of (float or None)
            the interpolation coefficients

        returns
        -------
        float or None
            the time connected to the coefficients; if missing this
            means extrapolation needs to be applied
        list of (float or None)
            the interpolation coefficients
        """

        if target >= times[-1]:
            return None, [coefficients[0][len(times) - 1]]
        generator = (i for i, time in enumerate(times) if time > target)
        index: int = next(generator)
        if index == 0:
            return None, [coefficients[0][0]]
        return times[index - 1], [c[index - 1] for c in coefficients]

    def get_coefficient(self, row: int, column: int) -> float:
        """get an interpolation coefficient.

        parameters
        ----------
        row : int
            the row of the coefficient array
        column : int
            the column of the coefficient array

        returns
        -------
        float
            the interpolation coefficient requested, or 0 if it is
            None
        """

        coeff = self._coefficients[row][column]
        if coeff is None:
            return 0
        return coeff

    def get_data(
        self,
        times: Optional[List[float]] = None,
        pillars: Optional[List[int]] = None,
        derivative: bool = False,
    ) -> Tuple[List[float], List[float]]:
        """get interpolated data.

        precedence: pillars, times. If both are missing data is
        returned for all pillars.

        parameters
        ----------
        times : list of float or None
            a list of times for which the data is requested
        pillars : list of int or None
            a list of pillars for which the data is requested
        derivative : bool, optional
            do we want interpolated data, or the derivative? default:
            False

        returns
        -------
        list of float
            the requested data
        list of float
            the times connected to the data
        """

        coefficients: List[List[Optional[float]]] = list(
            list(self._coefficients)
        )
        if derivative:
            return_index: int = 1
        else:
            return_index = 0
        if pillars is not None:
            data: List[Optional[float]] = [
                coefficients[return_index][p] for p in pillars
            ]
            return [d for d in data if d is not None], [
                self._times[p] for p in pillars
            ]
        if times is None:
            data = coefficients[return_index]
            return [d for d in data if d is not None], self._times
        if derivative:
            coefficients = [
                [c * k for c in row if c is not None]
                for k, row in enumerate(coefficients)
                if k > 0
            ]
        data = [None for _ in times]
        times_in: List[float] = [
            self._times[i] for i in range(self.n_pillars_set)
        ]
        for k, time in enumerate(times):
            time_out, coeffs = self._find_coefficient(
                times_in, time, coefficients
            )
            coeffs.reverse()
            data_k = coeffs.pop(0)
            if data_k is not None and time_out is not None:
                for coeff in coeffs:
                    if coeff is not None:
                        data_k = data_k * (time - time_out) + coeff
            data[k] = data_k
        return [d for d in data if d is not None], times

    def get_time(self, pillar: int) -> float:
        """get a time value

        parameters
        ----------
        pillar : int
            the pillar for which to find the time value

        returns
        -------
        float
            the time value
        """

        return self._times[pillar]

    def update_pillar(self, value: float, pillar: int) -> None:
        """update the value for a pillar.

        all impacted interpolation coefficients are recalculated.

        parameters
        ----------
        value : float
            the value for updating
        pillar : int
            the pillar that needs to be updated_pillar

        returns
        -------
        None
        """

        if self.n_pillars_set < pillar + 1:
            self.n_pillars_set = pillar + 1
        self._coefficients[0][pillar] = value
        self._calc_coefficients(updated_pillar=pillar)

    def update_all_pillars(self, values: List[float]) -> None:
        """update all pillar values.

        the interpolation coefficients will also be recalculated.

        parameters
        ----------
        values : list of float
            the values for updating

        returns
        -------
        None
        """

        if self.n_pillars_set < len(values):
            self.n_pillars_set = len(values)
        self._coefficients[0] = list(values)
        self._calc_coefficients()

    def set_coefficient(self, value: float, row: int, column: int) -> None:
        """update one specific interpolation coefficient

        parameters
        ----------
        value : float
            the value for updating
        row : int
            the row of the coefficients array where the value needs to
            be updated_pillar
        column : int
            the column of the coefficients array where the value needs to
            be updated_pillar

        returns
        -------
        None
        """

        self._coefficients[row][column] = value

    def set_times(self, times: List[float]) -> None:
        """set the times list

        the interpolation coefficients will be initialized to None

        parameters
        ----------
        times : list of float
            the list of times

        returns
        -------
        None
        """

        if times[0] == 0:
            self._times = times
        else:
            self._times = [0] + times
        self._coefficients = [
            [None for t in self._times] for _ in range(self.n_coefficients)
        ]
