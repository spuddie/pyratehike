import pytest

from pyratehike._interpolation import _InterpolationMethod


class TestGetData:
    iplin = _InterpolationMethod("linear", "no")
    iplin._coefficients = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    iplin._times = [0, 1, 2]
    iplin.n_pillars_set = 3
    ipbes = _InterpolationMethod("bessel", "no")
    ipbes._coefficients = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    ipbes._times = [0, 1, 2]
    ipbes.n_pillars_set = 3

    def test_get_data(self):
        data11, times11 = self.iplin.get_data()
        data12, times12 = self.ipbes.get_data()
        exp11 = [1, 2, 3]
        exp12 = [0, 1, 2]
        assert data11 == exp11
        assert times11 == exp12
        assert data12 == exp11
        assert times12 == exp12

        exp21 = [2, 3]
        exp22 = [1, 2]
        data21, times21 = self.iplin.get_data(pillars=exp22)
        data22, times22 = self.ipbes.get_data(pillars=exp22)
        assert data21 == exp21
        assert times21 == exp22
        assert data22 == exp21
        assert times22 == exp22

        exp31 = [
            1,
            1 + 0.3 * 4 + 0.3**2 * 7 + 0.3**3 * 10,
            2 + 0.3 * 5 + 0.3**2 * 8 + 0.3**3 * 11,
            3,
        ]
        exp32 = [-1, 0.3, 1.3, 2.3]
        data31, times31 = self.iplin.get_data(times=exp32)
        data32, times32 = self.ipbes.get_data(times=exp32)
        assert data31 == pytest.approx(exp31)
        assert times31 == exp32
        assert data32 == pytest.approx(exp31)
        assert times32 == exp32

    def test_get_data_deriv(self):
        data11, times11 = self.iplin.get_data(derivative=True)
        data12, times12 = self.ipbes.get_data(derivative=True)
        exp11 = [4, 5, 6]
        exp12 = [0, 1, 2]
        assert data11 == exp11
        assert times11 == exp12
        assert data12 == exp11
        assert times12 == exp12

        exp21 = [5, 6]
        exp22 = [1, 2]
        data21, times21 = self.iplin.get_data(pillars=exp22, derivative=True)
        data22, times22 = self.ipbes.get_data(pillars=exp22, derivative=True)
        assert data21 == exp21
        assert times21 == exp22
        assert data22 == exp21
        assert times22 == exp22

        exp31 = [
            4,
            4 + 0.3 * 7 * 2 + 0.3**2 * 10 * 3,
            5 + 0.3 * 8 * 2 + 0.3**2 * 11 * 3,
            6,
        ]
        exp32 = [-1, 0.3, 1.3, 2.3]
        data31, times31 = self.iplin.get_data(times=exp32, derivative=True)
        data32, times32 = self.ipbes.get_data(times=exp32, derivative=True)
        assert data31 == pytest.approx(exp31)
        assert times31 == exp32
        assert data32 == pytest.approx(exp31)
        assert times32 == exp32


