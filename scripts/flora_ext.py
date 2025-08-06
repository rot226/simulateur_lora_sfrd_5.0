from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from setuptools.command.build_ext import build_ext


class BuildFloraExtension(build_ext):
    """Custom build_ext to compile the native FLoRa library.

    It simply delegates to the existing shell script then copies the produced
    ``libflora_phy.so`` into the package directory so it is bundled with the
    wheel.
    """

    def build_extension(self, ext):  # type: ignore[override]
        root = Path(__file__).resolve().parent.parent
        script = root / "scripts" / "build_flora_cpp.sh"
        subprocess.check_call(["bash", str(script)])
        built = root / "flora-master" / "libflora_phy.so"
        dest = Path(self.build_lib) / "simulateur_lora_sfrd" / "launcher" / "libflora_phy.so"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built, dest)
