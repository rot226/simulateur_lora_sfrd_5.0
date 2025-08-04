"""Minimal NumPy stub used for tests when the real package is unavailable."""

from . import random

__all__ = [
    "random",
    "array",
    "zeros",
    "linspace",
    "diff",
    "histogram",
    "isscalar",
    "asarray",
    "ndarray",
    "dtype",
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


# Compatibility helpers for ``pytest`` which expects a few ``numpy`` APIs.
class ndarray(list):
    """Minimal stand‑in for :class:`numpy.ndarray`."""


def asarray(obj):
    """Return a list representation of *obj* as an ``ndarray``."""
    if isinstance(obj, ndarray):
        return obj
    return ndarray(array(obj))


def isscalar(obj) -> bool:
    """Return ``True`` if *obj* behaves like a scalar value."""
    return not isinstance(obj, (list, tuple, dict, set, ndarray))


# Alias used by ``pytest`` when checking for numpy booleans.
bool_ = bool
uint8 = int
int8 = int
int16 = int
uint16 = int
int32 = int
uint32 = int
int64 = int
uint64 = int
float16 = float
float32 = float
float64 = float
__version__ = "0"
class datetime64:
    def __init__(self, value=0, unit="ms"):
        self.value = value
        self.unit = unit


class timedelta64:
    def __init__(self, value=0, unit="ms"):
        self.value = value
        self.unit = unit


class integer(int):
    """Proxy for ``numpy.integer`` scalars."""



class _DType:
    """Minimal stand-in for ``numpy.dtype`` objects."""

    def __init__(self, pytype):
        self.type = pytype


def dtype(obj):
    """Return a very small proxy mimicking :func:`numpy.dtype`.

    Only the ``type`` attribute is provided which is sufficient for the parts
    of ``bokeh`` exercised in the test-suite.
    """

    return _DType(obj)
