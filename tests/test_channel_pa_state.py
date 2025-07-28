import random
from simulateur_lora_sfrd.launcher.channel import Channel


def test_channel_start_stop():
    random.seed(0)
    ch = Channel(
        phy_model="basic",
        pa_ramp_up_s=1.0,
        pa_ramp_down_s=1.0,
        shadowing_std=0.0,
        fast_fading_std=0.0,
    )
    ch.start_tx()
    ch.update(0.5)
    r1, _ = ch.compute_rssi(14.0, 10.0)
    ch.update(0.6)
    r2, _ = ch.compute_rssi(14.0, 10.0)
    assert r2 > r1
    ch.stop_tx()
    ch.update(0.5)
    r3, _ = ch.compute_rssi(14.0, 10.0)
    assert r3 < r2
