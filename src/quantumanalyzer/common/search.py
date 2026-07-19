"""
Ricerca ticker/nome su Yahoo Finance — implementazione canonica (M5).

Unifica le due ricerche che i progetti originali facevano per conto proprio:
StockAnalyzer via `yf.Search` (best-effort, mai eccezioni), QuantumValue via
endpoint HTTP diretto (requests + retry tenacity, filtro sul tipo di
strumento). La base e' quella HTTP diretta: piu' controllo su timeout/retry e
nessuna dipendenza dal wrapper yfinance per una semplice GET. Gli adapter nei
moduli storici conservano le rispettive API (lista di dict senza eccezioni da
una parte, lista di tuple con etichette borsa dall'altra).

Autore: Enrico Martini
"""

from typing import Dict, List, Optional, Tuple

import requests

# Stesso decoratore di retry e stessi default HTTP del checker aggiornamenti:
# helper condivisi del pacchetto common.
from .updater import _default_headers, _default_timeout, _retry_request

SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"


@_retry_request
def search_quotes(
    query: str,
    quote_types: Optional[Tuple[str, ...]] = None,
    max_results: int = 10,
    timeout: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, str]]:
    """
    Cerca strumenti per ticker, nome o ISIN sull'endpoint pubblico di Yahoo.

    Args:
        query: Testo da cercare.
        quote_types: Se indicato, tiene solo questi tipi (es. ('EQUITY','ETF')).
        max_results: Numero massimo di risultati richiesti.
        timeout: Timeout HTTP in secondi (default: config dell'app).
        headers: Header HTTP (default: config dell'app).

    Returns:
        List[Dict[str, str]]: Per ogni risultato: 'symbol', 'name',
        'exchange' (codice, es. 'MIL'), 'exchange_label' (nome leggibile
        fornito da Yahoo, es. 'Milan'), 'quote_type'.

    Raises:
        ValueError: Su errore di rete (dopo i retry).
    """
    cleaned = query.strip()
    if not cleaned:
        return []

    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": cleaned, "quotesCount": max_results},
            headers=headers if headers is not None else _default_headers(),
            timeout=timeout if timeout is not None else _default_timeout(),
        )
        response.raise_for_status()
        data: dict = response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Errore di rete durante la ricerca: {str(e)}")

    results: List[Dict[str, str]] = []
    for quote in data.get('quotes', []):
        if quote_types is not None and quote.get('quoteType') not in quote_types:
            continue
        symbol = str(quote.get('symbol', '')).replace(" ", "")
        if not symbol:
            continue
        name = quote.get('shortname') or quote.get('longname') or symbol
        exchange = quote.get('exchange', '') or ''
        exchange_label = quote.get('exchDisp', '') or exchange
        results.append({
            'symbol': symbol,
            'name': str(name),
            'exchange': str(exchange),
            'exchange_label': str(exchange_label),
            'quote_type': str(quote.get('quoteType', '')),
        })
    return results
