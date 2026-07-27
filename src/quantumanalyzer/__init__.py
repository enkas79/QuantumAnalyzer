"""
QuantumAnalyzer: analisi tecnica e fondamentale di azioni ed ETF in un'unica
app desktop (GUI PySide6).

Struttura:
- `quantumanalyzer.technical`: motore di conferma del trend (EMA/RSI/volume/
  ATR).
- `quantumanalyzer.fundamental`: scoring value investing e screening dei
  multipli di mercato.
- `quantumanalyzer.gui`: finestra principale unificata (barra ticker
  condivisa, tab Analisi Tecnica/Fondamentale, menu e tema comuni).
"""

from pathlib import Path

_version_file = Path(__file__).resolve().parents[2] / "version.txt"
__version__ = _version_file.read_text(encoding="utf-8").strip() if _version_file.exists() else "0.0.0"

__all__ = ["__version__"]
