from launcher.channel import Channel


def test_channel_sensitivity_values():
    channel = Channel()
    expected = {7: -124, 8: -127, 9: -130, 10: -133, 11: -135, 12: -137}
    assert channel.sensitivity_dBm == expected
