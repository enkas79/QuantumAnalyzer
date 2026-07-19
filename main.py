"""
Launcher di QuantumAnalyzer per esecuzione da sorgente e build PyInstaller.

Da sorgente: `python main.py` (equivalente allo script `quantumanalyzer-gui`).
Le build degli installer (vedi .github/workflows/build-installers.yml)
puntano PyInstaller a questo file.
"""

import os
import sys

# Esecuzione da checkout senza installazione: rende importabile src/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from quantumanalyzer.gui.app import main

if __name__ == "__main__":
    main()
