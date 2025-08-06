import time
import pytest
from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_metrics_progression():
    sim = Simulator(
        num_nodes=2,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=1,
        mobility=False,
        seed=1,
        channels=[868.1e6],
        fixed_sf=7,
    )
    # Force both nodes to transmit at the same instant to create collisions
    sim.event_queue = []
    sim.event_id_counter = 0
    for node in sim.nodes:
        sim.schedule_event(node, 0.0, reason="test")

    collisions = []
    pdrs = []
    for _ in range(4):
        sim.step()
        metrics = sim.get_metrics()
        collisions.append(metrics["collisions"])
        pdrs.append(metrics["PDR"])

    assert collisions == [0, 0, 1, 2]
    assert pdrs == [0.0, 0.0, 0.0, 0.0]

    # Schedule an additional transmission for one node to ensure a successful delivery
    node = sim.nodes[0]
    node._nb_trans_left = 1
    sim.schedule_event(node, sim.current_time + 1.0, reason="success")

    while sim.event_queue:
        sim.step()
    metrics = sim.get_metrics()
    assert metrics["collisions"] == 2
    assert metrics["PDR"] == pytest.approx(1 / 3)


def test_update_performance():
    sim = Simulator(
        num_nodes=100,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=5,
        mobility=False,
        seed=1,
    )
    start = time.perf_counter()
    for _ in range(1000):
        if not sim.step():
            break
    duration = time.perf_counter() - start
    assert duration < 1.0, f"Simulation step time too slow: {duration}s"
