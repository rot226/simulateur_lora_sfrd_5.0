from random import Random

def sample_interval(mean: float, rng: Random) -> float:
    """Return a delay drawn from an exponential distribution."""
    return rng.expovariate(1.0 / mean)
