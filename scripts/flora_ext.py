from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from setuptools.command.build_ext import build_ext


class BuildFloraExtension(build_ext):
    """Custom build_ext to compile the native FLoRa library.

    It simply delegates to the existing shell script then copies the produced
    ``libflora_phy.dll`` (on Windows) or ``libflora_phy.so`` into the package
    directory so it is bundled with the wheel.
    """

    def build_extension(self, ext):  # type: ignore[override]
        root = Path(__file__).resolve().parent.parent
        scripts_dir = root / "scripts"

        if sys.platform.startswith("win"):
            script = scripts_dir / "build_flora_cpp.ps1"
            subprocess.check_call([
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ])
            lib_name = "libflora_phy.dll"
        else:
            script = scripts_dir / "build_flora_cpp.sh"
            subprocess.check_call(["bash", str(script)])
            lib_name = "libflora_phy.so"

        built = root / "flora-master" / lib_name
        dest = Path(self.build_lib) / "simulateur_lora_sfrd" / "launcher" / lib_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built, dest)
