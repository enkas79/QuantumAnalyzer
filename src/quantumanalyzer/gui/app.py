"""
Finestra principale unificata di QuantumAnalyzer (milestone M4).

Un'unica finestra con un campo ticker condiviso e due tab che ospitano le
finestre esistenti: "Analisi Tecnica" (portata da StockAnalyzer) e "Analisi
Fondamentale" (portata da QuantumValue). Il campo condiviso smista il ticker
a entrambe le viste, che avviano i rispettivi fetch in parallelo sui propri
worker QThread: nessuna delle due analisi blocca l'altra.

Prima iterazione volutamente "sottile" (vedi MIGRATION_PLAN.md, M4): le due
viste embedded conservano i propri menu (tema, export CSV, API key, leg
opzionali, guida) e le proprie impostazioni QSettings. La deduplicazione dei
servizi condivisi (controllo aggiornamenti, ricerca ticker) e' il passo M5.

Autore: Enrico Martini
"""

import sys
from typing import Optional

from PySide6.QtCore import QSettings, QStringListModel, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QCompleter, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget
)

from ..common.legacy_import import migrate_legacy_data
from ..fundamental import utils
from ..fundamental.config import APP_NAME, AUTHOR, VERSION
from . import theme
from .fundamental_view import MAX_RECENT_TICKERS
from .fundamental_view import MainWindow as FundamentalWindow
from .technical_view import MainWindow as TechnicalWindow


class UnifiedMainWindow(QMainWindow):
    """Contenitore delle due analisi con barra ticker condivisa."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.settings = QSettings(AUTHOR.replace(" ", ""), APP_NAME.replace(" ", ""))

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

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

        self.btn_analyze_both = QPushButton("Analizza (Tecnica + Fondamentale)")
        self.btn_analyze_both.clicked.connect(self._on_analyze_both)
        bar.addWidget(self.btn_analyze_both)
        bar.addStretch()
        layout.addLayout(bar)

        # --- Tab con le due viste embedded ----------------------------------
        # QMainWindow e' un QWidget: le due finestre originali vengono ospitate
        # cosi' come sono, conservando menu interni e status bar. I menubar
        # nativi (macOS) vanno disattivati, altrimenti le finestre embedded si
        # contenderebbero la barra di sistema.
        self.technical = TechnicalWindow()
        self.technical.menuBar().setNativeMenuBar(False)
        self.fundamental = FundamentalWindow()
        self.fundamental.menuBar().setNativeMenuBar(False)

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
        # anche i suoi ~60px di margine verticale, scarso in questa
        # finestra (barra ticker + doppio menu + doppia barra tab).
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
        """Menu minimale: le funzioni specifiche restano nei menu delle tab."""
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        m_file = menubar.addMenu("&File")
        act_quit = QAction("Esci", self)
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        m_help = menubar.addMenu("&Aiuto")
        act_about = QAction("Informazioni", self)
        act_about.triggered.connect(self._show_about)
        m_help.addAction(act_about)

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

        # Vista fondamentale: il ticker condiviso e' un'azione (per gli ETF
        # resta il flusso dedicato dentro la tab fondamentale).
        self.fundamental.rb_azione.setChecked(True)
        self.fundamental.input_ticker.setText(ticker)
        self.fundamental._on_search_requested()


def main() -> None:
    """Entry point della GUI unificata (script: quantumanalyzer-gui)."""
    utils.setup_logging()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Tema applicato a livello di applicazione (comportamento QuantumValue);
    # la tab tecnica gestisce il proprio tema con lo stylesheet di finestra,
    # che dentro il suo sottoalbero ha precedenza su quello di applicazione.
    settings = QSettings(AUTHOR.replace(" ", ""), APP_NAME.replace(" ", ""))

    # Primo avvio dopo il passaggio da QuantumValue: recupera API key dal
    # vecchio servizio keyring e preferenze dal vecchio namespace QSettings
    # (one-shot, non sovrascrive nulla di gia' configurato).
    migrate_legacy_data(settings)

    theme.apply_theme(app, str(settings.value("theme", "light")))

    window = UnifiedMainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
