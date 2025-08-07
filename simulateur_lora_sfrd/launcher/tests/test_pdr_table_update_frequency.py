import types
import time
import pandas as pd
import pytest

panel = pytest.importorskip("panel")
dashboard = pytest.importorskip("simulateur_lora_sfrd.launcher.dashboard")


class DummySim:
    def __init__(self):
        self.step_count = 0

    def step(self):
        self.step_count += 1
        return True

    def get_metrics(self):
        return {
            "PDR": float(self.step_count),
            "collisions": 0,
            "energy_J": 0.0,
            "throughput_bps": 0.0,
            "pdr_by_node": {0: float(self.step_count)},
            "recent_pdr_by_node": {0: float(self.step_count)},
        }


def test_pdr_table_throttled_update(monkeypatch):
    """DataFrame for per-node PDR should update only after the configured delay."""
    sc = types.SimpleNamespace(session=None, server_context=object())
    doc = types.SimpleNamespace(session_context=sc)
    monkeypatch.setattr(panel.state, "curdoc", doc)

    dashboard.sim = DummySim()
    dashboard.runs_metrics = []
    dashboard.pdr_table.object = pd.DataFrame(columns=["Node", "PDR", "Recent PDR"])

    # Force update to happen only every 2 steps and disable time-based trigger
    dashboard.PDR_TABLE_UPDATE_STEPS = 2
    dashboard.PDR_TABLE_UPDATE_SECONDS = 999.0
    dashboard.pdr_table_step_counter = 0
    dashboard.pdr_table_last_update = time.time()

    first_df = dashboard.pdr_table.object
    dashboard.step_simulation()
    # No update yet
    assert dashboard.pdr_table.object.equals(first_df)

    dashboard.step_simulation()
    # Second step triggers update
    updated_df = dashboard.pdr_table.object
    assert not updated_df.equals(first_df)
    assert updated_df.loc[0, "PDR"] == pytest.approx(2.0)
