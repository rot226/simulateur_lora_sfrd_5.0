import sys
import pytest

from simulateur_lora_sfrd.launcher.channel import Channel


def test_rssi_matches_python_impl():
    try:
        ch_cpp = Channel(phy_model="flora_cpp", shadowing_std=0.0)
    except OSError:
        ext = ".dll" if sys.platform.startswith("win") else ".so"
        pytest.skip(f"libflora_phy{ext} missing")

    ch_py = Channel(phy_model="flora_full", shadowing_std=0.0)

    rssi_cpp, _ = ch_cpp.compute_rssi(14.0, 100.0, sf=7)
    rssi_py, _ = ch_py.compute_rssi(14.0, 100.0, sf=7)

    assert abs(rssi_cpp - rssi_py) <= 0.01
