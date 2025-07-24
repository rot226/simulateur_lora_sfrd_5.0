from simulateur_lora_sfrd.launcher.gateway import Gateway
from simulateur_lora_sfrd.launcher.server import NetworkServer


def test_orthogonal_sf_no_collision():
    gw = Gateway(0, 0, 0)
    server = NetworkServer()
    server.gateways = [gw]

    gw.start_reception(
        1, 1, 7, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=True
    )
    gw.start_reception(
        2, 2, 9, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=True
    )
    gw.end_reception(1, server, 1)
    gw.end_reception(2, server, 2)

    assert server.packets_received == 2
