"""Exponential distribution aligned with OMNeT++."""

from __future__ import annotations

import math
import numpy as np


def sample_interval(mean: float, rng: np.random.Generator) -> float:
    """Return a delay drawn from an exponential distribution.

    ``mean`` is expressed in seconds and must be a positive float. Any
    other type or non-positive value triggers an :class:`AssertionError`.

    The value is generated using inverse transform sampling with a
    ``numpy.random.Generator`` based on ``MT19937`` to match the algorithm
    used by OMNeT++.
    """
    if not isinstance(rng, np.random.Generator) or not isinstance(
        rng.bit_generator, np.random.MT19937
    ):
        raise TypeError("rng must be numpy.random.Generator using MT19937")
    assert isinstance(mean, float) and mean > 0, "mean_interval must be positive float"
    u = rng.random()
    return -mean * math.log(1.0 - u)
