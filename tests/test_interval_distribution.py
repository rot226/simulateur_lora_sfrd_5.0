import numpy as np
import pytest

from traffic.exponential import sample_interval


@pytest.mark.parametrize("seed", range(10))
def test_interval_distribution_mean(seed: int) -> None:
    """``sample_interval`` should preserve the configured mean.

    The test draws ``count`` samples from several RNG streams and checks that
    the empirical mean stays within 1% of ``mean_interval``. Using multiple
    seeds helps detect potential systematic bias in the implementation.
    """

    mean_interval = 10.0
    count = 1_000_000
    rng = np.random.Generator(np.random.MT19937(seed))
    total = 0.0
    for _ in range(count):
        total += sample_interval(mean_interval, rng)
    average = total / count
    assert abs(average - mean_interval) / mean_interval < 0.01
