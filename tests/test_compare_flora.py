import pytest
from pathlib import Path

from launcher.simulator import Simulator
from launcher.compare_flora import compare_with_sim


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
