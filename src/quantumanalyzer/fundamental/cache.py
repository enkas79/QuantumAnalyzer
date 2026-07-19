"""
Modulo Cache (fondamentali).

Gestisce il caching locale dei dati finanziari per ridurre le chiamate HTTP
ai provider esterni (Yahoo Finance, FMP). Dal M5 l'implementazione vive in
quantumanalyzer.common.cache.JsonCache (condivisa con la cache OHLCV
dell'analisi tecnica); questo modulo conserva l'API storica di QuantumValue
(funzioni di modulo, scadenza in ore da config).

Autore: Enrico Martini
Versione: portato da QuantumValue 0.7.14 in QuantumAnalyzer
"""

from typing import Any, Dict, Optional

from ..common.cache import JsonCache
from .config import CACHE_DB_PATH, CACHE_EXPIRY_HOURS  # noqa: F401 - riesposti e monkeypatchabili nei test

_cache: Optional[JsonCache] = None


def _get_cache() -> JsonCache:
    """Istanza condivisa, ricreata se il percorso db cambia (test) e con il
    TTL riletto ad ogni chiamata cosi' resta pilotabile via modulo."""
    global _cache
    if _cache is None or _cache.db_path != CACHE_DB_PATH:
        if _cache is not None:
            _cache.close()
        _cache = JsonCache(CACHE_DB_PATH, CACHE_EXPIRY_HOURS * 3600)
    _cache.ttl_seconds = CACHE_EXPIRY_HOURS * 3600
    return _cache


def get_cached(key: str) -> Optional[Dict[str, Any]]:
    """Recupera un valore dalla cache se non e' scaduto."""
    return _get_cache().get(key)


def set_cached(key: str, value: Dict[str, Any]) -> bool:
    """Salva un valore nella cache; True se riuscito."""
    return _get_cache().set(key, value)


def clear_cache() -> bool:
    """Svuota completamente la cache; True se riuscito."""
    return _get_cache().clear()


def get_cache_stats() -> Dict[str, int]:
    """Statistiche sulla cache (totale, scaduti, validi)."""
    return _get_cache().stats()
