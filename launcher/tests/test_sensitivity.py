from launcher.channel import Channel


def test_channel_sensitivity_values():
    channel = Channel()
    expected = {7: -123, 8: -126, 9: -129, 10: -132, 11: -134.5, 12: -137}
    assert channel.sensitivity_dBm == expected
