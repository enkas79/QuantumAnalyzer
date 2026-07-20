"""
Modulo Tema (chiaro/scuro) — unico per tutta l'app (M4/restyle).

Centralizza palette, stylesheet e colori semantici dell'interfaccia. Il tema
viene applicato a livello di QApplication cosi' da coprire anche tutte le
finestre di dialogo, e non dipende mai dal tema dell'OS: senza questa
forzatura, con il sistema in modalita' scura Qt applicherebbe testo chiaro
sopra gli sfondi chiari imposti dagli stylesheet (o viceversa), rendendo il
testo illeggibile.

Fino al restyle, StockAnalyzer e QuantumValue applicavano ciascuno il
proprio stylesheet con `app.setStyleSheet(...)`, che sostituisce sempre
l'intero foglio di stile dell'applicazione: chiamarli entrambi (come
succede incorporando le due viste in un'unica finestra) faceva vincere in
modo silenzioso quale dei due veniva chiamato per ultimo. Da qui in poi
questo e' l'unico stylesheet applicato: `quantumanalyzer.gui.technical_view`
non ha piu' un proprio tema, usa questo (vedi `apply_theme` li' chiamato
da `_apply_theme`).

Autore: Enrico Martini
"""

from string import Template
from typing import Dict

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

# Colori semantici per ciascun tema. Le viste devono leggere i colori da qui
# (via color()) invece di usare valori hardcoded, cosi' il cambio tema resta
# coerente in tutta l'app.
THEMES: Dict[str, Dict[str, str]] = {
    "light": {
        "window": "#eef0f2",
        "card": "#ffffff",
        "border": "#d6d9dd",
        "text": "#24262a",
        "muted": "#54585f",
        "placeholder": "#95a5a6",
        "input_bg": "#ffffff",
        "button_bg": "#2f6fed",
        "button_text": "#ffffff",
        "button_hover": "#255ed1",
        "button_pressed": "#1d4bab",
        "button_disabled": "#aab8d6",
        "tab_bg": "#e2e4e7",
        "value": "#222f3e",
        "accent": "#2980b9",
        "accent_etf": "#8e44ad",
        "highlight": "#2f6fed",
        "alt_row": "#f4f5f7",
    },
    "dark": {
        "window": "#1e1f22",
        "card": "#26282c",
        "border": "#35373c",
        "text": "#dfe1e4",
        "muted": "#aeb4bd",
        "placeholder": "#6c7a8e",
        "input_bg": "#1e1f22",
        "button_bg": "#4c86ff",
        "button_text": "#0c0d0e",
        "button_hover": "#6b9bff",
        "button_pressed": "#3a6fe0",
        "button_disabled": "#3d4552",
        "tab_bg": "#2a2c30",
        "value": "#e8ecf2",
        "accent": "#5dade2",
        "accent_etf": "#bb8fce",
        "highlight": "#4c86ff",
        "alt_row": "#28292d",
    },
}

