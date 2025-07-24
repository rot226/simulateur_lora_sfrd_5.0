import pytest
from run import simulate, PAYLOAD_SIZE
import random


def test_simulate_single_node_periodic():
    random.seed(0)
    delivered, collisions, pdr, energy, avg_delay, throughput = simulate(
        1,
        1,
        "Periodic",
        1,
        10,
    )
    assert delivered == 9
    assert collisions == 0
    assert pdr == 100.0
    assert energy == 9.0
    assert avg_delay == 0
    assert throughput == PAYLOAD_SIZE * 8 * delivered / 10


def test_simulate_periodic_float_interval():
    random.seed(0)
    delivered, collisions, pdr, _, _, _ = simulate(
        1,
        1,
        "Periodic",
        2.5,
        10,
    )
    assert delivered == 3
    assert collisions == 0
    assert pdr == 100.0


@pytest.mark.parametrize(
    "nodes, gateways, mode, interval, steps",
    [
        (0, 1, "random", 10, 10),
        (1, 0, "random", 10, 10),
        (1, 1, "random", 0, 10),
        (1, 1, "random", 10, 0),
        (1, 1, "bad", 10, 10),
    ],
)
def test_simulate_invalid_parameters(nodes, gateways, mode, interval, steps):
    with pytest.raises(ValueError):
        simulate(nodes, gateways, mode, interval, steps)


def test_simulate_collision():
    """Packets lost in a collision should not be retried indefinitely."""
    random.seed(0)
    delivered, collisions, pdr, energy, avg_delay, throughput = simulate(
        2,
        1,
        "Periodic",
        1,
        3,
    )
    assert delivered == 2
    assert collisions == 2
    assert energy == 4.0
    assert avg_delay == 0
    assert throughput == PAYLOAD_SIZE * 8 * delivered / 3
