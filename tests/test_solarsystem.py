
from unittest.mock import patch

import numpy as np

from beyond.utils.date import Date
from beyond.env.poleandtimes import ScalesDiff
from beyond.env.solarsystem import get_body


def test_moon():
    with patch('beyond.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(-0.0889898, 28.0)
        moon = get_body('Moon', Date(1994, 4, 28))

    assert str(moon.orbit.form) == 'Cartesian'
    assert str(moon.orbit.frame) == 'EME2000'
    assert moon.orbit.propagator.__class__.__name__ == 'MoonPropagator'
    np.testing.assert_array_equal(
        moon.orbit,
        np.array([
            -134181157.31672296, -311598171.54027724, -126699062.43738127, 0.0, 0.0, 0.0
        ])
    )


def test_sun():

    with patch('beyond.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(0.2653703, 33.0)

        sun = get_body('Sun', Date(2006, 4, 2))

        assert str(sun.orbit.form) == 'Cartesian'
        assert str(sun.orbit.frame) == 'MOD'
        assert sun.orbit.propagator.__class__.__name__ == 'SunPropagator'

        np.testing.assert_array_equal(
            sun.orbit,
            np.array([
                146186235643.53641, 28789144480.499767, 12481136552.345926, 0.0, 0.0, 0.0
            ])
        )
        # coord =
        #   x = 146186235644.0
        #   y = 28789144480.5
        #   z = 12481136552.3
        #   vx = 0.0
        #   vy = 0.0
        #   vz = 0.0