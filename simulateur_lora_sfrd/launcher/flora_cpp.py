import ctypes
import os
import subprocess
import sys
from pathlib import Path

class FloraCppPHY:
    """Wrapper around the native FLoRa physical layer."""

    def __init__(self, lib_path: str | None = None) -> None:
        ext_suffix = "dll" if sys.platform.startswith("win") else "so"
        lib_name = f"libflora_phy.{ext_suffix}"

        default_lib = Path(__file__).with_name(lib_name)
        build_error: Exception | None = None
        if not default_lib.exists():
            root_dir = Path(__file__).resolve().parent.parent.parent
            scripts_dir = root_dir / "scripts"
            if sys.platform.startswith("win"):
                build_script = scripts_dir / "build_flora_cpp.ps1"
                cmd = [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(build_script),
                ]
            else:
                build_script = scripts_dir / "build_flora_cpp.sh"
                cmd = ["bash", str(build_script)]
            try:
                subprocess.run(cmd, check=True, cwd=root_dir)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                build_error = e

        env = os.environ.get("FLORA_CPP_LIB")
        paths: list[Path] = []
        if lib_path:
            paths.append(Path(lib_path))
        if env:
            paths.append(Path(env))
        if not paths:
            paths.extend([
                Path(lib_name),
                default_lib,
                Path(__file__).resolve().parent.parent.parent / "flora-master" / lib_name,
            ])

        self.lib = None
        last_error: Exception | None = None
        for p in paths:
            if p.exists():
                try:
                    self.lib = ctypes.CDLL(str(p))
                    break
                except OSError as e:
                    last_error = e
                    continue
        if self.lib is None:
            msg = f"Impossible de charger {lib_name}"
            if build_error:
                msg += (
                    f" (build failed: {build_error}. "
                    "Install the required toolchain and retry)"
                )
            elif last_error:
                msg += f" ({last_error})"
            raise OSError(msg)

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
        *,
        aloha_channel_model: bool = True,
    ) -> list[bool]:
        length = len(rssi_list)
        if aloha_channel_model and length > 1:
            return [False] * length
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

    def bit_error_rate(self, snr: float, sf: int) -> float:
        """Return BER by delegating to ``flora_per`` with a one-byte payload.

        The native library only exposes a PER computation.  For a payload of
        one byte the relation ``PER = 1 - (1 - BER)^8`` holds, allowing the BER
        to be recovered analytically.
        """

        per = self.lib.flora_per(
            ctypes.c_double(snr), ctypes.c_int(sf), ctypes.c_int(1)
        )
        return float(1.0 - (1.0 - per) ** (1.0 / 8.0))
