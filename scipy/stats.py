import math
import statistics

__all__ = ["pearsonr"]


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
