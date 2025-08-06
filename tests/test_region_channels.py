from simulateur_lora_sfrd.launcher.channel import Channel


def test_region_channels_accepts_region_in_kwargs():
    channels = Channel.region_channels("EU868", region="ignored")
    assert len(channels) == len(Channel.REGION_CHANNELS["EU868"])
    assert all(ch.region == "EU868" for ch in channels)
