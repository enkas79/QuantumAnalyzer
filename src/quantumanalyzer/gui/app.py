"""
Finestra principale unificata di QuantumAnalyzer (milestone M4 + restyle).

Un'unica finestra con un campo ticker condiviso e due tab che ospitano le
finestre esistenti: "Analisi Tecnica" (portata da StockAnalyzer) e "Analisi
Fondamentale" (portata da QuantumValue). Il campo condiviso smista il ticker
a entrambe le viste, che avviano i rispettivi fetch in parallelo sui propri
worker QThread: nessuna delle due analisi blocca l'altra.

Le due viste embedded conservano la propria logica ma non piu' la propria
GUI di cornice: i menu bar interni sono nascosti (le voci utili — guide,
tema, API key, export CSV, aggiornamenti — sono consolidate nell'unico menu
di questa finestra, altrimenti erano davvero presenti ma sepolte in una
seconda barra menu per tab, poco distinguibile dalla prima) e le rispettive
caselle di ricerca ticker sono nascoste (sostituite dalla barra condivisa
sopra), mantenendo pero' i controlli che non hanno equivalente condiviso
(periodo/intervallo/leg opzionali per la tecnica, switch Azioni/ETF per la
fondamentale — quest'ultimo spostato qui nella barra condivisa, invece di
restare isolato in un box altrimenti vuoto).

Autore: Enrico Martini
"""

import sys

from PySide6.QtCore import QSettings, QStringListModel, Qt
from PySide6.QtGui import QAction, QActionGroup, QFont
from PySide6.QtWidgets import (
    QApplication, QCompleter, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget
)

from ..common.legacy_import import migrate_legacy_data
from ..fundamental import utils
from ..fundamental.config import APP_NAME, AUTHOR, VERSION
from . import theme
from .fundamental_view import GuideDialog, MAX_RECENT_TICKERS
from .fundamental_view import MainWindow as FundamentalWindow
from .technical_view import MainWindow as TechnicalWindow


