import os
import subprocess
import pytest

pn = pytest.importorskip("panel")
pd = pytest.importorskip("pandas")

from simulateur_lora_sfrd.launcher import dashboard


def test_export_to_tmp_dir(tmp_path, monkeypatch):
    df = pd.DataFrame({"a": [1], "b": [2]})
    dashboard.runs_events = [df]
    dashboard.runs_metrics = [{"PDR": 100}]
    dashboard.export_message = pn.pane.Markdown()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: None)
    dashboard.exporter_csv(dest_dir=str(tmp_path))
    files = list(tmp_path.glob("*.csv"))
    assert len(files) == 2
