import pytest

# Skip the test gracefully if the dashboard (and its heavy dependencies like
# Panel) are unavailable in the execution environment.
dashboard = pytest.importorskip(
    "simulateur_lora_sfrd.launcher.dashboard",
    reason="dashboard dependencies not available",
    exc_type=Exception,
)


class DummySessionContext:
    def __init__(self):
        # Simulates Bokeh >=3 where the ``session`` attribute is missing
        # but ``server_context`` is still available for active sessions.
        self.server_context = object()


class DummyDoc:
    session_context = DummySessionContext()


def test_session_alive_with_server_context(monkeypatch):
    monkeypatch.setattr(dashboard.pn.state, "curdoc", DummyDoc())
    assert dashboard.session_alive() is True
