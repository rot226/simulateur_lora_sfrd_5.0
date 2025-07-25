from pathlib import Path

from simulateur_lora_sfrd.launcher.simulator import Simulator
from simulateur_lora_sfrd.launcher.config_loader import parse_flora_interval


def test_flora_ini_interval_parsing():
    ini_path = Path('flora-master/simulations/examples/n100-gw1.ini')
    mean_f = parse_flora_interval(ini_path)
    assert mean_f is not None
    sim = Simulator(flora_mode=True, config_file=str(ini_path))
    assert sim.packet_interval == mean_f
