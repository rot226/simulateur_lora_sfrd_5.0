import pytest

from simulateur_lora_sfrd.launcher.simulator import Simulator
from simulateur_lora_sfrd import run


def test_simulator_interval_none_uses_packet_interval():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        packet_interval=5.0,
        first_packet_interval=None,
        packets_to_send=1,
        mobility=False,
        seed=0,
    )
    assert sim.packet_interval == 5.0
    assert sim.first_packet_interval == 5.0


def test_cli_first_interval_overrides(monkeypatch):
    captured = {}

    def fake_simulate(nodes, gateways, mode, interval, first_interval, steps, channels=1, *, fine_fading_std=0.0, noise_std=0.0, debug_rx=False, phy_model="omnet", rng_manager=None):
        captured["interval"] = interval
        captured["first_interval"] = first_interval
        captured["steps"] = steps
        return (0, 0, 0, 0, 0, 0)

    monkeypatch.setattr(run, "simulate", fake_simulate)
    run.main([
        "--nodes",
        "1",
        "--gateways",
        "1",
        "--steps",
        "5",
        "--interval",
        "2",
        "--first-interval",
        "7",
    ])
    assert captured["interval"] == 2.0
    assert captured["first_interval"] == 7.0


pn = pytest.importorskip("panel")
dashboard = pytest.importorskip("simulateur_lora_sfrd.launcher.dashboard")


def test_dashboard_inputs_synced():
    dashboard.interval_input.value = 8.0
    assert dashboard.first_interval_input.value == 8.0
    dashboard.first_interval_input.value = 12.0
    assert dashboard.interval_input.value == 12.0
