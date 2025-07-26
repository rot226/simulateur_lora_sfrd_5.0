from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_duty_cycle_keeps_mean_interval():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=5.0,
        packets_to_send=30,
        duty_cycle=0.01,
        mobility=False,
        pure_poisson_mode=True,
        seed=123,
    )
    sim.run()
    metrics = sim.get_metrics()
    airtime = sim.nodes[0].channel.airtime(sim.nodes[0].sf, payload_size=sim.payload_size_bytes)
    expected = 5.0 + airtime
    assert abs(metrics["avg_arrival_interval_s"] - expected) / expected < 0.2


def test_collisions_keep_mean_interval():
    sim = Simulator(
        num_nodes=3,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=5.0,
        packets_to_send=200,
        duty_cycle=0.01,
        mobility=False,
        pure_poisson_mode=True,
        seed=42,
    )
    sim.run()
    metrics = sim.get_metrics()
    airtime = sim.nodes[0].channel.airtime(sim.nodes[0].sf, payload_size=sim.payload_size_bytes)
    expected = 5.0 + airtime
    assert abs(metrics["avg_arrival_interval_s"] - expected) / expected < 0.2
