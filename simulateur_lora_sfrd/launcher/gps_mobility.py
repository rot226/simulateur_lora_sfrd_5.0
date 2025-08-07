import csv
from pathlib import Path
from typing import Iterable, Sequence
from xml.etree import ElementTree
from datetime import datetime


class GPSTraceMobility:
    """Mobility based on time-stamped GPS traces."""

    def __init__(self, trace: str | Iterable[Sequence[float]], loop: bool = True) -> None:
        if isinstance(trace, (str, Path)):
            rows = []
            path = Path(trace)
            if path.suffix.lower() == ".gpx":
                root = ElementTree.parse(path).getroot()
                if "}" in root.tag:
                    ns = {"ns": root.tag.split("}")[0].strip("{")}
                    search = ".//ns:trkpt"
                else:
                    ns = {}
                    search = ".//trkpt"
                prefix = "ns:" if ns else ""
                for i, pt in enumerate(root.findall(search, ns)):
                    lat_attr = pt.attrib.get("lat")
                    lon_attr = pt.attrib.get("lon")
                    lat = float(lat_attr) if lat_attr is not None else 0.0
                    lon = float(lon_attr) if lon_attr is not None else 0.0
                    ele = pt.find(f"{prefix}ele", ns)
                    alt = float(ele.text) if (ele is not None and ele.text is not None) else 0.0
                    time_el = pt.find(f"{prefix}time", ns)
                    time_text = time_el.text if time_el is not None else None
                    if time_text is not None:
                        try:
                            t = datetime.fromisoformat(time_text.replace("Z", "+00:00")).timestamp()
                        except Exception:
                            t = float(i)
                    else:
                        t = float(i)
                    rows.append((t, lon, lat, alt))
            else:
                with open(path, "r", newline="") as f:
                    for row in csv.reader(f):
                        if not row:
                            continue
                        values = [float(v) for v in row]
                        if len(values) == 3:
                            t, x, y = values
                            z = 0.0
                        else:
                            t, x, y, z = (values + [0.0])[:4]
                        rows.append((t, x, y, z))
        else:
            rows = [
                (
                    float(r[0]),
                    float(r[1]) if len(r) > 1 else 0.0,
                    float(r[2]) if len(r) > 2 else 0.0,
                    float(r[3]) if len(r) > 3 else 0.0,
                )
                for r in trace
            ]
        rows.sort(key=lambda r: r[0])
        if rows and rows[0][0] > 1e6:
            base = rows[0][0]
            rows = [(t - base, x, y, z) for (t, x, y, z) in rows]
        if len(rows) < 2:
            raise ValueError("Trace must contain at least two points")
        self.trace = rows
        self.loop = loop

    # ------------------------------------------------------------------
    def assign(self, node) -> None:
        node.trace_index = 0
        node.x = self.trace[0][1]
        node.y = self.trace[0][2]
        node.altitude = self.trace[0][3]
        node.last_move_time = self.trace[0][0]

    # ------------------------------------------------------------------
    def move(self, node, current_time: float) -> None:
        if current_time <= node.last_move_time:
            return
        while (
            node.trace_index < len(self.trace) - 1
            and current_time >= self.trace[node.trace_index + 1][0]
        ):
            node.trace_index += 1
            if node.trace_index >= len(self.trace) - 1:
                if self.loop:
                    node.trace_index = 0
                    current_time = current_time % self.trace[-1][0]
                else:
                    node.last_move_time = current_time
                    return
        t0, x0, y0, z0 = self.trace[node.trace_index]
        t1, x1, y1, z1 = self.trace[node.trace_index + 1]
        ratio = (current_time - t0) / (t1 - t0)
        node.x = x0 + (x1 - x0) * ratio
        node.y = y0 + (y1 - y0) * ratio
        node.altitude = z0 + (z1 - z0) * ratio
        node.last_move_time = current_time


class MultiGPSTraceMobility:
    """Assign a separate GPS trace to each node from a directory."""

    def __init__(self, directory: str | Path, loop: bool = True) -> None:
        path = Path(directory)
        files = [p for p in path.iterdir() if p.suffix.lower() in (".csv", ".gpx")]
        if not files:
            raise ValueError("No trace files found")
        files.sort()
        self.traces = [GPSTraceMobility(f, loop=loop) for f in files]

    def assign(self, node) -> None:
        # Node identifiers in the simulator may start at 0 or 1 depending on
        # how they are created.  Using ``node.id - 1`` would therefore map the
        # first node (id ``0``) to the last trace due to Python's negative
        # indexing.  To ensure a deterministic and intuitive mapping where the
        # first node gets the first trace regardless of the starting index, we
        # simply modulo by the number of traces without the ``- 1`` offset.
        #
        # This fixes incorrect assignments when node ids start at ``0``.
        idx = node.id % len(self.traces)
        node._trace_model = self.traces[idx]
        node._trace_model.assign(node)

    def move(self, node, current_time: float) -> None:
        if hasattr(node, "_trace_model"):
            node._trace_model.move(node, current_time)
