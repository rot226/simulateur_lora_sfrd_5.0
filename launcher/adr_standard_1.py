from __future__ import annotations

from .simulator import Simulator
from . import server
from .advanced_channel import AdvancedChannel


def apply(sim: Simulator, *, degrade_channel: bool = False) -> None:
    """Configure ADR variant ``adr_standard_1`` (LoRaWAN defaults).

    Parameters
    ----------
    sim : Simulator
        Instance to modify in-place.
    degrade_channel : bool, optional
        Deprecated. Previously enabled additional propagation impairments
        when set to ``True``. This option no longer has any effect.
    """
    Simulator.MARGIN_DB = 15.0
    server.MARGIN_DB = Simulator.MARGIN_DB
    sim.adr_node = False
    sim.adr_server = True
    sim.network_server.adr_enabled = True
    for node in sim.nodes:
        node.sf = 12
        node.initial_sf = 12
        node.tx_power = 14.0
        node.initial_tx_power = 14.0
        node.adr_ack_cnt = 0
        node.adr_ack_limit = 64
        node.adr_ack_delay = 32

    # Channel degradation has been disabled; the parameter is kept for
    # backward compatibility but no additional impairments are applied.
