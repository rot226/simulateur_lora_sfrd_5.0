import sys
import pytest

from simulateur_lora_sfrd.launcher.channel import Channel

LIB_NAME = "libflora_phy.dll" if sys.platform.startswith("win") else "libflora_phy.so"


def test_rssi_matches_python_impl():
    try:
        ch_cpp = Channel(phy_model="flora_cpp", shadowing_std=0.0)
    except OSError:
        pytest.skip(f"{LIB_NAME} missing")

    ch_py = Channel(phy_model="flora_full", shadowing_std=0.0)

    rssi_cpp, _ = ch_cpp.compute_rssi(14.0, 100.0, sf=7)
    rssi_py, _ = ch_py.compute_rssi(14.0, 100.0, sf=7)

    assert abs(rssi_cpp - rssi_py) <= 0.01
