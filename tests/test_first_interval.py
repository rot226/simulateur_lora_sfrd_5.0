import pytest

from simulateur_lora_sfrd.launcher.simulator import Simulator
import simulateur_lora_sfrd.run as run


# Test that None first_packet_interval defaults to packet_interval

def test_simulator_default_first_interval():
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        mobility=False,
        packets_to_send=1,
        packet_interval=7.5,
        first_packet_interval=None,
    )
    assert sim.packet_interval == 7.5
    assert sim.first_packet_interval == 7.5


# Test that CLI parameter --first-interval overrides default

def test_cli_first_interval_overrides(monkeypatch):
    received = {}

    def fake_simulate(*args, first_interval=None, **kwargs):
        received['first_interval'] = first_interval
        return 0, 0, 0, 0, 0, 0

    monkeypatch.setattr(run, 'simulate', fake_simulate)
    run.main([
        '--nodes', '1',
        '--gateways', '1',
        '--interval', '5',
        '--steps', '10',
        '--first-interval', '3'
    ])
    assert received['first_interval'] == 3.0


def test_first_interval_matches_poisson():
    seed = 123
    sim = Simulator(
        num_nodes=1,
        num_gateways=1,
        transmission_mode="Random",
        packet_interval=5.0,
        first_packet_interval=10.0,
        packets_to_send=2,
        mobility=False,
        pure_poisson_mode=True,
        seed=seed,
    )
    from traffic.rng_manager import RngManager
    from traffic.exponential import sample_interval

    rng = RngManager((seed or 0) ^ 3091881735).get_stream("traffic", 0)
    expected_first = sample_interval(5.0, rng)
    expected_second = expected_first + sample_interval(5.0, rng)

    sim.run()
    times = [e["poisson_time"] for e in sim.nodes[0].interval_log]
    assert times[0] == pytest.approx(expected_first)
    assert times[1] == pytest.approx(expected_second)
