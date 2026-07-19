"""Test del checker aggiornamenti canonico (quantumanalyzer.common.updater)."""

from unittest.mock import patch

import pytest
import requests

from quantumanalyzer.common.updater import check_for_updates, parse_version


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


_GET = "quantumanalyzer.common.updater.requests.get"


@pytest.mark.parametrize("raw, expected", [
    ("1.2.3", (1, 2, 3)),
    ("v1.2.3", (1, 2, 3)),
    ("V0.10.0", (0, 10, 0)),
    ("1.2.3rc1", (1, 2, 31)),  # cifre estratte dal segmento non numerico
    ("garbage", (0,)),
])
def test_parse_version(raw, expected):
    assert parse_version(raw) == expected


def test_update_available_prefers_platform_asset():
    payload = {
        "tag_name": "v9.9.9",
        "html_url": "https://example.invalid/releases/v9.9.9",
        "assets": [
            {"name": "App_v9.9.9_amd64.deb", "browser_download_url": "https://example.invalid/app.deb"},
        ],
    }
    with patch(_GET, return_value=_FakeResponse(payload)):
        available, tag, url = check_for_updates("0.1.0", "enkas79/QuantumAnalyzer")
    assert available is True
    assert tag == "9.9.9"
    # su linux (piattaforma dei test) vince l'asset .deb sul link HTML
    assert url == "https://example.invalid/app.deb"


def test_update_available_falls_back_to_html_url_without_matching_asset():
    payload = {"tag_name": "v9.9.9", "html_url": "https://example.invalid/rel", "assets": []}
    with patch(_GET, return_value=_FakeResponse(payload)):
        available, _tag, url = check_for_updates("0.1.0", "enkas79/QuantumAnalyzer")
    assert available is True
    assert url == "https://example.invalid/rel"


def test_no_release_yet_404_means_no_update():
    with patch(_GET, return_value=_FakeResponse({}, status_code=404)):
        available, tag, url = check_for_updates("0.1.0", "enkas79/QuantumAnalyzer")
    assert (available, tag, url) == (False, "0.1.0", "")


def test_same_version_means_no_update():
    payload = {"tag_name": "v0.1.0", "html_url": "https://example.invalid/rel", "assets": []}
    with patch(_GET, return_value=_FakeResponse(payload)):
        available, _tag, _url = check_for_updates("0.1.0", "enkas79/QuantumAnalyzer")
    assert available is False


def test_pick_release_asset_darwin_accepts_dmg_and_legacy_zip():
    from quantumanalyzer.common.updater import pick_release_asset

    dmg_assets = [{"name": "QuantumAnalyzer-0.1.0.dmg", "browser_download_url": "https://example.invalid/qa.dmg"}]
    assert pick_release_asset(dmg_assets, platform="darwin") == "https://example.invalid/qa.dmg"

    legacy_assets = [{"name": "QuantumValue_v0.7_macOS.zip", "browser_download_url": "https://example.invalid/qv.zip"}]
    assert pick_release_asset(legacy_assets, platform="darwin") == "https://example.invalid/qv.zip"

    # il .dmg (formato della pipeline unificata) ha priorita' sul legacy zip
    both = legacy_assets + dmg_assets
    assert pick_release_asset(both, platform="darwin") == "https://example.invalid/qa.dmg"


def test_network_failure_raises_value_error(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)  # scavalca i backoff tenacity
    with patch(_GET, side_effect=requests.exceptions.ConnectionError("down")):
        with pytest.raises(ValueError):
            check_for_updates("0.1.0", "enkas79/QuantumAnalyzer")
