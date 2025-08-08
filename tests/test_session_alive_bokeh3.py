import pytest

# Skip the test gracefully if the dashboard (and its heavy dependencies like
# Panel) are unavailable in the execution environment.
dashboard = pytest.importorskip(
    "simulateur_lora_sfrd.launcher.dashboard",
    reason="dashboard dependencies not available",
    exc_type=Exception,
)


class DummySessionContext:
    def __init__(self, server_present: bool = True):
        # Simulates Bokeh >=3 where the ``session`` attribute is missing.
        # ``server_context`` indicates an active session when present.
        self.server_context = object() if server_present else None


class DummyDoc:
    def __init__(self, server_present: bool = True):
        self.session_context = DummySessionContext(server_present)


def test_session_alive_with_server_context(monkeypatch):
    monkeypatch.setattr(dashboard.pn.state, "curdoc", DummyDoc())
    assert dashboard.session_alive() is True


def test_session_alive_without_server_context(monkeypatch):
    monkeypatch.setattr(dashboard.pn.state, "curdoc", DummyDoc(server_present=False))
    assert dashboard.session_alive() is False
