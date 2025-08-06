"""Stub ``panel`` module used for tests.

If the real `panel` package is available, this stub forwards all imports to it.
Otherwise an ``ImportError`` is raised so dashboard tests can be skipped
gracefully when Panel (or its heavy dependencies) are missing.
"""
from __future__ import annotations

import importlib
import sys

# Temporarily remove the repository path from ``sys.path`` so that Python looks
# for the genuine Panel package in site-packages instead of importing this
# stub again.  If the import succeeds, we expose the real module; otherwise we
# raise ``ImportError`` to signal that Panel is unavailable in this environment.
_repo_path = sys.path.pop(0)
try:  # pragma: no cover - executed only when Panel is installed
    _panel = importlib.import_module("panel")
    import pandas  # noqa: F401  -- Panel requires pandas
    import plotly  # noqa: F401  -- dashboard relies on Plotly
except Exception as exc:  # pragma: no cover - when Panel or deps are missing
    raise ImportError("panel is not available in this test environment") from exc
finally:
    sys.path.insert(0, _repo_path)

# Replace this stub with the real Panel module so callers get full functionality
# when it is installed.
sys.modules[__name__] = _panel
