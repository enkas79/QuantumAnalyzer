"""
Importer one-shot dei dati locali delle vecchie installazioni (milestone M7).

Chi aveva QuantumValue installato ha le API key nel portachiavi di sistema
sotto il servizio "QuantumValue" e le preferenze (tema, ticker recenti) nel
namespace QSettings di QuantumValue: senza questa migrazione, al passaggio a
QuantumAnalyzer le chiavi salvate sparirebbero silenziosamente. StockAnalyzer
invece non ha bisogno di migrazione: la vista tecnica ha conservato il suo
namespace QSettings originale ("StockAnalyzer"), quindi watchlist e tema
tecnici si ritrovano da soli.

La cache SQLite legacy (~/.quantumvalue/cache/) non viene migrata di
proposito: ha una scadenza di 1 ora, e' gia' stantia al primo avvio.

Autore: Enrico Martini
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("QuantumAnalyzer")

# Identita' della vecchia installazione QuantumValue
LEGACY_KEYRING_SERVICE = "QuantumValue"
LEGACY_SETTINGS_ORG = "EnricoMartini"          # AUTHOR senza spazi
LEGACY_SETTINGS_APP = "QuantumValueAnalysis"   # APP_NAME senza spazi

# Cosa migrare
API_KEY_NAMES = ("fmp_api_key", "twelvedata_api_key", "eodhd_api_key")
SETTINGS_KEYS_TO_COPY = ("theme", "recent_tickers")

# Chiave marcatore nelle nuove impostazioni: la migrazione gira una volta sola
MARKER_KEY = "legacy_import_done"

_EMPTY_VALUES = (None, "", [])


def migrate_legacy_data(
    new_settings: Any,
    keyring_module: Optional[Any] = None,
    legacy_settings: Optional[Any] = None,
) -> Dict[str, List[str]]:
    """
    Migra API key e preferenze dalla vecchia installazione QuantumValue.

    Idempotente e best-effort: gira una volta sola (marcatore nelle nuove
    impostazioni), non sovrascrive mai valori gia' presenti nella nuova
    installazione e ignora ogni errore del portachiavi (una migrazione
    fallita non deve mai impedire l'avvio dell'app).

    Args:
        new_settings: QSettings (o compatibile) della nuova installazione.
        keyring_module: Modulo keyring iniettabile nei test; default: import
            reale (None se la libreria non c'e').
        legacy_settings: QSettings della vecchia installazione, iniettabile
            nei test; default: namespace storico di QuantumValue.

    Returns:
        Dict[str, List[str]]: cosa e' stato migrato ({'api_keys': [...],
        'settings': [...]}); vuoto se la migrazione era gia' avvenuta.
    """
    if new_settings.value(MARKER_KEY):
        return {}

    migrated: Dict[str, List[str]] = {"api_keys": [], "settings": []}

    # --- API key dal portachiavi di sistema --------------------------------
    kr = keyring_module
    if kr is None:
        try:
            import keyring as kr  # type: ignore[no-redef]
        except ImportError:
            kr = None
    if kr is not None:
        from ..fundamental.utils import _KEYRING_SERVICE
        for name in API_KEY_NAMES:
            try:
                if kr.get_password(_KEYRING_SERVICE, name):
                    continue  # gia' configurata nella nuova installazione
                old_value = kr.get_password(LEGACY_KEYRING_SERVICE, name)
                if old_value:
                    kr.set_password(_KEYRING_SERVICE, name, old_value)
                    migrated["api_keys"].append(name)
            except Exception as e:
                logger.warning(f"Migrazione API key '{name}' saltata: {e}")

    # --- Preferenze dal vecchio namespace QSettings ------------------------
    if legacy_settings is None:
        try:
            from PySide6.QtCore import QSettings
            legacy_settings = QSettings(LEGACY_SETTINGS_ORG, LEGACY_SETTINGS_APP)
        except ImportError:
            legacy_settings = None
    if legacy_settings is not None:
        for key in SETTINGS_KEYS_TO_COPY:
            try:
                if new_settings.value(key) not in _EMPTY_VALUES:
                    continue  # non sovrascrivere scelte gia' fatte
                old_value = legacy_settings.value(key)
                if old_value not in _EMPTY_VALUES:
                    new_settings.setValue(key, old_value)
                    migrated["settings"].append(key)
            except Exception as e:
                logger.warning(f"Migrazione impostazione '{key}' saltata: {e}")

    new_settings.setValue(MARKER_KEY, True)
    if migrated["api_keys"] or migrated["settings"]:
        logger.info(f"Dati legacy QuantumValue migrati: {migrated}")
    return migrated
