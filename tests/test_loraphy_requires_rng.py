import pytest
from simulateur_lora_sfrd.phy import LoRaPHY
from simulateur_lora_sfrd.loranode import Node
from simulateur_lora_sfrd.launcher.channel import Channel

def build_nodes():
    ch1 = Channel(
        shadowing_std=0.0,
        fast_fading_std=0.0,
        noise_floor_std=0.0,
        pa_non_linearity_dB=0.0,
        pa_non_linearity_std_dB=0.0,
        frontend_filter_order=0,
    )
    ch2 = Channel(
        shadowing_std=0.0,
        fast_fading_std=0.0,
        noise_floor_std=0.0,
        pa_non_linearity_dB=0.0,
        pa_non_linearity_std_dB=0.0,
        frontend_filter_order=0,
    )
    n1 = Node(0, 0, 0, 7, 14, channel=ch1)
    n2 = Node(1, 0, 0, 7, 14, channel=ch2)
    return n1, n2


def test_transmit_requires_rng():
    src, dest = build_nodes()
    phy = LoRaPHY(src)
    with pytest.raises(ValueError):
        phy.transmit(dest, 20)
