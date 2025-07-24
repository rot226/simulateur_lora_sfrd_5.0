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
        If ``True``, replace existing :class:`~launcher.channel.Channel` objects
        with :class:`~launcher.advanced_channel.AdvancedChannel` instances using
        more realistic propagation impairments.
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

    if degrade_channel:
        new_channels = []
        for ch in sim.multichannel.channels:
            adv = AdvancedChannel(
                propagation_model="cost231",
                fading="rayleigh",
                variable_noise_std=3.0,
                fine_fading_std=3.0,
                freq_offset_std_hz=400.0,
                sync_offset_std_s=0.004,
                advanced_capture=True,
                frequency_hz=ch.frequency_hz,
                path_loss_exp=ch.path_loss_exp,
                shadowing_std=ch.shadowing_std,
                detection_threshold_dBm=ch.detection_threshold_dBm,
                bandwidth=ch.bandwidth,
                coding_rate=ch.coding_rate,
                capture_threshold_dB=ch.capture_threshold_dB,
            )
            new_channels.append(adv)

        sim.multichannel.channels = new_channels
        sim.channel = sim.multichannel.channels[0]
        sim.network_server.channel = sim.channel
        for node in sim.nodes:
            node.channel = sim.multichannel.select_mask(getattr(node, "chmask", 0xFFFF))

