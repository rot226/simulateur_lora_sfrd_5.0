import random
from simulateur_lora_sfrd.phy import LoRaPHY
from simulateur_lora_sfrd.loranode import Node
from simulateur_lora_sfrd.launcher.channel import Channel


def test_loraphy_transmit_deterministic():
    ch1 = Channel(shadowing_std=0.0, fast_fading_std=0.0, noise_floor_std=0.0)
    ch2 = Channel(shadowing_std=0.0, fast_fading_std=0.0, noise_floor_std=0.0)
    n1 = Node(0, 0, 0, 7, 14, channel=ch1)
    n2 = Node(1, 0, 0, 7, 14, channel=ch2)

    phy = LoRaPHY(n1)
    rng1 = random.Random(123)
    random.seed(0)
    res1 = phy.transmit(n2, 20, rng=rng1)
    rng2 = random.Random(123)
    random.seed(0)
    res2 = phy.transmit(n2, 20, rng=rng2)
    assert res1 == res2
