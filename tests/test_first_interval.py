import types
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


# Test dashboard callback syncing behaviour

def test_dashboard_first_interval_sync(monkeypatch):
    pn = pytest.importorskip('panel')
    dashboard = pytest.importorskip('simulateur_lora_sfrd.launcher.dashboard')

    dashboard.first_packet_user_edited = False
    dashboard._syncing_first_packet = False
    dashboard.interval_input.value = 10
    dashboard.first_packet_input.value = 10

    event = types.SimpleNamespace(new=20)
    dashboard.on_interval_update(event)
    assert dashboard.first_packet_input.value == 20

    # Simulate user edit breaking the link
    event_fp = types.SimpleNamespace(new=25)
    dashboard.on_first_packet_change(event_fp)
    dashboard.interval_input.value = 30
    dashboard.on_interval_update(types.SimpleNamespace(new=30))
    assert dashboard.first_packet_input.value == 25