class TestInterpCoeff:
    times = [0, 5, 6, 9, 11, 12, 15, 16, 17, 18, 19, 20]
    values = [8, 12, 3, 1, 5, 19, 8, 17, 13, 18, 1, 7]

    def test_linear(self):
        ip = _InterpolationMethod("linear", "no")
        ip.set_times(self.times)
        ip.n_pillars_set = len(self.times)
        ip._coefficients[0] = self.values
        ip._calc_coefficients()
        # test continuity
        for i in range(ip.n_pillars - 1):
            assert (
                ip._coefficients[0][i]
                + ip._coefficients[1][i] * (self.times[i + 1] - self.times[i])
                == ip._coefficients[0][i + 1]
            )

    def test_bessel(self):
        ip = _InterpolationMethod("bessel", "no")
        ip.set_times(self.times)
        ip.n_pillars_set = len(self.times)
        ip._coefficients[0] = self.values
        ip._calc_coefficients()
        dx = [
            self.times[i + 1] - self.times[i] for i in range(ip.n_pillars - 1)
        ]

        # test continuity
        for i in range(ip.n_pillars - 1):
            assert ip._coefficients[0][i] + ip._coefficients[1][i] * dx[
                i
            ] + ip._coefficients[2][i] * dx[i] ** 2 + ip._coefficients[3][
                i
            ] * dx[
                i
            ] ** 3 == pytest.approx(
                ip._coefficients[0][i + 1]
            )

        # test continuity derivative
        # test for n_pillars-1 holds by construction of b_n; checking anyway
        for i in range(1, ip.n_pillars - 1):
            assert ip._coefficients[1][i] + ip._coefficients[2][i] * 2 * dx[
                i
            ] + ip._coefficients[3][i] * 3 * dx[i] ** 2 == pytest.approx(
                ip._coefficients[1][i + 1]
            )

        # test value derivative (using lagrange interpolation formula)
        for i in range(1, ip.n_pillars - 1):
            assert (
                -self.values[i - 1] * dx[i] ** 2
                + self.values[i] * (dx[i] ** 2 - dx[i - 1] ** 2)
                + self.values[i + 1] * dx[i - 1] ** 2
            ) / (dx[i - 1] * (dx[i] + dx[i - 1]) * dx[i]) == pytest.approx(
                ip._coefficients[1][i]
            )

    def test_bessel_lincorr(self):
        ip = _InterpolationMethod("bessel", "linear")
        ip.set_times(self.times)
        ip.n_pillars_set = len(self.times)
        ip._coefficients[0] = self.values
        ip._calc_coefficients()
        dx = [
            self.times[i + 1] - self.times[i] for i in range(ip.n_pillars - 1)
        ]

        # test continuity
        for i in range(ip.n_pillars - 1):
            assert ip._coefficients[0][i] + ip._coefficients[1][i] * dx[
                i
            ] + ip._coefficients[2][i] * dx[i] ** 2 + ip._coefficients[3][
                i
            ] * dx[
                i
            ] ** 3 == pytest.approx(
                ip._coefficients[0][i + 1]
            )

        # test zeros
        i = ip.n_pillars - 1
        assert ip._coefficients[1][i] == 0
        assert ip._coefficients[2][i] == 0
        assert ip._coefficients[3][i] == 0
        assert ip._coefficients[2][i - 1] == 0
        assert ip._coefficients[3][i - 1] == 0

        # test continuity derivative
        # (n_pillars - 3 is the last interior point in this case;
        # last interval is n_pillars-2 -> n_pillars -1 is now linear!)
        for i in range(1, ip.n_pillars - 3):
            assert ip._coefficients[1][i] + ip._coefficients[2][i] * 2 * dx[
                i
            ] + ip._coefficients[3][i] * 3 * dx[i] ** 2 == pytest.approx(
                ip._coefficients[1][i + 1]
            )

        # test value derivative (using lagrange interpolation formula)
        for i in range(1, ip.n_pillars - 2):
            assert (
                -self.values[i - 1] * dx[i] ** 2
                + self.values[i] * (dx[i] ** 2 - dx[i - 1] ** 2)
                + self.values[i + 1] * dx[i - 1] ** 2
            ) / (dx[i - 1] * (dx[i] + dx[i - 1]) * dx[i]) == pytest.approx(
                ip._coefficients[1][i]
            )

    def test_bessel_natcorr(self):
        ip = _InterpolationMethod("bessel", "natural")
        ip.set_times(self.times)
        ip.n_pillars_set = len(self.times)
        ip._coefficients[0] = self.values
        ip._calc_coefficients()
        dx = [
            self.times[i + 1] - self.times[i] for i in range(ip.n_pillars - 1)
        ]

        # test continuity
        for i in range(ip.n_pillars - 1):
            assert ip._coefficients[0][i] + ip._coefficients[1][i] * dx[
                i
            ] + ip._coefficients[2][i] * dx[i] ** 2 + ip._coefficients[3][
                i
            ] * dx[
                i
            ] ** 3 == pytest.approx(
                ip._coefficients[0][i + 1]
            )

        # test zeros
        i = ip.n_pillars - 1
        assert ip._coefficients[1][i] == 0
        assert ip._coefficients[2][i] == 0
        assert ip._coefficients[3][i] == 0

        # test continuity derivative
        # this also tests the value of the corrected derivative
        #    (RHS of last interval)
        for i in range(1, ip.n_pillars - 2):
            assert ip._coefficients[1][i] + ip._coefficients[2][i] * 2 * dx[
                i
            ] + ip._coefficients[3][i] * 3 * dx[i] ** 2 == pytest.approx(
                ip._coefficients[1][i + 1]
            )

        # test value derivative (using lagrange interpolation formula)
        for i in range(1, ip.n_pillars - 2):
            assert (
                -self.values[i - 1] * dx[i] ** 2
                + self.values[i] * (dx[i] ** 2 - dx[i - 1] ** 2)
                + self.values[i + 1] * dx[i - 1] ** 2
            ) / (dx[i - 1] * (dx[i] + dx[i - 1]) * dx[i]) == pytest.approx(
                ip._coefficients[1][i]
            )
