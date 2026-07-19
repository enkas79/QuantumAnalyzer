"""
GUI unificata di QuantumAnalyzer (PySide6).

Moduli:
- `app`: finestra principale unificata (barra ticker condivisa + tab) ed
  entry point `quantumanalyzer-gui`.
- `technical_view` / `technical_workers`: analisi tecnica (da StockAnalyzer,
  gia' PySide6 in origine).
- `fundamental_view` / `fundamental_workers`: analisi fondamentale/ETF
  (da QuantumValue, portata da PyQt6 a PySide6).
- `theme`: palette e stylesheet chiaro/scuro applicati a livello applicazione.
"""
