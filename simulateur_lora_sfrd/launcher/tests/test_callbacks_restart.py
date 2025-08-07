import importlib
import types
import time

import pytest

panel = pytest.importorskip("panel")


def test_callbacks_restart_after_session_restore(monkeypatch):
    # Prepare a fake Bokeh document and patch before importing dashboard
    sc = types.SimpleNamespace(session=None, server_context=object())
    doc = types.SimpleNamespace(session_context=sc, title="")
    monkeypatch.setattr(panel.state, "curdoc", doc)

    started = {}

    def fake_add(func, period, timeout=None):
        started[func.__name__] = started.get(func.__name__, 0) + 1
        return types.SimpleNamespace(stop=lambda: None)

    monkeypatch.setattr(panel.state, "add_periodic_callback", fake_add)
    dashboard = importlib.reload(importlib.import_module("simulateur_lora_sfrd.launcher.dashboard"))

    from simulateur_lora_sfrd.launcher.simulator import Simulator

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
    sim.running = True

    dashboard.sim = sim
    dashboard.start_time = time.time()

    # Initially callbacks should start
    dashboard._ensure_callbacks()
    assert dashboard.sim_callback is not None
    assert dashboard.hist_callback is not None

    # Simulate session loss and cleanup
    doc.session_context = None
    dashboard._cleanup_callbacks()
    assert dashboard.sim_callback is None
    assert dashboard.hist_callback is None

    # Restore session and ensure callbacks restart
    doc.session_context = sc
    dashboard._ensure_callbacks()
    assert dashboard.sim_callback is not None
    assert dashboard.hist_callback is not None
    assert started["step_simulation"] >= 1
    assert started["update_histogram"] >= 1
