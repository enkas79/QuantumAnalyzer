"""Startup update check against GitHub Releases.

Deliberately does not download or replace anything on its own: replacing an
installed binary automatically is platform-specific and risky, so this only
tells the caller a newer version exists and where to get it.

Since M5 this is a thin adapter over the canonical checker in
quantumanalyzer.common.updater (requests + tenacity retry + per-platform
asset pick), keeping StockAnalyzer's historical best-effort API:
UpdateInfo on a newer release, None on anything else, never raising.
It also now points at the unified QuantumAnalyzer repo instead of the old
StockAnalyzer one.
"""

from dataclasses import dataclass

from ..common.updater import check_for_updates as _check_for_updates_impl
from ..fundamental.config import GITHUB_REPO


@dataclass
class UpdateInfo:
    version: str
    url: str


def check_for_update(current_version: str, timeout: float = 5.0) -> UpdateInfo | None:
    """Return the latest GitHub release if it's newer than `current_version`.

    Best-effort: any failure (offline, rate-limited, no releases yet, ...)
    returns None instead of raising, so a broken check never blocks or
    crashes startup.
    """
    try:
        available, tag, url = _check_for_updates_impl(
            current_version, GITHUB_REPO, timeout=int(timeout)
        )
    except Exception:
        return None

    if available and url:
        return UpdateInfo(version=tag.lstrip("vV"), url=url)
    return None
