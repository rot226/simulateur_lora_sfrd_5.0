from simulateur_lora_sfrd.launcher.gateway import Gateway
from simulateur_lora_sfrd.launcher.server import NetworkServer


def test_orthogonal_sf_no_collision():
    gw = Gateway(0, 0, 0)
    server = NetworkServer()
    server.gateways = [gw]

    gw.start_reception(1, 1, 7, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=True)
    gw.start_reception(2, 2, 9, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=True)
    gw.end_reception(1, server, 1)
    gw.end_reception(2, server, 2)

    assert server.packets_received == 2


def test_cross_sf_collision():
    """Transmissions on the same frequency with different SFs collide when
    ``orthogonal_sf`` is ``False``."""
    gw = Gateway(0, 0, 0)
    server = NetworkServer()
    server.gateways = [gw]

    gw.start_reception(1, 1, 7, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=False)
    gw.start_reception(2, 2, 9, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=False)
    gw.end_reception(1, server, 1)
    gw.end_reception(2, server, 2)

    assert server.packets_received == 0


def test_cross_sf_capture():
    """The strongest of two cross-SF transmissions on the same frequency is
    received when the power difference exceeds the capture threshold."""
    gw = Gateway(0, 0, 0)
    server = NetworkServer()
    server.gateways = [gw]

    gw.start_reception(1, 1, 7, -50, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=False)
    gw.start_reception(2, 2, 9, -60, 1.0, 6.0, 0.0, 868e6, orthogonal_sf=False)
    gw.end_reception(1, server, 1)
    gw.end_reception(2, server, 2)

    assert server.packets_received == 1
