"""
Test della finestra unificata (M4): embedding delle due viste e dispatch
del ticker condiviso a entrambe.
"""

import pytest

pytest.importorskip("PySide6.QtWidgets")
pytest.importorskip("pytestqt")

from quantumanalyzer.gui.app import UnifiedMainWindow
from quantumanalyzer.gui.fundamental_view import MainWindow as FundamentalWindow
from quantumanalyzer.gui.technical_view import MainWindow as TechnicalWindow


@pytest.fixture
def window(qtbot, monkeypatch):
    # La vista fondamentale schedula controllo aggiornamenti e dialogo di
    # primo avvio via QTimer: mockati per non dipendere da rete o input.
    monkeypatch.setattr(FundamentalWindow, "_check_for_updates", lambda self, silent=True: None)
    monkeypatch.setattr(FundamentalWindow, "_check_first_run_setup", lambda self: None)
    w = UnifiedMainWindow()
    qtbot.addWidget(w)
    return w


def test_embeds_both_views_as_tabs(window):
    assert window.tabs.count() == 2
    assert isinstance(window.tabs.widget(0), TechnicalWindow)
    assert isinstance(window.tabs.widget(1), FundamentalWindow)


def test_embedded_menubars_are_not_native(window):
    # Su macOS i menubar nativi delle finestre embedded si contenderebbero
    # la barra di sistema: devono restare in-window.
    assert window.technical.menuBar().isNativeMenuBar() is False
    assert window.fundamental.menuBar().isNativeMenuBar() is False


def test_analyze_both_dispatches_to_both_views(window, monkeypatch):
    calls = []
    monkeypatch.setattr(window.technical, "_on_analyze_clicked", lambda: calls.append("tech"))
    monkeypatch.setattr(window.fundamental, "_on_search_requested", lambda: calls.append("fund"))

    window.shared_ticker.setText("aapl")
    window._on_analyze_both()

    assert sorted(calls) == ["fund", "tech"]
    # Il ticker viene propagato normalizzato (maiuscolo) a entrambe le viste
    assert window.technical.ticker_input.text() == "AAPL"
    assert window.fundamental.input_ticker.text() == "AAPL"
    # e la vista fondamentale viene forzata in modalita' Azioni
    assert window.fundamental.rb_azione.isChecked()


def test_analyze_both_resets_stale_resolved_symbol(window, monkeypatch):
    monkeypatch.setattr(window.technical, "_on_analyze_clicked", lambda: None)
    monkeypatch.setattr(window.fundamental, "_on_search_requested", lambda: None)
    window.technical._resolved = ("MSFT", "Microsoft")

    window.shared_ticker.setText("AAPL")
    window._on_analyze_both()

    assert window.technical._resolved is None


def test_analyze_both_with_empty_ticker_warns_and_does_not_dispatch(window, monkeypatch):
    calls = []
    monkeypatch.setattr(window.technical, "_on_analyze_clicked", lambda: calls.append("tech"))
    monkeypatch.setattr(window.fundamental, "_on_search_requested", lambda: calls.append("fund"))
    warned = []
    from quantumanalyzer.gui import app as app_mod
    monkeypatch.setattr(app_mod.QMessageBox, "warning",
                        staticmethod(lambda *a, **k: warned.append(True)))

    window.shared_ticker.setText("   ")
    window._on_analyze_both()

    assert calls == []
    assert warned
