from __future__ import annotations

from .simulator import Simulator
from . import server
from .lorawan import TX_POWER_INDEX_TO_DBM


def apply(sim: Simulator) -> None:
    """Configure ADR variant ``adr_standard_1`` (LoRaWAN defaults).

    Parameters
    ----------
    sim : Simulator
        Instance to modify in-place.
    """
    Simulator.MARGIN_DB = 15.0
    server.MARGIN_DB = Simulator.MARGIN_DB
    sim.adr_node = True
    sim.adr_server = True
    # Utilise la moyenne de SNR sur 20 paquets comme dans FLoRa
    sim.adr_method = "avg"
    sim.network_server.adr_enabled = True
    sim.network_server.adr_method = "avg"
    for node in sim.nodes:
        node.sf = 12
        node.initial_sf = 12
        # FLoRa uses 2 dBm as the minimum transmit power (index 6)
        min_tx_power = TX_POWER_INDEX_TO_DBM[max(TX_POWER_INDEX_TO_DBM.keys())]
        node.tx_power = min_tx_power
        node.initial_tx_power = min_tx_power
        node.adr_ack_cnt = 0
        node.adr_ack_limit = 64
        node.adr_ack_delay = 32


