from __future__ import annotations

from random import Random
from typing import Dict, Tuple


class RngManager:
    """Manage deterministic RNG streams."""

    def __init__(self, master_seed: int) -> None:
        self.master_seed = master_seed
        self._streams: Dict[Tuple[str, int], Random] = {}

    def get_stream(self, stream_name: str, node_id: int = 0) -> Random:
        """Return a Random instance for the given stream and node."""
        key = (stream_name, node_id)
        if key not in self._streams:
            seed = self.master_seed ^ hash(stream_name) ^ node_id
            self._streams[key] = Random(seed)
        return self._streams[key]

