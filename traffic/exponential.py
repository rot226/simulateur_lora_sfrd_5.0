import random

def sample_interval(mean: float) -> float:
    """Return a delay drawn from an exponential distribution."""
    return random.expovariate(1.0 / mean)
