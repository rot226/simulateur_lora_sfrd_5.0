"""Example reproducing a FLoRa scenario."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from launcher import Simulator
from launcher.adr_standard_1 import apply as adr1

CONFIG = "flora-master/simulations/examples/n100-gw1.ini"

if __name__ == "__main__":
    sim = Simulator(flora_mode=True, config_file=CONFIG, seed=1)
    adr1(sim)
    sim.run(1000)
    print(sim.get_metrics())
