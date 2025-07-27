import math
from types import SimpleNamespace

from simulateur_lora_sfrd.launcher.gateway import Gateway
from simulateur_lora_sfrd.launcher.node import Node
from simulateur_lora_sfrd.launcher.server import NetworkServer
from simulateur_lora_sfrd.launcher.lorawan import compute_rx1, compute_rx2


def test_schedule_receive_windows():
    node = Node(1, 0.0, 0.0, 7, 14)
    node.rx_delay = 2
    rx1, rx2 = node.schedule_receive_windows(5.0)
    assert math.isclose(rx1, compute_rx1(5.0, node.rx_delay))
    assert math.isclose(rx2, compute_rx2(5.0, node.rx_delay))


def test_send_downlink_schedules_next_rx_window():
    sim = SimpleNamespace(current_time=0.0, event_queue=[], event_id_counter=0)
    server = NetworkServer(simulator=sim)
    gw = Gateway(1, 0, 0)
    server.gateways = [gw]
    node = Node(1, 0, 0, 7, 14)
    server.nodes = [node]

    node.last_uplink_end_time = 1.0
    server.send_downlink(node, b"d")
    t = server.scheduler.next_time(node.id)
    rx1 = compute_rx1(1.0, node.rx_delay) + server.network_delay
    rx2 = compute_rx2(1.0, node.rx_delay) + server.network_delay
    assert math.isclose(t, rx1) or math.isclose(t, rx2)
