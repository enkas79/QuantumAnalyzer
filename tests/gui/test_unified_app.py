"""
Test della finestra unificata (M4): embedding delle due viste e dispatch
del ticker condiviso a entrambe.
"""

import pytest

pytest.importorskip("PySide6.QtWidgets")
pytest.importorskip("pytestqt")

from PySide6.QtCore import QSettings

from quantumanalyzer.gui.app import UnifiedMainWindow
from quantumanalyzer.gui.fundamental_view import MainWindow as FundamentalWindow
from quantumanalyzer.gui.technical_view import MainWindow as TechnicalWindow

# Stesso namespace QSettings condiviso da entrambe le viste dal restyle
# (vedi gui/app.py, gui/technical_view.py). QSettings scrive su storage
# reale del sistema, persistente fra un test e l'altro nello stesso
# processo: senza pulirlo, un test che analizza un ticker fa trovare quel
# valore gia' in "recent_tickers" al test successivo.
SETTINGS_ORG = "EnricoMartini"
SETTINGS_APP = "QuantumAnalyzer"


@pytest.fixture(autouse=True)
def _clean_settings():
    QSettings(SETTINGS_ORG, SETTINGS_APP).clear()
    yield
    QSettings(SETTINGS_ORG, SETTINGS_APP).clear()


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


def test_fundamental_own_exit_button_is_hidden(window):
    # Ridondante (questa finestra ha gia' il suo File > Esci) e rotto se
    # cliccato qui: self.close() su un widget non top-level lo nasconde
    # soltanto invece di chiudere l'app.
    # isHidden() (non isVisible()): qtbot non mostra mai la finestra
    # top-level nei test, quindi isVisible() sarebbe sempre False anche
    # senza chiamare .hide() — isHidden() riflette il flag esplicito.
    assert window.fundamental.btn_exit.isHidden() is True


def test_closing_the_unified_window_saves_technical_settings(window, monkeypatch, tmp_path):
    """Regressione: TechnicalWindow salva watchlist/tema solo nel proprio
    closeEvent, che Qt non richiama automaticamente sui widget figli non
    top-level quando la finestra unificata si chiude. Senza propagare la
    chiusura, uscire dall'app perderebbe silenziosamente le modifiche alla
    watchlist fatte nella sessione."""
    calls = []
    monkeypatch.setattr(window.technical, "_save_settings", lambda: calls.append(True))
    window.close()
    assert calls == [True]


def test_embedded_menubars_are_hidden(window):
    # Le voci utili sono consolidate nel menu unico di questa finestra
    # (vedi _build_menu); i menu bar interni restano nascosti, cosi' non
    # duplicano ne' rischiano di contendersi la barra di sistema su macOS.
    assert window.technical.menuBar().isHidden() is True
    assert window.fundamental.menuBar().isHidden() is True


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


def test_analyze_both_respects_etf_toggle_instead_of_forcing_azioni(window, monkeypatch):
    """Prima del restyle _on_analyze_both forzava sempre la modalita'
    Azioni; ora rb_azione/rb_etf sono condivisi (spostati nella barra in
    alto, non duplicati) e la scelta dell'utente li' va rispettata."""
    monkeypatch.setattr(window.technical, "_on_analyze_clicked", lambda: None)
    monkeypatch.setattr(window.fundamental, "_on_search_requested", lambda: None)

    window.fundamental.rb_etf.setChecked(True)
    window.shared_ticker.setText("SWDA")
    window._on_analyze_both()

    assert window.fundamental.rb_etf.isChecked()
    assert not window.fundamental.rb_azione.isChecked()


def test_analyze_both_resets_stale_resolved_symbol(window, monkeypatch):
    monkeypatch.setattr(window.technical, "_on_analyze_clicked", lambda: None)
    monkeypatch.setattr(window.fundamental, "_on_search_requested", lambda: None)
    window.technical._resolved = ("MSFT", "Microsoft")

    window.shared_ticker.setText("AAPL")
    window._on_analyze_both()

    assert window.technical._resolved is None


def test_analyze_both_updates_recent_ticker_history(window, monkeypatch):
    monkeypatch.setattr(window.technical, "_on_analyze_clicked", lambda: None)
    monkeypatch.setattr(window.fundamental, "_on_search_requested", lambda: None)

    for ticker in ["AAPL", "ENI.MI", "AAPL"]:
        window.shared_ticker.setText(ticker)
        window._on_analyze_both()

    # Ultimo analizzato in testa, senza duplicati
    assert window.recent_tickers == ["AAPL", "ENI.MI"]
    assert window.completer_model.stringList() == ["AAPL", "ENI.MI"]
    assert window.settings.value("shared_recent_tickers") == ["AAPL", "ENI.MI"]


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


# ----------------------------------------------------------------------
# Consolidamento controlli duplicati (restyle): la barra condivisa
# sostituisce le caselle di ricerca proprie di ciascuna vista, riusando
# (non duplicando) l'unico controllo senza equivalente li' — lo switch
# Azioni/ETF della vista fondamentale.
# ----------------------------------------------------------------------

