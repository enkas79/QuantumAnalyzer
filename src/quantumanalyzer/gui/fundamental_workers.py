"""
Worker QThread dell'analisi fondamentale (portati da QuantumValue).

Gestiscono tutti i task asincroni interfacciando le funzioni pure di
quantumanalyzer.fundamental.models con la View (GUI).

Autore: Enrico Martini
Versione: portato da QuantumValue 0.7.14 in QuantumAnalyzer (PyQt6 -> PySide6)
"""

import asyncio
from typing import Optional, List, Tuple
from PySide6.QtCore import QThread, Signal, QObject

from ..fundamental import models


class UpdateCheckWorker(QThread):
    """Worker in background per la verifica degli aggiornamenti su GitHub."""
    finished = Signal(bool, str, str)
    error = Signal(str)

    def __init__(self, current_version: str, repo: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.current_version: str = current_version
        self.repo: str = repo

    def run(self) -> None:
        """Esegue il polling asincrono su GitHub via funzioni di modulo."""
        try:
            update_avail, new_ver, url = models.check_for_updates(self.current_version, self.repo)
            self.finished.emit(update_avail, new_ver, url)
        except ValueError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Errore fatale controllo aggiornamenti: {str(e)}")


class SearchWorker(QThread):
    """Worker in background per la ricerca testuale dei Ticker (per nome, ISIN o simbolo)."""
    finished = Signal(object, str)
    error = Signal(str)

    def __init__(
        self,
        query: str,
        quote_types: Tuple[str, ...] = ('EQUITY', 'ETF'),
        parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self.query: str = query
        self.quote_types: Tuple[str, ...] = quote_types

    def run(self) -> None:
        """Esegue la ricerca testuale di aziende ed ETF via funzioni di modulo."""
        try:
            results: List[Tuple[str, str, str]] = models.search_by_name(self.query, self.quote_types)
            self.finished.emit(results, self.query)
        except Exception as e:
            self.error.emit(str(e))


class FetchWorker(QThread):
    """Worker in background per il download dei fondamentali contabili (Azioni)."""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fetcher: models.FinancialDataFetcher, ticker: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.fetcher: models.FinancialDataFetcher = fetcher
        self.ticker: str = ticker

    def run(self) -> None:
        # Crea un loop asincrono temporaneo per proteggere yfinance su Windows
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data: models.StockData = self.fetcher.fetch_data(self.ticker)
            self.finished.emit(data)
        except ValueError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Errore imprevisto durante il download: {str(e)}")
        finally:
            # Assicura la chiusura del loop per prevenire Segfault
            loop.close()


class EtfFetchWorker(QThread):
    """Worker in background per il download e screening dei fondi passivi (ETF)."""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, query: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.query: str = query

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data: models.EtfData = models.fetch_etf_data(self.query)
            self.finished.emit(data)
        except ValueError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Errore imprevisto ETF: {str(e)}")
        finally:
            loop.close()
