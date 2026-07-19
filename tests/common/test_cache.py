"""Test dell'implementazione cache condivisa (quantumanalyzer.common.cache)."""

from quantumanalyzer.common.cache import JsonCache


def _make(tmp_path, ttl=3600):
    return JsonCache(str(tmp_path / "cache.db"), ttl_seconds=ttl)


def test_set_get_roundtrip(tmp_path):
    cache = _make(tmp_path)
    payload = {"ticker": "AAPL", "prices": {"current": 180.0}, "history": [1, 2, 3]}
    assert cache.set("k", payload) is True
    assert cache.get("k") == payload
    cache.close()


def test_get_missing_key_returns_none(tmp_path):
    cache = _make(tmp_path)
    assert cache.get("inesistente") is None
    cache.close()


def test_expired_entry_returns_none_and_is_removed(tmp_path):
    cache = _make(tmp_path, ttl=3600)
    cache.set("k", {"v": 1})
    assert cache.backdate("k", 3601) is True
    assert cache.get("k") is None          # scaduta
    cache.ttl_seconds = 10 ** 9
    assert cache.get("k") is None          # rimossa fisicamente, non solo filtrata
    cache.close()


def test_backdate_missing_key_returns_false(tmp_path):
    cache = _make(tmp_path)
    assert cache.backdate("inesistente", 10) is False
    cache.close()


def test_clear_and_stats(tmp_path):
    cache = _make(tmp_path)
    cache.set("a", {"v": 1})
    cache.set("b", {"v": 2})
    cache.backdate("b", cache.ttl_seconds + 1)
    stats = cache.stats()
    assert stats["total"] == 2
    assert stats["expired"] == 1
    assert stats["valid"] == 1
    assert cache.clear() is True
    assert cache.stats()["total"] == 0
    cache.close()


def test_separate_instances_are_isolated(tmp_path):
    a = JsonCache(str(tmp_path / "a.db"), ttl_seconds=60)
    b = JsonCache(str(tmp_path / "b.db"), ttl_seconds=60)
    a.set("k", {"da": "a"})
    assert b.get("k") is None
    a.close()
    b.close()
