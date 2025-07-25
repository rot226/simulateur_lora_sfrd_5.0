import random
from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_interval_distribution_mean():
    """_sample_interval should follow an exponential distribution."""
    mean_interval = 10.0
    sim = Simulator(num_nodes=0, num_gateways=0, packet_interval=mean_interval, mobility=False)
    count = 1_000_000
    total = 0.0
    for _ in range(count):
        total += sim._sample_interval()
    average = total / count
    assert abs(average - mean_interval) / mean_interval < 0.01
