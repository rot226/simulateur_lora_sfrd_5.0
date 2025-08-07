import types
import pytest

pn = pytest.importorskip("panel")

from launcher import dashboard


def test_session_alive_without_context(monkeypatch):
    doc = types.SimpleNamespace(session_context=None)
    monkeypatch.setattr(pn.state, "curdoc", doc)
    # A missing session context should not stop callbacks; the dashboard
    # returns True so periodic updates keep running.
    assert dashboard.session_alive() is True
    assert pn.io.with_lock(dashboard.session_alive) is True


def test_session_alive_closed_session(monkeypatch):
    session = types.SimpleNamespace(closed=True)
    sc = types.SimpleNamespace(session=session, server_context=None)
    doc = types.SimpleNamespace(session_context=sc)
    monkeypatch.setattr(pn.state, "curdoc", doc)
    assert dashboard.session_alive() is False


def test_session_alive_active(monkeypatch):
    session = types.SimpleNamespace(closed=False)
    sc = types.SimpleNamespace(session=session, server_context=None)
    doc = types.SimpleNamespace(session_context=sc)
    monkeypatch.setattr(pn.state, "curdoc", doc)
    assert dashboard.session_alive() is True