def test_asset_toggle_is_moved_into_shared_bar_not_duplicated(window):
    # isHidden() (non isVisible()): riflette il flag di visibilita' esplicito
    # del singolo widget, indipendente dal fatto che qtbot non mostri mai la
    # finestra top-level nei test (isVisible() sarebbe sempre False li').
    assert window.fundamental.rb_azione.parentWidget() is window.centralWidget()
    assert window.fundamental.rb_etf.parentWidget() is window.centralWidget()
    assert window.fundamental.rb_azione.isHidden() is False
    assert window.fundamental.rb_etf.isHidden() is False


def test_fundamental_search_box_is_hidden(window):
    assert window.fundamental.search_group.isHidden() is True


def test_technical_ticker_row_is_hidden_but_parameters_remain(window):
    assert window.technical.ticker_label.isHidden() is True
    assert window.technical.ticker_input.isHidden() is True
    assert window.technical.analyze_button.isHidden() is True
    # Periodo/intervallo/leg opzionali non hanno equivalente nella barra
    # condivisa: devono restare visibili e usabili.
    assert window.technical.period_combo.isHidden() is False
    assert window.technical.interval_combo.isHidden() is False
    assert window.technical.macd_checkbox.isHidden() is False


# ----------------------------------------------------------------------
# Menu unico (restyle): consolida le voci prima sparse nei due menu bar
# interni (nascosti, vedi sopra) — guida e configurazione API erano gia'
# presenti in QuantumValue/StockAnalyzer ma sepolte in una seconda barra
# menu duplicata, difficile da notare nella finestra unificata.
# ----------------------------------------------------------------------

def _menu_titles(window):
    return [a.text().replace("&", "") for a in window.menuBar().actions()]


def _find_action(window, menu_title, action_text_substr):
    for menu_action in window.menuBar().actions():
        if menu_action.text().replace("&", "") == menu_title:
            for a in menu_action.menu().actions():
                if action_text_substr in a.text().replace("&", ""):
                    return a
    return None


def test_unified_menu_has_all_four_top_level_menus(window):
    assert _menu_titles(window) == ["File", "Visualizza", "Guida", "Aiuto"]


def test_export_csv_action_calls_fundamental_export(window, monkeypatch):
    calls = []
    monkeypatch.setattr(window.fundamental, "_export_csv", lambda: calls.append(True))
    action = _find_action(window, "File", "Esporta Analisi")
    assert action is not None
    action.trigger()
    assert calls == [True]


def test_reset_api_action_calls_fundamental_reset(window, monkeypatch):
    calls = []
    monkeypatch.setattr(window.fundamental, "_reset_api_key", lambda: calls.append(True))
    action = _find_action(window, "File", "Reimposta API")
    assert action is not None
    action.trigger()
    assert calls == [True]


def test_update_check_action_calls_fundamental_check(window, monkeypatch):
    calls = []
    monkeypatch.setattr(window.fundamental, "_check_for_updates", lambda silent=True: calls.append(silent))
    action = _find_action(window, "Aiuto", "Verifica Aggiornamenti")
    assert action is not None
    action.trigger()
    assert calls == [False]  # non silenzioso: l'utente l'ha chiesto esplicitamente


def test_guide_menu_opens_both_guides(window, monkeypatch):
    from PySide6.QtWidgets import QDialog
    opened = []
    monkeypatch.setattr(window.technical, "_show_guide", lambda: opened.append("tech"))

    from quantumanalyzer.gui import app as app_mod
    monkeypatch.setattr(app_mod, "GuideDialog",
                        lambda parent: opened.append("fund") or type("_D", (), {"exec": lambda self: None})())

    tech_action = _find_action(window, "Guida", "Analisi Tecnica")
    fund_action = _find_action(window, "Guida", "Fondamentale")
    assert tech_action is not None and fund_action is not None
    tech_action.trigger()
    fund_action.trigger()
    assert sorted(opened) == ["fund", "tech"]


def test_theme_menu_actions_apply_to_both_views(window, monkeypatch):
    from quantumanalyzer.gui import theme
    calls = []
    monkeypatch.setattr(window.fundamental, "_set_theme", lambda n: calls.append(("fund", n)))
    monkeypatch.setattr(window.technical, "_apply_theme", lambda n: calls.append(("tech", n)))

    dark_action = _find_action(window, "Visualizza", "Scuro")
    assert dark_action is not None
    dark_action.trigger()

    assert ("fund", "dark") in calls
    assert ("tech", "dark") in calls


def test_set_theme_helper_updates_both_views_for_real(window):
    """Senza mock: verifica che il tema resti coerente fra le due viste
    (il bug che il restyle ha corretto era proprio le due app.setStyleSheet()
    indipendenti che si sovrascrivevano a vicenda)."""
    from quantumanalyzer.gui import theme
    window._set_theme("dark")
    assert theme.current_theme() == "dark"
    assert window.technical._theme == "dark"
    assert window.fundamental.settings.value("theme") == "dark"
