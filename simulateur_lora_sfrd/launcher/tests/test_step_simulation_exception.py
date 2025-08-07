import types
import pytest

panel = pytest.importorskip("panel")
dashboard = pytest.importorskip("simulateur_lora_sfrd.launcher.dashboard")
from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_step_simulation_handles_exception(monkeypatch):
    sc = types.SimpleNamespace(session=None, server_context=object())
    doc = types.SimpleNamespace(session_context=sc)
    monkeypatch.setattr(panel.state, "curdoc", doc)

    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=1,
        mobility=False,
        seed=1,
        channels=[868.1e6],
        fixed_sf=7,
    )

    dashboard.sim = sim
    dashboard.runs_metrics = []

    call_count = {"step": 0}

    def failing_step():
        call_count["step"] += 1
        if call_count["step"] == 1:
            raise RuntimeError("boom")
        return True

    monkeypatch.setattr(sim, "step", failing_step)
    monkeypatch.setattr(
        sim,
        "get_metrics",
        lambda: {
            "PDR": 0.0,
            "collisions": 0,
            "energy_J": 0.0,
            "throughput_bps": 0.0,
            "pdr_by_node": {},
            "recent_pdr_by_node": {},
        },
    )

    alerts = []
    monkeypatch.setattr(dashboard, "_add_alert", lambda msg, alert_type="danger": alerts.append(msg))
    stopped = []
    monkeypatch.setattr(dashboard, "on_stop", lambda event: stopped.append(True))

    dashboard.step_simulation()
    assert alerts and "boom" in alerts[0]
    assert stopped

    dashboard.step_simulation()
    assert call_count["step"] == 2
