"""Exponential distribution aligned with OMNeT++."""

from __future__ import annotations

import math
import numpy as np


def sample_interval(mean: float, rng: np.random.Generator) -> float:
    """Return a delay drawn from an exponential distribution.

    The value is generated using inverse transform sampling with a
    ``numpy.random.Generator`` based on ``MT19937`` to match the algorithm
    used by OMNeT++.
    """
    if not isinstance(rng, np.random.Generator) or not isinstance(
        rng.bit_generator, np.random.MT19937
    ):
        raise TypeError("rng must be numpy.random.Generator using MT19937")
    u = rng.random()
    while u <= 0.0:
        u = rng.random()
    return -mean * math.log(u)
