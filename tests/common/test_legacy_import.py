"""Test dell'importer one-shot dei dati legacy QuantumValue (M7).

Keyring e QSettings sono iniettati come fake: nessuna dipendenza da
portachiavi di sistema o da PySide6.
"""

import pytest

from quantumanalyzer.common.legacy_import import MARKER_KEY, migrate_legacy_data


class FakeSettings:
    def __init__(self, store=None):
        self.store = dict(store or {})

    def value(self, key, default=None):
        return self.store.get(key, default)

    def setValue(self, key, value):
        self.store[key] = value


class FakeKeyring:
    def __init__(self, passwords=None):
        # {(service, name): password}
        self.passwords = dict(passwords or {})

    def get_password(self, service, name):
        return self.passwords.get((service, name))

    def set_password(self, service, name, password):
        self.passwords[(service, name)] = password


def test_migrates_api_keys_from_legacy_service():
    kr = FakeKeyring({("QuantumValue", "fmp_api_key"): "vecchia-fmp",
                      ("QuantumValue", "eodhd_api_key"): "vecchia-eodhd"})
    new = FakeSettings()

    result = migrate_legacy_data(new, keyring_module=kr, legacy_settings=FakeSettings())

    assert sorted(result["api_keys"]) == ["eodhd_api_key", "fmp_api_key"]
    assert kr.get_password("QuantumAnalyzer", "fmp_api_key") == "vecchia-fmp"
    assert kr.get_password("QuantumAnalyzer", "eodhd_api_key") == "vecchia-eodhd"
    assert new.value(MARKER_KEY) is True


def test_does_not_overwrite_existing_new_api_key():
    kr = FakeKeyring({("QuantumValue", "fmp_api_key"): "vecchia",
                      ("QuantumAnalyzer", "fmp_api_key"): "nuova"})

    result = migrate_legacy_data(FakeSettings(), keyring_module=kr,
                                 legacy_settings=FakeSettings())

    assert result["api_keys"] == []
    assert kr.get_password("QuantumAnalyzer", "fmp_api_key") == "nuova"


def test_migrates_settings_without_overwriting():
    legacy = FakeSettings({"theme": "dark", "recent_tickers": ["AAPL", "ENI.MI"]})
    new = FakeSettings({"theme": "light"})  # scelta gia' fatta: non toccarla

    result = migrate_legacy_data(new, keyring_module=FakeKeyring(), legacy_settings=legacy)

    assert result["settings"] == ["recent_tickers"]
    assert new.value("theme") == "light"
    assert new.value("recent_tickers") == ["AAPL", "ENI.MI"]


def test_runs_only_once():
    kr = FakeKeyring({("QuantumValue", "fmp_api_key"): "vecchia"})
    new = FakeSettings({MARKER_KEY: True})

    result = migrate_legacy_data(new, keyring_module=kr, legacy_settings=FakeSettings())

    assert result == {}
    assert kr.get_password("QuantumAnalyzer", "fmp_api_key") is None


def test_keyring_errors_do_not_block_migration():
    class BrokenKeyring:
        def get_password(self, service, name):
            raise RuntimeError("portachiavi rotto")

        def set_password(self, service, name, password):
            raise RuntimeError("portachiavi rotto")

    legacy = FakeSettings({"theme": "dark"})
    new = FakeSettings()

    result = migrate_legacy_data(new, keyring_module=BrokenKeyring(), legacy_settings=legacy)

    assert result["api_keys"] == []
    assert result["settings"] == ["theme"]
    assert new.value(MARKER_KEY) is True


def test_without_keyring_module_still_migrates_settings(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "keyring", None)  # import keyring -> fallisce

    legacy = FakeSettings({"recent_tickers": ["MSFT"]})
    new = FakeSettings()

    result = migrate_legacy_data(new, legacy_settings=legacy)

    assert result["settings"] == ["recent_tickers"]
