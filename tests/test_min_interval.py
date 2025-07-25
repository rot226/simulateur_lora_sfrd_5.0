from simulateur_lora_sfrd.launcher.simulator import Simulator


def test_next_event_after_airtime():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=1.0,
        packets_to_send=5,
        pure_poisson_mode=True,
        mobility=False,
        seed=1,
    )
    sim.run()
    events = sim.events_log
    for i in range(len(events) - 1):
        airtime = events[i]["end_time"] - events[i]["start_time"]
        delta = events[i + 1]["start_time"] - events[i]["start_time"]
        assert delta >= airtime
