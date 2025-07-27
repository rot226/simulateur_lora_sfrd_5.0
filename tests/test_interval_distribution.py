import numpy as np
import pytest
import math
import scipy.stats

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


@pytest.mark.parametrize("seed", range(10))
def test_interval_distribution_cv(seed: int) -> None:
    """``sample_interval`` should have a coefficient of variation of 1."""

    mean_interval = 10.0
    count = 1_000_000
    rng = np.random.Generator(np.random.MT19937(seed))
    total = 0.0
    sumsq = 0.0
    for _ in range(count):
        x = sample_interval(mean_interval, rng)
        total += x
        sumsq += x * x
    mean = total / count
    variance = sumsq / count - mean * mean
    std = math.sqrt(variance)
    cv = std / mean
    assert abs(cv - 1.0) < 0.02


@pytest.mark.parametrize("seed", range(10))
def test_interval_distribution_ks(seed: int) -> None:
    """``sample_interval`` should match an exponential distribution."""

    mean_interval = 10.0
    rng = np.random.Generator(np.random.MT19937(seed))
    samples = [sample_interval(mean_interval, rng) for _ in range(10_000)]
    statistic, pvalue = scipy.stats.kstest(samples, "expon", args=(0, mean_interval))
    assert pvalue >= 0.05
