import pytest

# Skip test if dashboard or panel not available
pn = pytest.importorskip("panel")
from simulateur_lora_sfrd.launcher import dashboard

class DummyIndicator:
    def __init__(self):
        self.value = 0

class DummySim:
    def __init__(self):
        self.running = True
        self.counter = 0
    def step(self):
        self.counter += 1
        return True
    def get_metrics(self):
        return {
            "PDR": self.counter,
            "collisions": 0,
            "energy_J": 0,
            "avg_delay_s": 0,
            "throughput_bps": 0,
            "retransmissions": 0,
        }


def test_runs_metrics_capped(monkeypatch):
    # Patch indicators
    for name in [
        "callback_interval_indicator",
        "pdr_indicator",
        "collisions_indicator",
        "energy_indicator",
        "delay_indicator",
        "throughput_indicator",
        "retrans_indicator",
    ]:
        monkeypatch.setattr(dashboard, name, DummyIndicator())
    # Patch session_alive to always return True
    monkeypatch.setattr(dashboard, "session_alive", lambda: True)
    # Set small limit for fast test
    monkeypatch.setattr(dashboard, "RUNS_METRICS_LIMIT", 5, raising=False)
    dashboard.runs_metrics.clear()
    dashboard.sim = DummySim()
    for _ in range(10):
        dashboard.step_simulation()
    assert len(dashboard.runs_metrics) == dashboard.RUNS_METRICS_LIMIT