class UnifiedMainWindow(QMainWindow):
    """Contenitore delle due analisi con barra ticker condivisa e menu unico."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.settings = QSettings(AUTHOR.replace(" ", ""), APP_NAME.replace(" ", ""))

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # --- Le due viste embedded, create prima della barra condivisa: -----
        # quest'ultima riusa lo switch Azioni/ETF della vista fondamentale
        # (vedi sotto), quindi deve gia' esistere. I menu bar interni sono
        # nascosti: le loro voci utili confluiscono nel menu unico costruito
        # da _build_menu() piu' sotto.
        self.technical = TechnicalWindow()
        self.technical.menuBar().hide()
        self.fundamental = FundamentalWindow()
        self.fundamental.menuBar().hide()

        # --- Barra ticker condivisa -----------------------------------------
        bar = QHBoxLayout()
        lbl = QLabel("Ticker:")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        bar.addWidget(lbl)

        self.shared_ticker = QLineEdit()
        self.shared_ticker.setPlaceholderText(
            "Es. AAPL, ENI.MI — avvia analisi tecnica e fondamentale insieme")
        self.shared_ticker.setMaximumWidth(420)
        self.shared_ticker.returnPressed.connect(self._on_analyze_both)

        # Cronologia degli ultimi ticker analizzati dalla barra condivisa,
        # persistita fra le sessioni e suggerita mentre si digita. Decisione
        # M4.3: watchlist (tab tecnica) e recenti (tab fondamentale) restano
        # separate — servono a scopi diversi (titoli da ri-analizzare vs
        # cronologia di ricerca); questa e' la cronologia unificata della
        # barra condivisa.
        recent = self.settings.value("shared_recent_tickers", [])
        if isinstance(recent, str):
            recent = [recent] if recent else []
        self.recent_tickers: list = [str(t) for t in (recent or [])][:MAX_RECENT_TICKERS]
        self.completer_model = QStringListModel(self.recent_tickers)
        completer = QCompleter(self.completer_model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.shared_ticker.setCompleter(completer)
        bar.addWidget(self.shared_ticker)

        # Switch Azioni/ETF: sposta qui (non duplica) i radio button della
        # vista fondamentale, l'unica parte del suo box "1. Ricerca" senza
        # equivalente nella barra condivisa. _on_search_requested() li legge
        # gia' direttamente (self.rb_azione.isChecked()), quindi funzionano
        # identici alla posizione originale.
        bar.addSpacing(12)
        bar.addWidget(self.fundamental.rb_azione)
        bar.addWidget(self.fundamental.rb_etf)
        bar.addSpacing(12)

        self.btn_analyze_both = QPushButton("Analizza")
        self.btn_analyze_both.clicked.connect(self._on_analyze_both)
        bar.addWidget(self.btn_analyze_both)
        bar.addStretch()
        layout.addLayout(bar)

        # Con rb_azione/rb_etf gia' spostati sopra, il resto del box di
        # ricerca fondamentale (ticker + bottone fetch) e la riga ticker
        # tecnica duplicano la barra condivisa: nascosti.
        self.technical.hide_ticker_row()
        self.fundamental.hide_search_box()

        # --- Tab con le due viste embedded ----------------------------------
        self.tabs = QTabWidget()
        self.tabs.addTab(self.technical, "Analisi Tecnica (Trend)")
        self.tabs.addTab(self.fundamental, "Analisi Fondamentale (Value)")
        layout.addWidget(self.tabs)

        # Le etichette di punteggio della vista fondamentale usano un font
        # grande impostato con setFont() in fase di costruzione, quando
        # 'fundamental' non aveva ancora un parent. Il reparenting in questa
        # finestra a piu' livelli di tab annidati (fatto da addTab() sopra)
        # fa si' che Qt risolva da qui in poi il font di quelle etichette
        # via cascata CSS invece di usare il QFont assegnato, ereditando una
        # dimensione minuscola dagli antenati. _reset_results()/
        # _reset_etf_results() ridichiarano quel font esplicitamente via
        # stylesheet (vedi _style_label in fundamental_view.py): chiamarli
        # qui, subito dopo l'incorporamento, ripara lo stato "in attesa di
        # dati" iniziale invece di mostrarlo per un istante compresso.
        self.fundamental._reset_results()
        self.fundamental._reset_etf_results()

        # Il grande bottone rosso "Esci dal Programma" della vista
        # fondamentale ha senso in QuantumValue standalone, ma qui e'
        # ridondante (questa finestra ha gia' il suo File > Esci) e in piu'
        # rotto: chiama self.close() su 'fundamental', che essendo un widget
        # non top-level si limiterebbe a nascondersi invece di chiudere
        # l'app, lasciando la tab Fondamentale vuota. Nascosto: recupera
        # anche i suoi ~60px di margine verticale.
        self.fundamental.btn_exit.hide()

        self.setCentralWidget(central)
        self._build_menu()

        last = str(self.settings.value("shared_ticker", ""))
        if last:
            self.shared_ticker.setText(last)

    def closeEvent(self, event) -> None:
        """Propaga la chiusura alla tab tecnica prima di uscire.

        TechnicalWindow salva watchlist/tema solo nel proprio closeEvent
        (vedi technical_view.py: _save_settings() non ha altri punti di
        chiamata). Qt non inoltra closeEvent ai widget figli non top-level
        quando questa finestra si chiude, quindi senza questa chiamata
        esplicita quel salvataggio non scatterebbe mai in QuantumAnalyzer:
        chiudere l'app dal menu File > Esci perderebbe silenziosamente le
        modifiche alla watchlist fatte nella sessione.
        """
        self.technical.close()
        super().closeEvent(event)

    def _build_menu(self) -> None:
        """Menu unico dell'app: consolida le voci prima sparse nei due menu
        bar interni (ciascuno nascosto, vedi __init__), cosi' guide e
        configurazione API — gia' presenti ma poco visibili in una seconda
        barra menu duplicata — diventano immediate da trovare."""
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        m_file = menubar.addMenu("&File")
        export_action = QAction("Esporta Analisi &Fondamentale (CSV)...", self)
        export_action.triggered.connect(self.fundamental._export_csv)
        m_file.addAction(export_action)
        m_file.addSeparator()
        reset_api_action = QAction("&Reimposta API Dati Esterni (FMP/Twelve Data/EODHD)...", self)
        reset_api_action.triggered.connect(self.fundamental._reset_api_key)
        m_file.addAction(reset_api_action)
        m_file.addSeparator()
        act_quit = QAction("&Esci", self)
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        m_view = menubar.addMenu("&Visualizza")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        for label, name in [("Tema &Chiaro", "light"), ("Tema &Scuro", "dark")]:
            action = QAction(label, self, checkable=True)
            action.setChecked(theme.current_theme() == name)
            action.triggered.connect(lambda _checked, n=name: self._set_theme(n))
            theme_group.addAction(action)
            m_view.addAction(action)

        m_guide = menubar.addMenu("&Guida")
        guide_tech_action = QAction("Guida &Analisi Tecnica...", self)
        guide_tech_action.triggered.connect(self.technical._show_guide)
        m_guide.addAction(guide_tech_action)
        guide_fund_action = QAction("Guida Analisi &Fondamentale...", self)
        guide_fund_action.triggered.connect(lambda: GuideDialog(self.fundamental).exec())
        m_guide.addAction(guide_fund_action)

        m_help = menubar.addMenu("&Aiuto")
        update_action = QAction("&Verifica Aggiornamenti", self)
        update_action.triggered.connect(lambda: self.fundamental._check_for_updates(silent=False))
        m_help.addAction(update_action)
        m_help.addSeparator()
        act_about = QAction("&Informazioni", self)
        act_about.triggered.connect(self._show_about)
        m_help.addAction(act_about)

    def _set_theme(self, name: str) -> None:
        """Applica il tema scelto a entrambe le viste incorporate.

        Chiama gli stessi metodi che le due viste usavano dai propri menu
        (ora nascosti): entrambi si appoggiano all'unico
        gui.theme.apply_theme() da quando i due stylesheet indipendenti
        sono stati unificati, quindi non si sovrascrivono piu' a vicenda;
        chiamarli entrambi assicura che anche gli aggiornamenti di colore
        per-widget di ciascuna vista (etichette in tinta, ridisegno del
        grafico) restino allineati al tema scelto.
        """
        self.fundamental._set_theme(name)
        self.technical._apply_theme(name)

    def _add_recent_ticker(self, ticker: str) -> None:
        """Aggiorna cronologia, suggerimenti del completer e persistenza."""
        self.recent_tickers = [ticker] + [t for t in self.recent_tickers if t != ticker]
        self.recent_tickers = self.recent_tickers[:MAX_RECENT_TICKERS]
        self.completer_model.setStringList(self.recent_tickers)
        self.settings.setValue("shared_recent_tickers", self.recent_tickers)

    def _show_about(self) -> None:
        QMessageBox.information(
            self, f"Informazioni — {APP_NAME}",
            f"<b>{APP_NAME}</b> v{VERSION}<br><br>"
            "Fusione di StockAnalyzer (analisi tecnica) e "
            "QuantumValue (analisi fondamentale).<br>"
            f"Autore: {AUTHOR} — Licenza MIT")

    def _on_analyze_both(self) -> None:
        """Smista il ticker condiviso a entrambe le viste, in parallelo.

        Ciascuna vista avvia il proprio worker in background: l'analisi OHLCV
        (tipicamente piu' rapida) popola la tab tecnica appena pronta, senza
        aspettare il fetch dei fondamentali (che ha il suo hedging multi
        provider), e viceversa.
        """
        ticker = self.shared_ticker.text().strip().upper()
        if not ticker:
            QMessageBox.warning(self, "Attenzione", "Inserire un ticker valido.")
            return
        self.settings.setValue("shared_ticker", ticker)
        self._add_recent_ticker(ticker)

        # Vista tecnica: azzera l'eventuale simbolo risolto dalla ricerca
        # precedente, altrimenti l'analisi riuserebbe il vecchio titolo.
        self.technical._resolved = None
        self.technical.ticker_input.setText(ticker)
        self.technical._on_analyze_clicked()

        # Vista fondamentale: rispetta lo switch Azioni/ETF della barra
        # condivisa (rb_azione/rb_etf, spostati li' in __init__) invece di
        # forzare sempre la modalita' Azioni; _on_search_requested() legge
        # gia' internamente quale dei due e' selezionato.
        self.fundamental.input_ticker.setText(ticker)
        self.fundamental._on_search_requested()


def main() -> None:
    """Entry point della GUI unificata (script: quantumanalyzer-gui)."""
    utils.setup_logging()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    settings = QSettings(AUTHOR.replace(" ", ""), APP_NAME.replace(" ", ""))

    # Primo avvio dopo il passaggio da QuantumValue: recupera API key dal
    # vecchio servizio keyring e preferenze dal vecchio namespace QSettings
    # (one-shot, non sovrascrive nulla di gia' configurato).
    migrate_legacy_data(settings)

    # Tema unico applicato a livello di applicazione (vedi gui/theme.py):
    # sia la vista tecnica sia quella fondamentale vi si appoggiano.
    theme.apply_theme(app, str(settings.value("theme", "light")))

    window = UnifiedMainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
