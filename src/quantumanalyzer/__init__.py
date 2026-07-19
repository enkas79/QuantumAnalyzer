"""
QuantumAnalyzer: fusione di StockAnalyzer (analisi tecnica/trend) e
QuantumValue (analisi fondamentale/value investing) in un'unica app.

Struttura attuale (vedi MIGRATION_PLAN.md per lo stato completo):
- `quantumanalyzer.technical`: motore di conferma del trend (EMA/RSI/volume/
  ATR), portato da StockAnalyzer.
- `quantumanalyzer.fundamental`: scoring value investing e screening dei
  multipli di mercato, portato da QuantumValue.
- `quantumanalyzer.gui`: non ancora implementata; le due GUI originali
  (PySide6 e PyQt6) devono prima essere unificate su un solo framework.
"""

from pathlib import Path

_version_file = Path(__file__).resolve().parents[2] / "version.txt"
__version__ = _version_file.read_text(encoding="utf-8").strip() if _version_file.exists() else "0.0.0"

__all__ = ["__version__"]
