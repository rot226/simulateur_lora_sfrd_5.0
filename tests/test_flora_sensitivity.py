import re
from pathlib import Path

import sys
import pytest

from simulateur_lora_sfrd.launcher.channel import Channel
from simulateur_lora_sfrd.launcher.flora_phy import FloraPHY
from simulateur_lora_sfrd.launcher.omnet_modulation import calculate_ber


def parse_flora_sensitivity():
    path = Path('flora-master/src/LoRaPhy/LoRaAnalogModel.cc')
    text = path.read_text()
    table = {}
    current_sf = None
    for line in text.splitlines():
        m_sf = re.search(r'getLoRaSF\(\) == (\d+)', line)
        if m_sf:
            current_sf = int(m_sf.group(1))
            table[current_sf] = {}
            continue
        if current_sf is not None:
            m_bw = re.search(r'getLoRaBW\(\) == Hz\((\d+)\).*dBmW2mW\((-?\d+)\)', line)
            if m_bw:
                bw = int(m_bw.group(1))
                val = int(m_bw.group(2))
                table[current_sf][bw] = val
    return table


def test_flora_json_matches_cc():
    expected = parse_flora_sensitivity()
    json_path = Path('simulateur_lora_sfrd/launcher/flora_noise_table.json')
    assert Channel.parse_flora_noise_table(json_path) == expected


def test_flora_noise_path_loading():
    path = Path('flora-master/src/LoRaPhy/LoRaAnalogModel.cc')
    ch = Channel(flora_noise_path=path)
    assert ch.flora_noise_table == parse_flora_sensitivity()


def test_channel_loads_default_json():
    ch = Channel()
    assert ch.flora_noise_table == parse_flora_sensitivity()


def test_flora_exact_ber_matches_formula():
    snr = 5.0
    sf = 7
    payload = 20

    try:
        ch = Channel(phy_model="flora_full", shadowing_std=0.0)
    except OSError:
        ext = ".dll" if sys.platform.startswith("win") else ".so"
        pytest.skip(f"libflora_phy{ext} missing")
    phy = FloraPHY(ch, use_exact_ber=True)

    per = phy.packet_error_rate(snr, sf, payload)

    bitrate = sf * ch.bandwidth * 4.0 / ((1 << sf) * (ch.coding_rate + 4))
    snir = 10 ** (snr / 10.0)
    ber = calculate_ber(snir, ch.bandwidth, bitrate)
    expected = 1.0 - (1.0 - ber) ** (payload * 8)

    assert per == pytest.approx(expected)
