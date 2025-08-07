import types
import pytest

panel = pytest.importorskip("panel")
dashboard = pytest.importorskip("simulateur_lora_sfrd.launcher.dashboard")
from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_step_simulation_metrics_vary(monkeypatch):
    """Ensure metrics evolve when stepping the simulator.

    The document's ``session_context`` mimics a Bokeh 3 environment where only
    ``server_context`` is available.  The test would fail without the
    ``session_alive`` fix because the simulation steps would be skipped.
    """
    sc = types.SimpleNamespace(session=None, server_context=object())
    doc = types.SimpleNamespace(session_context=sc)
    monkeypatch.setattr(panel.state, "curdoc", doc)

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
    sim.event_queue = []
    sim.event_id_counter = 0
    for node in sim.nodes:
        sim.schedule_event(node, 0.0, reason="collision")
    node = sim.nodes[0]
    node._nb_trans_left = 1
    sim.schedule_event(node, 1.0, reason="success")

    dashboard.sim = sim
    dashboard.runs_metrics = []

    metrics_list = []
    for _ in range(10):
        dashboard.step_simulation()
        metrics_list.append(dashboard.sim.get_metrics())

    pdr_values = [m["PDR"] for m in metrics_list]
    collisions_values = [m["collisions"] for m in metrics_list]
    throughput_values = [m["throughput_bps"] for m in metrics_list]

    assert len(set(pdr_values)) > 1
    assert len(set(collisions_values)) > 1
    assert len(set(throughput_values)) > 1
