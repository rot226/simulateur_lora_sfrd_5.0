import pytest

panel = pytest.importorskip("panel")
dashboard = pytest.importorskip("simulateur_lora_sfrd.launcher.dashboard")


def test_average_numeric_metrics_union_and_numeric_filtering():
    metrics = [
        {"a": 1, "b": 2, "d": "x"},
        {"a": 3, "c": 4, "d": 5},
        {"a": True, "b": 4, "c": "y"},
    ]
    assert dashboard.average_numeric_metrics(metrics) == {
        "a": 2.0,
        "b": 3.0,
        "c": 4.0,
        "d": 5.0,
    }

