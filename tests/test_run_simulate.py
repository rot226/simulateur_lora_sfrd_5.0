import pytest
from simulateur_lora_sfrd.run import simulate, PAYLOAD_SIZE
from traffic.rng_manager import RngManager


def test_simulate_single_node_periodic():
    rng_manager = RngManager(0)
    delivered, collisions, pdr, energy, avg_delay, throughput = simulate(
        1,
        1,
        "Periodic",
        1.0,
        10,
        rng_manager=rng_manager,
    )
    assert delivered == 10
    assert collisions == 0
    assert pdr == 100.0
    assert energy == 10.0
    assert avg_delay == 0
    assert throughput == PAYLOAD_SIZE * 8 * delivered / 10


def test_simulate_periodic_float_interval():
    rng_manager = RngManager(0)
    delivered, collisions, pdr, _, _, _ = simulate(
        1,
        1,
        "Periodic",
        2.5,
        10,
        rng_manager=rng_manager,
    )
    assert delivered == 4
    assert collisions == 0
    assert pdr == 100.0


@pytest.mark.parametrize(
    "nodes, gateways, mode, interval, steps",
    [
        (0, 1, "random", 10.0, 10),
        (1, 0, "random", 10.0, 10),
        (1, 1, "random", 0.0, 10),
        (1, 1, "random", 10.0, 0),
        (1, 1, "bad", 10.0, 10),
    ],
)
def test_simulate_invalid_parameters(nodes, gateways, mode, interval, steps):
    with pytest.raises(ValueError):
        simulate(nodes, gateways, mode, interval, steps, rng_manager=RngManager(0))
