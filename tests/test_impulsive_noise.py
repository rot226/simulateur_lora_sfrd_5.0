import random
from simulateur_lora_sfrd.launcher.channel import Channel


def test_impulsive_noise_increases_floor():
    random.seed(0)
    base = Channel(noise_floor_std=0.0, variable_noise_std=0.0, fine_fading_std=0.0)
    ch = Channel(
        noise_floor_std=0.0,
        variable_noise_std=0.0,
        fine_fading_std=0.0,
        impulsive_noise_prob=1.0,
        impulsive_noise_dB=20.0,
    )
    assert ch.noise_floor_dBm() >= base.noise_floor_dBm() + 19.0
