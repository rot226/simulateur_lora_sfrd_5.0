from __future__ import annotations

import hashlib
import numpy as np
from typing import Dict, Tuple


class RngManager:
    """Manage deterministic RNG streams based on MT19937."""

    def __init__(self, master_seed: int) -> None:
        self.master_seed = master_seed
        self._streams: Dict[Tuple[str, int], np.random.Generator] = {}

    def get_stream(self, stream_name: str, node_id: int = 0) -> np.random.Generator:
        """Return a Generator instance for the given stream and node."""
        key = (stream_name, node_id)
        if key not in self._streams:
            # ``hash()`` is not stable across interpreter runs so we
            # derive a deterministic hash from the stream name instead.
            digest = hashlib.sha256(stream_name.encode()).digest()
            stream_hash = int.from_bytes(digest[:8], "little")
            seed = (self.master_seed ^ stream_hash ^ node_id) & 0xFFFFFFFF
            self._streams[key] = np.random.Generator(np.random.MT19937(seed))
        return self._streams[key]
