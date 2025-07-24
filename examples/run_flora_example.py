"""Exécution d'un scénario FLoRa prêt à l'emploi."""

from simulateur_lora_sfrd.launcher import Simulator
from simulateur_lora_sfrd.launcher.adr_standard_1 import apply as adr1

CONFIG = "flora-master/simulations/examples/n100-gw1.ini"

if __name__ == "__main__":
    sim = Simulator(flora_mode=True, config_file=CONFIG, seed=1)
    adr1(sim)
    sim.run(1000)
    print(sim.get_metrics())
