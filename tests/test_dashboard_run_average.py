import pytest

dashboard = pytest.importorskip('simulateur_lora_sfrd.launcher.dashboard')


class DummyIndicator:
    def __init__(self):
        self.value = 0


class DummySim:
    def __init__(self):
        self.running = True

    def get_events_dataframe(self):
        return None

    def get_metrics(self):
        return {
            "PDR": 1.0,
            "collisions": 0,
            "energy_J": 0,
            "avg_delay_s": 0,
            "throughput_bps": 0,
            "retransmissions": 0,
        }


def test_average_uses_completed_run_metrics(monkeypatch):
    # patch indicators so on_stop can update values
    for name in [
        "pdr_indicator",
        "collisions_indicator",
        "energy_indicator",
        "delay_indicator",
        "throughput_indicator",
        "retrans_indicator",
    ]:
        monkeypatch.setattr(dashboard, name, DummyIndicator())

    monkeypatch.setattr(dashboard, "update_map", lambda: None)
    monkeypatch.setattr(dashboard, "update_timeline", lambda: None)
    monkeypatch.setattr(dashboard, "_validate_positive_inputs", lambda: True)
    monkeypatch.setattr(dashboard, "setup_simulation", lambda *a, **k: None)

    dashboard.sim = DummySim()
    dashboard.sim_callback = None
    dashboard.chrono_callback = None
    dashboard.map_anim_callback = None
    dashboard.hist_callback = None
    dashboard.metrics_callback = None
    dashboard.start_time = None
    dashboard.max_real_time = None
    dashboard.paused = False
    dashboard.last_step_ts = None
    dashboard.latest_metrics = None

    dashboard.current_run = 1
    dashboard.total_runs = 2
    dashboard.runs_events = []
    dashboard.runs_metrics = [
        {
            "PDR": 0.0,
            "collisions": 0,
            "energy_J": 0,
            "avg_delay_s": 0,
            "throughput_bps": 0,
            "retransmissions": 0,
        }
    ]
    dashboard.completed_run_metrics = []
    dashboard.auto_fast_forward = False

    dashboard.on_stop(None)

    assert dashboard.pdr_indicator.value == 1.0
    assert dashboard.completed_run_metrics[-1]["PDR"] == 1.0
