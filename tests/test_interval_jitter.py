import numpy as np
from simulateur_lora_sfrd.launcher.node import Node


def test_jitter_changes_intervals():
    rng1 = np.random.Generator(np.random.MT19937(0))
    node1 = Node(0, 0, 0, 7, 20)
    node1.ensure_poisson_arrivals(10.0, rng1, 1.0, limit=5, variation=0.5)
    jittered = list(node1.arrival_queue)

    rng2 = np.random.Generator(np.random.MT19937(0))
    node2 = Node(0, 0, 0, 7, 20)
    node2.ensure_poisson_arrivals(10.0, rng2, 1.0, limit=5)
    base = list(node2.arrival_queue)

    assert jittered != base
    mean_jitter = sum(jittered[i] - (jittered[i-1] if i else 0.0) for i in range(len(jittered))) / len(jittered)
    assert abs(mean_jitter - 1.0) < 0.2
