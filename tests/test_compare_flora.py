import pytest
from pathlib import Path

from launcher.simulator import Simulator
from launcher.compare_flora import (
    compare_with_sim,
    load_flora_metrics,
    load_flora_rx_stats,
)


def test_compare_with_flora(tmp_path):
    pytest.importorskip('pandas')
    data_path = Path(__file__).parent / 'data' / 'flora_metrics.csv'
    flora_copy = tmp_path / 'flora_metrics.csv'
    flora_copy.write_bytes(data_path.read_bytes())

    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode='Periodic',
        packet_interval=1.0,
        packets_to_send=10,
        mobility=False,
        fixed_sf=7,
        seed=0,
    )
    sim.run()
    metrics = sim.get_metrics()
    assert compare_with_sim(metrics, flora_copy, pdr_tol=0.01)


def test_load_flora_metrics_from_sca(tmp_path):
    """Metrics should be correctly parsed from a single .sca file."""
    pytest.importorskip('pandas')
    sca = tmp_path / "metrics.sca"
    sca.write_text("""\
scalar sim sent 10
scalar sim received 8
scalar sim sf7 5
scalar sim sf8 3
""")

    metrics = load_flora_metrics(sca)
    assert metrics["PDR"] == pytest.approx(0.8)
    assert metrics["sf_distribution"] == {7: 5, 8: 3}


def test_load_flora_metrics_directory(tmp_path):
    """Aggregated metrics from a directory of .sca files are combined."""
    pytest.importorskip('pandas')
    sca1 = tmp_path / "run1.sca"
    sca1.write_text("""\
scalar sim sent 5
scalar sim received 3
scalar sim sf7 1
scalar sim sf8 4
""")
    sca2 = tmp_path / "run2.sca"
    sca2.write_text("""\
scalar sim sent 5
scalar sim received 4
scalar sim sf7 2
scalar sim sf8 3
""")

    metrics = load_flora_metrics(tmp_path)
    assert metrics["PDR"] == pytest.approx(0.7)
    assert metrics["sf_distribution"] == {7: 3, 8: 7}


def test_compare_with_flora_mismatch(tmp_path):
    """Comparison should fail when metrics differ significantly."""
    pytest.importorskip('pandas')
    data_path = Path(__file__).parent / 'data' / 'flora_metrics.csv'
    flora_copy = tmp_path / 'flora_metrics.csv'
    flora_copy.write_bytes(data_path.read_bytes())

    wrong_metrics = {"PDR": 0.0, "sf_distribution": {7: 0}}
    assert not compare_with_sim(wrong_metrics, flora_copy, pdr_tol=0.01)


def test_rssi_snr_match(tmp_path):
    """Parsed RSSI/SNR values should match simulator results."""
    pytest.importorskip('pandas')
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=1,
        mobility=False,
        fixed_sf=7,
        seed=0,
    )
    sim.run()
    df = sim.get_events_dataframe()
    rssi = float(df["rssi_dBm"].dropna().mean())
    snr = float(df["snr_dB"].dropna().mean())
    sca = tmp_path / "run.sca"
    sca.write_text(
        f"scalar sim sent 1\nscalar sim received 1\nscalar sim rssi {rssi}\nscalar sim snr {snr}\n"
    )
    stats = load_flora_rx_stats(sca)
    assert stats["rssi"] == pytest.approx(rssi)
    assert stats["snr"] == pytest.approx(snr)
