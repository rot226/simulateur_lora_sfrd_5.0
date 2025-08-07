import types
import pytest

pn = pytest.importorskip("panel")
pio = pytest.importorskip("panel.io")


def test_with_lock_callbacks_no_typeerror(monkeypatch):
    doc = types.SimpleNamespace(add_next_tick_callback=lambda cb: cb())
    monkeypatch.setattr(pn.state, "curdoc", doc)

    export_button = types.SimpleNamespace(disabled=True)

    def on_stop(arg):
        pass

    pio.with_lock(lambda: doc.add_next_tick_callback(lambda val=42: None))
    pio.with_lock(lambda: doc.add_next_tick_callback(lambda: None))
    pio.with_lock(lambda: on_stop(None))
    pio.with_lock(lambda: setattr(export_button, "disabled", False))
