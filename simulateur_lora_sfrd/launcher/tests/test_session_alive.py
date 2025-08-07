import types
import panel as pn

from launcher import dashboard

def test_session_alive_without_context(monkeypatch):
    doc = types.SimpleNamespace(session_context=None)
    monkeypatch.setattr(pn.state, "curdoc", doc)
    assert dashboard.session_alive() is True

def test_session_alive_inactive(monkeypatch):
    sc = types.SimpleNamespace(session=None, server_context=None)
    doc = types.SimpleNamespace(session_context=sc)
    monkeypatch.setattr(pn.state, "curdoc", doc)
    assert dashboard.session_alive() is False
