"""Utility classes for correlated random processes."""

from __future__ import annotations

import numpy as np


class _CorrelatedValue:
    """Correlated random walk used for drifting offsets."""

    def __init__(
        self,
        mean: float,
        std: float,
        correlation: float,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.mean = mean
        self.std = std
        self.corr = correlation
        self.value = mean
        self.rng = rng or np.random.Generator(np.random.MT19937())

    def sample(self) -> float:
        self.value = self.corr * self.value + (1.0 - self.corr) * self.mean
        if self.std > 0.0:
            self.value += self.rng.normal(0.0, self.std)
        return self.value
