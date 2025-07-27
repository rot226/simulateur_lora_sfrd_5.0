import ctypes
from pathlib import Path

class FloraCppPHY:
    """Wrapper around the native FLoRa physical layer."""

    def __init__(self, lib_path: str | None = None) -> None:
        paths = []
        if lib_path:
            paths.append(Path(lib_path))
        else:
            paths.extend([
                Path("libflora_phy.so"),
                Path(__file__).with_name("libflora_phy.so"),
                Path(__file__).resolve().parent.parent.parent / "flora-master" / "libflora_phy.so",
            ])
        self.lib = None
        for p in paths:
            if p.exists():
                try:
                    self.lib = ctypes.CDLL(str(p))
                    break
                except OSError:
                    continue
        if self.lib is None:
            raise OSError("libflora_phy.so not found")

        self.lib.flora_path_loss.argtypes = [ctypes.c_double]
        self.lib.flora_path_loss.restype = ctypes.c_double
        self.lib.flora_capture.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double), ctypes.c_size_t,
        ]
        self.lib.flora_capture.restype = ctypes.c_int
        self.lib.flora_per.argtypes = [ctypes.c_double, ctypes.c_int, ctypes.c_int]
        self.lib.flora_per.restype = ctypes.c_double

    def path_loss(self, distance: float) -> float:
        return float(self.lib.flora_path_loss(ctypes.c_double(distance)))

    def capture(
        self,
        rssi_list: list[float],
        sf_list: list[int],
        start_list: list[float],
        end_list: list[float],
        freq_list: list[float],
    ) -> list[bool]:
        length = len(rssi_list)
        arr_type_d = ctypes.c_double * length
        arr_type_i = ctypes.c_int * length
        res = self.lib.flora_capture(
            arr_type_d(*rssi_list),
            arr_type_i(*sf_list),
            arr_type_d(*start_list),
            arr_type_d(*end_list),
            arr_type_d(*freq_list),
            ctypes.c_size_t(length),
        )
        winners = [False] * length
        if res >= 0:
            winners[res] = True
        return winners

    def packet_error_rate(self, snr: float, sf: int, payload_bytes: int = 20) -> float:
        return float(self.lib.flora_per(ctypes.c_double(snr), ctypes.c_int(sf), ctypes.c_int(payload_bytes)))
