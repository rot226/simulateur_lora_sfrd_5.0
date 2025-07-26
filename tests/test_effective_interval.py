from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_effective_avg_interval():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=2.0,
        packets_to_send=50,
        duty_cycle=0.01,
        pure_poisson_mode=True,
        mobility=False,
        dump_intervals=False,
        seed=0,
    )
    sim.run()
    metrics = sim.get_metrics()
    airtime = sim.nodes[0].channel.airtime(sim.nodes[0].sf, payload_size=sim.payload_size_bytes)
    expected = 2.0 + airtime
    assert abs(metrics["avg_arrival_interval_s"] - expected) / expected < 0.1
