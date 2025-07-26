from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_default_intervals_flora_mode():
    sim = Simulator(flora_mode=True)
    assert sim.packet_interval == 1000.0
    assert sim.first_packet_interval == 1000.0
