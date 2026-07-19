# QuantumAnalyzer

Fusione di [StockAnalyzer](https://github.com/enkas79/StockAnalyzer) (motore di
trend-confirmation tecnico) e [QuantumValue](https://github.com/enkas79/QuantumValue)
(scoring value investing e screening dei multipli di mercato) in un'unica
base di codice Python.

**Stato attuale: scaffold + logica "core" portata, GUI non ancora unificata.**
Vedi [MIGRATION_PLAN.md](MIGRATION_PLAN.md) per il piano dettagliato dei passi
restanti e per il ragionamento dietro le scelte architetturali.

## Perche' questa fusione

I due programmi originali analizzano lo stesso oggetto (un titolo azionario)
da due angolazioni complementari e non sovrapposte:

- **StockAnalyzer** risponde a "il trend attuale e' affidabile?" — EMA
  50/200, RSI(14), volume relativo, ATR per il rischio, MACD/Bollinger
  opzionali. Nessun dato fondamentale.
- **QuantumValue** risponde a "il prezzo attuale e' giustificato dai
  fondamentali?" — Earnings Yield, ROIC, EV/EBITDA (qualita'/convenienza in
  stile Magic Formula di Greenblatt), P/E, P/S, PEG (multipli di mercato), piu'
  screening ETF (TER, AUM, rendimenti). Include anche 4 "campanelli d'allarme"
  di valutazione: P/E molto oltre la propria media storica, P/S oltre i limiti
  tipici di un'azienda matura, margine EBIT in contrazione mentre il prezzo
  sale, Free Cash Flow negativo su piu' periodi consecutivi.

Nessuno dei due dice nulla su cio' che copre l'altro: un titolo puo' avere un
trend tecnico solidissimo e fondamentali pessimi, o viceversa. Un'unica app
con entrambe le viste affiancate sullo stesso ticker e' più utile di due
programmi separati che vanno aperti e incrociati a mano.

## Struttura del repository

```
src/quantumanalyzer/
    technical/       # Portato da StockAnalyzer: engine.py, indicators.py,
                      # data.py, risk.py, backtest.py, cli.py, updater.py.
                      # Import gia' relativi nel pacchetto originale: nessuna
                      # modifica alla logica, solo lo spostamento di cartella.
    fundamental/      # Portato da QuantumValue: models.py, config.py,
                      # cache.py, utils.py (la sola parte non-GUI di src/).
                      # Import adattati da stile "flat + sys.path hack" a
                      # import relativi di pacchetto (`from . import config`).
    gui/              # Placeholder. Le due GUI originali sono su framework
                      # Qt diversi (PySide6 vs PyQt6) e vanno prima unificate:
                      # vedi MIGRATION_PLAN.md.
tests/
    technical/        # Portati da StockAnalyzer (esclusi i test della GUI)
    fundamental/       # Portati da QuantumValue (esclusi i test di GUI/controller)
```

Entrambi i pacchetti (`technical` e `fundamental`) sono indipendenti fra loro
e completamente funzionanti: non condividono ancora codice (stessa logica di
retry HTTP, stesso pattern di controllo aggiornamenti GitHub, ecc. sono
duplicati fra i due — vedi il piano di migrazione per la roadmap di
deduplicazione).

## Installazione e uso (solo libreria, no GUI)

```bash
git clone https://github.com/enkas79/QuantumAnalyzer.git
cd QuantumAnalyzer
pip install -e ".[dev]"
pytest
```

```python
# Analisi tecnica (trend confirmation)
from quantumanalyzer.technical import fetch_ohlcv, analyze

df = fetch_ohlcv("AAPL", period="1y", interval="1d")
result = analyze(df)
print(result.direction, result.score)

# Analisi fondamentale (value investing + campanelli d'allarme)
from quantumanalyzer.fundamental.models import FinancialDataFetcher, evaluate_core, evaluate_red_flags

fetcher = FinancialDataFetcher()
data = fetcher.fetch_data("AAPL")
triggered, verdict, color, details = evaluate_red_flags(
    data.pe, data.pe_history, data.ps,
    data.ebit_margin_history, data.price_change_hist_pct, data.fcf_history
)
print(verdict)
```

Non esiste ancora un entry point GUI unificato (`quantumanalyzer-gui`): per
usare le interfacce grafiche originali, i due repository sorgente restano
disponibili e pienamente funzionanti nel frattempo.

## Licenza

MIT, come entrambi i progetti originali.