# Stylesheet globale unico: ogni regola che impone uno sfondo dichiara anche
# il colore del testo, cosi' nessuna combinazione puo' produrre testo
# invisibile. Copre anche i widget usati solo dalla vista tecnica
# (QComboBox, QDoubleSpinBox, QListWidget, QProgressBar, QCheckBox,
# QScrollArea/QScrollBar) cosi' che l'intera app abbia un aspetto coerente,
# non "a meta'" fra i widget della vista fondamentale (gia' temati prima del
# restyle) e quelli della vista tecnica. Il QTextBrowser (guida) resta
# sempre chiaro perche' il suo HTML usa colori scuri fissi pensati per
# sfondo bianco.
_STYLESHEET = Template("""
    QWidget { color: $text; font-size: 13px; }
    QMainWindow, QDialog { background-color: $window; }

    QGroupBox {
        font-weight: 600;
        border: 1px solid $border;
        border-radius: 10px;
        margin-top: 16px;
        padding: 14px 10px 10px 10px;
        background-color: $card;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        color: $text;
    }

    QLabel, QRadioButton, QCheckBox { background: transparent; }
    QCheckBox, QRadioButton { spacing: 6px; }

    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
        border: 1px solid $border;
        border-radius: 6px;
        padding: 5px 8px;
        background-color: $input_bg;
        color: $text;
        selection-background-color: $highlight;
        selection-color: #ffffff;
    }
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {
        border: 1px solid $accent;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QLineEdit:disabled, QComboBox:disabled { color: $placeholder; }

    QPushButton {
        font-weight: 600;
        border-radius: 6px;
        background-color: $button_bg;
        color: $button_text;
        border: none;
        padding: 7px 16px;
    }
    QPushButton:hover { background-color: $button_hover; }
    QPushButton:pressed { background-color: $button_pressed; }
    QPushButton:disabled { background-color: $button_disabled; color: $placeholder; }

    QTabWidget::pane { border: 1px solid $border; border-radius: 10px; background: $card; top: -1px; }
    QTabBar::tab {
        background: $tab_bg;
        color: $muted;
        padding: 8px 18px;
        border: 1px solid $border;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 2px;
        font-weight: 600;
    }
    QTabBar::tab:selected { background: $card; color: $accent; }
    QTabBar::tab:hover { background: $button_hover; color: $button_text; }

    QListWidget, QTableWidget {
        background-color: $card;
        color: $text;
        gridline-color: $border;
        border: 1px solid $border;
        border-radius: 6px;
        alternate-background-color: $alt_row;
    }
    QListWidget::item, QTableWidget::item { padding: 4px; }
    QHeaderView::section {
        background-color: $tab_bg;
        color: $text;
        font-weight: 600;
        border: none;
        border-bottom: 1px solid $border;
        padding: 6px;
    }

    QProgressBar {
        border: 1px solid $border;
        border-radius: 6px;
        text-align: center;
        background-color: $input_bg;
        min-height: 20px;
        color: $text;
    }
    QProgressBar::chunk { background-color: $highlight; border-radius: 5px; }

    QScrollArea { border: none; background: transparent; }
    QScrollBar:vertical { background: transparent; width: 12px; margin: 0; }
    QScrollBar::handle:vertical { background: $border; border-radius: 5px; min-height: 24px; }
    QScrollBar::handle:vertical:hover { background: $muted; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal { background: transparent; height: 12px; margin: 0; }
    QScrollBar::handle:horizontal { background: $border; border-radius: 5px; min-width: 24px; }
    QScrollBar::handle:horizontal:hover { background: $muted; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    QTextBrowser { background-color: #ffffff; color: #2c3e50; border: 1px solid $border; border-radius: 6px; }
    QMenuBar { background-color: $window; color: $text; }
    QMenuBar::item:selected { background-color: $tab_bg; border-radius: 4px; }
    QMenu { background-color: $card; color: $text; border: 1px solid $border; }
    QMenu::item:selected { background-color: $highlight; color: #ffffff; }
    QStatusBar { background-color: $window; color: $muted; border-top: 1px solid $border; }
    QMessageBox { background-color: $window; }
    QToolTip { background-color: $card; color: $text; border: 1px solid $border; }
""")

_current: str = "light"


def current_theme() -> str:
    """Restituisce il nome del tema attualmente applicato."""
    return _current


def color(key: str) -> str:
    """Restituisce il colore semantico richiesto per il tema attivo."""
    return THEMES[_current][key]


def apply_theme(app: QApplication, name: str = "light") -> None:
    """
    Applica palette e stylesheet del tema richiesto all'intera applicazione.

    Unico punto da chiamare per cambiare tema: sia la vista tecnica sia
    quella fondamentale vi si appoggiano, cosi' non esistono piu' due
    `app.setStyleSheet()` indipendenti che potrebbero sovrascriversi a
    vicenda.

    Args:
        app (QApplication): L'applicazione a cui applicare il tema.
        name (str): "light" o "dark" (valori sconosciuti ricadono su "light").
    """
    global _current
    if name not in THEMES:
        name = "light"
    _current = name
    t = THEMES[name]

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(t["window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(t["input_bg"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(t["alt_row"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["card"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["placeholder"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(t["button_bg"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(t["button_text"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor(t["accent"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(t["highlight"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(t["placeholder"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(t["placeholder"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(t["placeholder"]))
    app.setPalette(palette)
    app.setStyleSheet(_STYLESHEET.substitute(t))
