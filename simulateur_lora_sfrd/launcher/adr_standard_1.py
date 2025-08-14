from __future__ import annotations

from .simulator import Simulator
from . import server
from .advanced_channel import AdvancedChannel
from .lorawan import TX_POWER_INDEX_TO_DBM

# ---------------------------------------------------------------------------
# Default parameters used when degrading channels to a more realistic model.
# These values are applied uniformly to all channels and may be tweaked from a
# single location.
# ---------------------------------------------------------------------------



DEGRADE_PARAMS = {
    "propagation_model": "log_distance",  # ou "cost231" avec n ajusté
    "fading": "rician",                   # ou None
    "path_loss_exp": 3.5,
    "shadowing_std": 6.0,
    "variable_noise_std": 40.0,
    "fine_fading_std": 40.0,
    "freq_offset_std_hz": 200000.0,
    #"sync_offset_std_s": 0.005,
    "sync_offset_std_s": 2.5,
    "advanced_capture": True,            # ou "flora_capture": True si dispo
    "detection_threshold_dBm": -132.0,
    "capture_threshold_dB": 6.0,
}

def apply(sim: Simulator, *, degrade_channel: bool = False) -> None:
    """Configure ADR variant ``adr_standard_1`` (LoRaWAN defaults).

    Parameters
    ----------
    sim : Simulator
        Instance to modify in-place.
    degrade_channel : bool, optional
        If ``True``, replace existing :class:`~launcher.channel.Channel` objects
        with :class:`~launcher.advanced_channel.AdvancedChannel` instances using
        more realistic propagation impairments.
    """
    # Marge ADR
    Simulator.MARGIN_DB = 15.0
    server.MARGIN_DB = Simulator.MARGIN_DB
    sim.adr_node = True
    sim.adr_server = True
    # Utilise la moyenne de SNR sur 20 paquets comme dans FLoRa
    sim.adr_method = "avg"
    sim.network_server.adr_enabled = True
    sim.network_server.adr_method = "avg"
    for node in sim.nodes:
        # Démarre au SF12 pour une sensibilité maximale
        node.sf = 12
        node.initial_sf = 12
        # Démarre avec la puissance TX maximale (14 dBm, index 0)
        max_tx_power = TX_POWER_INDEX_TO_DBM[0]
        node.tx_power = max_tx_power
        node.initial_tx_power = max_tx_power
        # Compteurs ADR
        node.adr_ack_cnt = 0
        node.adr_ack_limit = 64
        node.adr_ack_delay = 32

    if degrade_channel:
        new_channels = []
        for ch in sim.multichannel.channels:
            params = dict(DEGRADE_PARAMS)
            # Conserver les paramètres spécifiques au canal original
            params["frequency_hz"] = ch.frequency_hz
            if hasattr(ch, "bandwidth"):
                params["bandwidth"] = ch.bandwidth
            if hasattr(ch, "coding_rate"):
                params["coding_rate"] = ch.coding_rate
            # Créer un canal avancé avec les paramètres mis à jour
            adv = AdvancedChannel(**params)
            new_channels.append(adv)

        # Remplacer la liste des canaux par les nouveaux canaux dégradés
        sim.multichannel.channels = new_channels
        sim.channel = sim.multichannel.channels[0]
        sim.network_server.channel = sim.channel
        # Mettre à jour la référence de canal de chaque nœud
        for node in sim.nodes:
            node.channel = sim.multichannel.select_mask(getattr(node, "chmask", 0xFFFF))
