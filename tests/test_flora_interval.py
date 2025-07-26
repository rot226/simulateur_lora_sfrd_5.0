from pathlib import Path

from simulateur_lora_sfrd.launcher.simulator import Simulator
from simulateur_lora_sfrd.launcher.config_loader import (
    parse_flora_interval,
    parse_flora_first_interval,
    parse_flora_intervals,
)


def test_flora_ini_interval_parsing():
    ini_path = Path('flora-master/simulations/examples/n100-gw1.ini')
    next_i = parse_flora_interval(ini_path)
    first_i = parse_flora_first_interval(ini_path)
    both = parse_flora_intervals(ini_path)
    assert next_i is not None and first_i is not None
    assert both == (next_i, first_i)
    sim = Simulator(flora_mode=True, config_file=str(ini_path))
    assert sim.packet_interval == next_i
