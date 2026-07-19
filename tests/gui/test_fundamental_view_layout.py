"""
Regressioni sui bug grafici corretti nella vista fondamentale:
- le tre sotto-tab (Value/Occasioni/ETF) devono restare scrollabili invece
  di comprimere le etichette quando lo spazio verticale disponibile e'
  inferiore al contenuto (successo quando la finestra e' incorporata nella
  GUI unificata, vedi gui/app.py);
- le etichette con un font "grande" dedicato (punteggi, campanelli
  d'allarme, valori numerici) devono ridichiarare le proprie dimensioni ad
  ogni aggiornamento, non affidarsi al solo setFont() di costruzione.
"""

import pytest

pytest.importorskip("PySide6.QtWidgets")
pytest.importorskip("pytestqt")

from PySide6.QtWidgets import QScrollArea

from quantumanalyzer.gui.fundamental_view import MainWindow


@pytest.fixture
def window(qtbot, monkeypatch):
    monkeypatch.setattr(MainWindow, "_check_for_updates", lambda self, silent=True: None)
    monkeypatch.setattr(MainWindow, "_check_first_run_setup", lambda self: None)
    w = MainWindow()
    qtbot.addWidget(w)
    return w


@pytest.mark.parametrize("tab_attr", ["tab_value", "tab_opp", "tab_etf"])
def test_subtabs_content_is_wrapped_in_a_scroll_area(window, tab_attr):
    tab = getattr(window, tab_attr)
    scroll = tab.layout().itemAt(0).widget()
    assert isinstance(scroll, QScrollArea)
    assert scroll.widgetResizable() is True


def test_style_label_always_includes_font_size_and_family(window):
    window._style_label(window.lbl_score, "#c0392b", size_pt=26, bold=True, family="Segoe UI")
    style = window.lbl_score.styleSheet()
    assert "color: #c0392b;" in style
    assert "font-size: 26pt;" in style
    assert "font-family: 'Segoe UI';" in style
    assert "font-weight: bold;" in style


def test_style_label_omits_unspecified_font_properties(window):
    window._style_label(window.lbl_recommendation, "#27ae60")
    assert window.lbl_recommendation.styleSheet() == "color: #27ae60;"


def test_display_results_reasserts_score_label_fonts(window):
    """Regressione: in una gerarchia di widget annidata (come quando questa
    finestra e' incorporata in UnifiedMainWindow), un setStyleSheet() che
    specifichi solo il colore puo' far perdere silenziosamente il font-size
    assegnato altrove con setFont(). _display_results deve ridichiararlo
    sempre tramite _style_label, non solo il colore."""
    for le in window.inputs.values():
        le.setText("10")
    window._on_input_changed()

    for label in (window.lbl_score, window.lbl_opp_score):
        style = label.styleSheet()
        assert "font-size: 26pt;" in style
        assert "font-weight: bold;" in style

    # ey = roic = ev_ebitda = 100%/100%/1.0x con tutti gli input a 10: ramo
    # numerico di set_val_core, che deve includere il font Consolas 12pt.
    for key in ("ey", "roic", "ev_ebitda"):
        assert "font-size: 12pt;" in window.res_labels[key].styleSheet()
        assert "Consolas" in window.res_labels[key].styleSheet()
