import math
import random

class LogDistanceShadowing:
    """Simple log-distance model with log-normal shadowing."""

    ENV_PARAMS = {
        "urban": (2.7, 6.0),
        "suburban": (2.3, 4.0),
        "rural": (2.0, 2.0),
        "flora": (2.7, 3.57),
    }

    def __init__(self, frequency_hz: float = 868e6, *, path_loss_exp: float = 2.7,
                 shadowing_std: float = 6.0, environment: str | None = None) -> None:
        if environment is not None:
            env = environment.lower()
            if env not in self.ENV_PARAMS:
                raise ValueError(f"Unknown environment: {environment}")
            path_loss_exp, shadowing_std = self.ENV_PARAMS[env]
        self.frequency_hz = frequency_hz
        self.path_loss_exp = path_loss_exp
        self.shadowing_std = shadowing_std

    def path_loss(self, distance: float) -> float:
        if distance <= 0:
            return 0.0
        freq_mhz = self.frequency_hz / 1e6
        pl_d0 = 32.45 + 20 * math.log10(freq_mhz) - 60.0
        loss = pl_d0 + 10 * self.path_loss_exp * math.log10(max(distance, 1.0))
        if self.shadowing_std > 0:
            loss += random.gauss(0.0, self.shadowing_std)
        return loss


def multipath_fading_db(taps: int = 1) -> float:
    """Return a multipath fading value in dB based on Rayleigh paths."""
    taps = int(taps)
    if taps <= 1:
        return 0.0
    i = sum(random.gauss(0.0, 1.0) for _ in range(taps))
    q = sum(random.gauss(0.0, 1.0) for _ in range(taps))
    amp = math.sqrt(i * i + q * q) / math.sqrt(taps)
    return 20 * math.log10(max(amp, 1e-12))
