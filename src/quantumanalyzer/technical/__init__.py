import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

from .data import fetch_ohlcv, resolve_ticker
from .engine import AnalysisResult, Leg, analyze


def _read_version() -> str:
    try:
        return _pkg_version("quantumanalyzer")
    except PackageNotFoundError:
        pass

    # PyInstaller builds run frozen, without the installed dist-info metadata
    # importlib.metadata needs; version.txt is bundled alongside the
    # executable as a fallback. The build/packaging pipeline for the merged
    # app is not set up yet (see MIGRATION_PLAN.md), so in source checkouts
    # this falls through to the repo-root version.txt three levels up
    # (technical/ -> quantumanalyzer/ -> src/ -> repo root).
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    version_file = base_dir / "version.txt"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()

    return "0.0.0"


__version__ = _read_version()

__all__ = ["fetch_ohlcv", "resolve_ticker", "analyze", "AnalysisResult", "Leg", "__version__"]
