from __future__ import annotations

from .simulator import Simulator
from . import server
from .lorawan import TX_POWER_INDEX_TO_DBM


def apply(sim: Simulator, disable_channel_impairments: bool = True) -> None:
    """Configure ADR variant ``adr_standard_1`` (LoRaWAN defaults).

    Parameters
    ----------
    sim:
        Simulation instance to update.
    disable_channel_impairments:
        When ``True`` (default), reset optional channel impairment parameters
        such as fading or advanced capture on all channels of the simulator.
    """
    Simulator.MARGIN_DB = 15.0
    server.MARGIN_DB = Simulator.MARGIN_DB
    sim.adr_node = True
    sim.adr_server = True
    # Utilise la moyenne de SNR sur 20 paquets comme dans FLoRa
    sim.adr_method = "avg"
    sim.network_server.adr_enabled = True
    sim.network_server.adr_method = "avg"
    if disable_channel_impairments and getattr(sim, "multichannel", None):
        impairment_defaults = {
            "fine_fading_std": 0.0,
            "variable_noise_std": 0.0,
            "advanced_capture": False,
            "flora_capture": False,
            "fast_fading_std": 0.0,
            "noise_floor_std": 0.0,
            "time_variation_std": 0.0,
            "frequency_offset_hz": 0.0,
            "freq_offset_std_hz": 0.0,
            "dev_freq_offset_std_hz": 0.0,
            "freq_drift_std_hz": 0.0,
            "clock_drift_std_s": 0.0,
            "clock_jitter_std_s": 0.0,
            "temperature_std_K": 0.0,
            "phase_noise_std_dB": 0.0,
            "pa_non_linearity_dB": 0.0,
            "pa_non_linearity_std_dB": 0.0,
            "pa_ramp_up_s": 0.0,
            "pa_ramp_down_s": 0.0,
            "pa_ramp_current_a": 0.0,
            "humidity_std_percent": 0.0,
            "humidity_noise_coeff_dB": 0.0,
            "impulsive_noise_prob": 0.0,
            "impulsive_noise_dB": 0.0,
            "adjacent_interference_dB": 0.0,
            "tx_power_std": 0.0,
            "interference_dB": 0.0,
            "band_interference": [],
        }
        for ch in sim.multichannel.channels:
            for attr, val in impairment_defaults.items():
                if hasattr(ch, attr):
                    setattr(ch, attr, val)
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
