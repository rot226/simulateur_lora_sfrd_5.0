import pytest
from pathlib import Path

from simulateur_lora_sfrd.launcher.simulator import Simulator
from simulateur_lora_sfrd.launcher.compare_flora import load_flora_metrics

pytest.importorskip(
    "pandas",
    reason="pandas is required to parse FLoRa metrics",
    exc_type=ImportError,
)

def test_flora_metrics_match(tmp_path):
    data_path = Path(__file__).parent / "data" / "flora_metrics.csv"
    flora_copy = tmp_path / "flora_metrics.csv"
    flora_copy.write_bytes(data_path.read_bytes())

    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=10,
        mobility=False,
        fixed_sf=7,
        seed=0,
        phy_model="flora_full",
    )
    sim.run()
    metrics = sim.get_metrics()
    flora = load_flora_metrics(flora_copy)

    assert abs(metrics["PDR"] - flora["PDR"]) <= 0.01

    total = sum(flora["sf_distribution"].values())
    for sf, expected in flora["sf_distribution"].items():
        got = metrics["sf_distribution"].get(sf, 0)
        if total:
            assert abs(got - expected) / total <= 0.01

    energy = metrics.get("energy_J", 0.0)
    flora_energy = flora.get("energy_J", 0.0)
    if energy:
        assert abs(energy - flora_energy) / energy <= 0.01
