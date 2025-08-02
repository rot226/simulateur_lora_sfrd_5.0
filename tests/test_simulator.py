import math
from simulateur_lora_sfrd.launcher.channel import Channel


def test_sensitivity_mode_switch():
    ch_flora = Channel()
    flora_expected = ch_flora.flora_noise_table[7][int(ch_flora.bandwidth)]
    assert ch_flora.sensitivity_dBm[7] == flora_expected

    ch_theoretical = Channel(sensitivity_mode="theoretical")
    bw = ch_theoretical.bandwidth
    noise = -174 + 10 * math.log10(bw) + ch_theoretical.noise_figure_dB
    expected = noise + Channel.SNR_THRESHOLDS[7]
    assert math.isclose(ch_theoretical.sensitivity_dBm[7], expected, abs_tol=0.1)
