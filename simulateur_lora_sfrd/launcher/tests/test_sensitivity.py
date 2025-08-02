import math
from simulateur_lora_sfrd.launcher.channel import Channel


def test_channel_sensitivity_flora():
    channel = Channel()
    expected = {
        sf: channel.flora_noise_table[sf][int(channel.bandwidth)]
        for sf in channel.flora_noise_table
    }
    assert channel.sensitivity_dBm == expected


def test_channel_sensitivity_theoretical():
    channel = Channel(sensitivity_mode="theoretical")
    noise = -174 + 10 * math.log10(channel.bandwidth) + channel.noise_figure_dB
    expected = {sf: noise + snr for sf, snr in Channel.SNR_THRESHOLDS.items()}
    for sf, th in expected.items():
        assert math.isclose(channel.sensitivity_dBm[sf], th, abs_tol=0.1)
