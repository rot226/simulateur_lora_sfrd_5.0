"""Minimal NumPy stub used for tests when the real package is unavailable."""

from . import random

# Minimal scalar type used by pytest.approx
bool_ = bool

__all__ = [
    "random",
    "array",
    "zeros",
    "linspace",
    "diff",
    "histogram",
    "isscalar",
    "bool_",
]


def array(obj, dtype=None):
    if hasattr(obj, "__iter__"):
        return list(obj)
    return [obj]


def zeros(shape, dtype=float):
    if isinstance(shape, int):
        return [0 for _ in range(shape)]
    if len(shape) == 2:
        rows, cols = shape
        return [[0 for _ in range(cols)] for _ in range(rows)]
    raise ValueError("unsupported shape")


def linspace(start, stop, num):
    if num <= 1:
        return [float(start)]
    step = (stop - start) / (num - 1)
    return [start + step * i for i in range(num)]


def diff(a):
    return [a[i + 1] - a[i] for i in range(len(a) - 1)]


def histogram(a, bins=10):
    if not a:
        return [0] * bins, [0] * (bins + 1)
    lo, hi = min(a), max(a)
    if hi == lo:
        edges = [lo + i for i in range(bins + 1)]
        return [len(a)] + [0] * (bins - 1), edges
    width = (hi - lo) / bins
    edges = [lo + i * width for i in range(bins + 1)]
    hist = [0] * bins
    for x in a:
        idx = int((x - lo) / width)
        if idx == bins:
            idx -= 1
        hist[idx] += 1
    return hist, edges


def isscalar(obj) -> bool:
    """Return True if *obj* behaves like a scalar."""
    return not hasattr(obj, "__iter__") or isinstance(obj, (bytes, str, bytearray))
