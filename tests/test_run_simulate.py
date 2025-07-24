import pytest
from run import simulate, PAYLOAD_SIZE


def test_simulate_single_node_periodic():
    delivered, collisions, pdr, energy, avg_delay, throughput = simulate(
        1,
        1,
        "Periodic",
        1,
        10,
    )
    assert delivered == 10
    assert collisions == 0
    assert pdr == 100.0
    assert energy == 10.0
    assert avg_delay == 0
    assert throughput == PAYLOAD_SIZE * 8


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
