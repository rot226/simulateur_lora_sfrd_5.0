from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_rx_chain_single_node():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=3,
        mobility=False,
        seed=1,
    )
    sim.run()
    metrics = sim.get_metrics()
    assert metrics["PDR"] > 0
    assert metrics["pdr_by_node"][1] > 0


def test_rx_chain_multiple_nodes():
    sim = Simulator(
        num_nodes=3,
        num_gateways=1,
        transmission_mode="Periodic",
        packet_interval=1.0,
        packets_to_send=3,
        mobility=False,
        seed=1,
    )
    sim.run()
    metrics = sim.get_metrics()
    assert metrics["PDR"] > 0
    for pdr in metrics["pdr_by_node"].values():
        assert pdr > 0
