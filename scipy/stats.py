import math
import statistics

__all__ = ["pearsonr", "kstest", "expon"]


def pearsonr(x, y):
    """Return Pearson correlation coefficient and p-value.

    This is a simplified implementation relying only on the standard library.
    The p-value is approximated using a normal distribution for large sample
    sizes, which is adequate for the tests in this repository.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    n = len(x)
    if n < 2:
        raise ValueError("x and y must contain at least 2 elements")

    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)
    ssxm = sum((a - mean_x) ** 2 for a in x)
    ssym = sum((b - mean_y) ** 2 for b in y)
    if ssxm == 0 or ssym == 0:
        return 0.0, 1.0

    r_num = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    r_den = math.sqrt(ssxm * ssym)
    r = r_num / r_den

    df = n - 2
    if df <= 0 or abs(r) >= 1.0:
        return r, 0.0
    t = r * math.sqrt(df / (1.0 - r * r))
    nd = statistics.NormalDist()
    p = 2 * (1.0 - nd.cdf(abs(t)))
    return r, p


def kstest(samples, cdf, args=()):
    """Kolmogorov-Smirnov test for goodness of fit.

    Supports a callable *cdf* or the string ``"expon"``.
    Returns the KS statistic and an approximate p-value.
    """
    n = len(samples)
    if n == 0:
        return 0.0, 1.0
    samples = sorted(samples)
    if isinstance(cdf, str):
        if cdf != "expon":
            raise NotImplementedError("only 'expon' supported")
        loc = args[0] if len(args) > 0 else 0.0
        scale = args[1] if len(args) > 1 else 1.0
        dist_cdf = expon(loc=loc, scale=scale).cdf
    else:
        dist_cdf = cdf

    d_plus = 0.0
    d_minus = 0.0
    for i, x in enumerate(samples, 1):
        cdf_val = dist_cdf(x)
        d_plus = max(d_plus, i / n - cdf_val)
        d_minus = max(d_minus, cdf_val - (i - 1) / n)
    d = d_plus if d_plus > d_minus else d_minus
    p = 2 * math.exp(-2.0 * n * d * d)
    if p > 1.0:
        p = 1.0
    return d, p


class _ExponDist:
    def __init__(self, loc=0.0, scale=1.0):
        self.loc = loc
        self.scale = scale

    def cdf(self, x: float) -> float:
        if x < self.loc:
            return 0.0
        return 1.0 - math.exp(-(x - self.loc) / self.scale)


def expon(loc=0.0, scale=1.0):
    """Return a simple exponential distribution object."""
    return _ExponDist(loc, scale)
