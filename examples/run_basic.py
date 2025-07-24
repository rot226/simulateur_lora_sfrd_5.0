"""Exemple basique de simulation LoRa."""

import os
import sys

# Ajoute le répertoire parent pour pouvoir importer ``launcher``
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from launcher import Simulator

if __name__ == "__main__":
    sim = Simulator(num_nodes=20, packet_interval=10, transmission_mode="Random")
    sim.run(500)
    print(sim.get_metrics())
