from simulateur_lora_sfrd.launcher.simulator import Simulator
from simulateur_lora_sfrd.launcher.adr_standard_1 import apply as apply_adr


def test_interval_with_degraded_channel():
    mean_interval = 2.0
    packets = 1000
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=mean_interval,
        packets_to_send=packets,
        pure_poisson_mode=True,
        mobility=False,
        seed=1,
    )
    apply_adr(sim, degrade_channel=True)
    sim.run()
    node = sim.nodes[0]
    average = node._last_arrival_time / node.packets_sent
    assert node.packets_sent == packets
    airtime = sum(e['end_time'] - e['start_time'] for e in sim.events_log) / len(sim.events_log)
    expected = mean_interval + airtime
    assert abs(average - expected) / expected < 0.03
