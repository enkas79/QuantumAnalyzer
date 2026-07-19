"""Test della ricerca ticker canonica (quantumanalyzer.common.search)."""

from unittest.mock import patch

import pytest
import requests

from quantumanalyzer.common.search import search_quotes


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


_GET = "quantumanalyzer.common.search.requests.get"

_PAYLOAD = {
    "quotes": [
        {"symbol": "ENI.MI", "shortname": "Eni S.p.A.", "exchange": "MIL",
         "exchDisp": "Milan", "quoteType": "EQUITY"},
        {"symbol": "SWDA.MI", "shortname": "iShares Core MSCI World",
         "exchange": "MIL", "exchDisp": "Milan", "quoteType": "ETF"},
        {"symbol": "ENIFUT", "shortname": "Eni Future", "exchange": "MIL",
         "quoteType": "FUTURE"},
        {"shortname": "senza simbolo: scartato", "quoteType": "EQUITY"},
    ]
}


def test_maps_fields_and_skips_symbolless_quotes():
    with patch(_GET, return_value=_FakeResponse(_PAYLOAD)):
        results = search_quotes("eni")

    assert [r["symbol"] for r in results] == ["ENI.MI", "SWDA.MI", "ENIFUT"]
    assert results[0]["name"] == "Eni S.p.A."
    assert results[0]["exchange"] == "MIL"
    assert results[0]["exchange_label"] == "Milan"
    assert results[0]["quote_type"] == "EQUITY"
    # senza exchDisp l'etichetta ricade sul codice borsa
    assert results[2]["exchange_label"] == "MIL"


def test_quote_types_filter():
    with patch(_GET, return_value=_FakeResponse(_PAYLOAD)):
        results = search_quotes("eni", quote_types=("ETF",))

    assert [r["symbol"] for r in results] == ["SWDA.MI"]


def test_empty_query_short_circuits_without_network():
    with patch(_GET, side_effect=AssertionError("non deve chiamare la rete")) as mock_get:
        assert search_quotes("   ") == []
    mock_get.assert_not_called()


def test_network_failure_raises_value_error(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)  # scavalca i backoff tenacity
    with patch(_GET, side_effect=requests.exceptions.ConnectionError("down")):
        with pytest.raises(ValueError):
            search_quotes("eni")
