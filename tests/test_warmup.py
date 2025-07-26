from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_warmup_intervals():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=5.0,
        packets_to_send=20,
        warm_up_intervals=5,
        log_mean_after=None,
        duty_cycle=0.01,
        mobility=False,
        seed=1,
        pure_poisson_mode=True,
    )
    sim.run()
    node = sim.nodes[0]
    assert node.arrival_interval_count == 20 - 5
    airtime = sim.nodes[0].channel.airtime(sim.nodes[0].sf, payload_size=sim.payload_size_bytes)
    expected = 5.0 + airtime
    average = node.arrival_interval_sum / node.arrival_interval_count
    assert abs(average - expected) / expected < 0.2
