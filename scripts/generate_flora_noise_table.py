#!/usr/bin/env python3
"""Generate flora_noise_table.json from FLoRa's LoRaAnalogModel.cc."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def parse_flora_cc(path: Path) -> dict[int, dict[int, float]]:
    """Parse LoRaAnalogModel.cc to extract noise thresholds."""
    text = path.read_text()
    table: dict[int, dict[int, float]] = {}
    current_sf: int | None = None
    for line in text.splitlines():
        m_sf = re.search(r"getLoRaSF\(\) == (\d+)", line)
        if m_sf:
            current_sf = int(m_sf.group(1))
            table[current_sf] = {}
            continue
        if current_sf is not None:
            m_bw = re.search(
                r"getLoRaBW\(\) == Hz\((\d+)\).*dBmW2mW\((-?\d+)\)", line
            )
            if m_bw:
                bw = int(m_bw.group(1))
                val = int(m_bw.group(2))
                table[current_sf][bw] = val
    return table


def main() -> None:
    cc_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("flora-master/src/LoRaPhy/LoRaAnalogModel.cc")
    )
    out_path = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else Path("simulateur_lora_sfrd/launcher/flora_noise_table.json")
    )
    table = parse_flora_cc(cc_path)
    out_path.write_text(json.dumps(table, indent=2, sort_keys=True))
    print(f"Written {out_path} with {len(table)} spreading factors")


if __name__ == "__main__":
    main()
