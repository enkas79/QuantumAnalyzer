"""L'adapter best-effort sopra il checker canonico (common.updater):
UpdateInfo su release piu' nuova, None in ogni altro caso, mai eccezioni."""

from unittest.mock import patch

from quantumanalyzer.technical.updater import UpdateInfo, check_for_update

_IMPL = "quantumanalyzer.technical.updater._check_for_updates_impl"


def test_check_for_update_returns_none_when_already_latest():
    with patch(_IMPL, return_value=(False, "0.2.0", "")):
        assert check_for_update("0.2.0") is None


def test_check_for_update_returns_info_when_newer_release_exists():
    with patch(_IMPL, return_value=(True, "0.3.0", "https://example.invalid/releases/v0.3.0")):
        result = check_for_update("0.2.0")

    assert result == UpdateInfo(version="0.3.0", url="https://example.invalid/releases/v0.3.0")


def test_check_for_update_returns_none_when_current_is_newer():
    with patch(_IMPL, return_value=(False, "0.1.0", "https://example.invalid/releases/v0.1.0")):
        assert check_for_update("0.2.0") is None


def test_check_for_update_returns_none_on_network_failure():
    # Il checker canonico solleva ValueError dopo i retry: l'adapter la assorbe
    with patch(_IMPL, side_effect=ValueError("no network")):
        assert check_for_update("0.2.0") is None


def test_check_for_update_returns_none_when_update_has_no_url():
    with patch(_IMPL, return_value=(True, "0.3.0", "")):
        assert check_for_update("0.2.0") is None
