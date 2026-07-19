"""L'adapter best-effort sopra la ricerca canonica (common.search):
lista di dict su successo, lista vuota su qualsiasi errore, mai eccezioni."""

from unittest.mock import patch

from quantumanalyzer.technical.data import resolve_ticker, search_candidates

_SEARCH = "quantumanalyzer.technical.data.search_quotes"


def _quote(symbol, name, exchange_label="", exchange=""):
    return {"symbol": symbol, "name": name, "exchange": exchange,
            "exchange_label": exchange_label, "quote_type": "EQUITY"}


def test_search_candidates_maps_canonical_results():
    results = [
        _quote("ENI.MI", "Eni S.p.A.", exchange_label="Milan", exchange="MIL"),
        _quote("E", "Eni SpA", exchange_label="NYSE", exchange="NYQ"),
    ]
    with patch(_SEARCH, return_value=results):
        candidates = search_candidates("eni")

    assert candidates == [
        {"symbol": "ENI.MI", "name": "Eni S.p.A.", "exchange": "Milan"},
        {"symbol": "E", "name": "Eni SpA", "exchange": "NYSE"},
    ]


def test_search_candidates_falls_back_to_exchange_code_without_label():
    with patch(_SEARCH, return_value=[_quote("AAPL", "Apple", exchange="NMS")]):
        assert search_candidates("apple")[0]["exchange"] == "NMS"


def test_search_candidates_returns_empty_list_on_no_query():
    # La ricerca canonica restituisce [] senza chiamare la rete
    assert search_candidates("   ") == []


def test_search_candidates_returns_empty_list_on_network_failure():
    # La ricerca canonica solleva ValueError dopo i retry: l'adapter la assorbe
    with patch(_SEARCH, side_effect=ValueError("boom")):
        assert search_candidates("eni") == []


def test_resolve_ticker_picks_best_match_from_search():
    with patch(_SEARCH, return_value=[_quote("ENI.MI", "Eni S.p.A.", "Milan")]):
        symbol, name = resolve_ticker("eni")

    assert symbol == "ENI.MI"
    assert name == "Eni S.p.A."


def test_resolve_ticker_falls_back_to_uppercased_query_when_no_match():
    with patch(_SEARCH, return_value=[]):
        symbol, name = resolve_ticker("madeupticker")

    assert symbol == "MADEUPTICKER"
    assert name == "MADEUPTICKER"
