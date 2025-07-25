import numpy as np
from traffic.exponential import sample_interval


def test_interval_distribution_mean():
    """_sample_interval should follow an exponential distribution."""
    mean_interval = 10.0
    count = 1_000_000
    rng = np.random.Generator(np.random.MT19937(0))
    total = 0.0
    for _ in range(count):
        total += sample_interval(mean_interval, rng)
    average = total / count
    assert abs(average - mean_interval) / mean_interval < 0.01
