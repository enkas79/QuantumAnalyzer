# QuantumAnalyzer

Fusione di [StockAnalyzer](https://github.com/enkas79/StockAnalyzer) (motore di
trend-confirmation tecnico) e [QuantumValue](https://github.com/enkas79/QuantumValue)
(scoring value investing e screening dei multipli di mercato) in un'unica
base di codice Python.

**Stato attuale: app completa (GUI PySide6 unificata, CI, pipeline
installer).** La finestra principale ha una barra ticker condivisa (con
cronologia suggerita) e due tab — Analisi Tecnica e Analisi Fondamentale —
che analizzano lo stesso titolo in parallelo. Un unico menu (File /
Visualizza / Guida / Aiuto) e un unico tema chiaro/scuro coprono entrambe le
viste — guide, configurazione API esterne (FMP/Twelve Data/EODHD) e verifica
aggiornamenti sono tutte raggiungibili da li', senza menu duplicati. I
servizi comuni (controllo aggiornamenti, ricerca ticker, cache) sono
unificati in `quantumanalyzer.common`. Un push che modifica `version.txt` su
`main` costruisce gli installer (.exe/.dmg/.deb) e pubblica la release. Vedi
[MIGRATION_PLAN.md](MIGRATION_PLAN.md) per la storia della migrazione e il
restyle post-M4.

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
    technical/        # Da StockAnalyzer: engine, indicators, data, risk,
                      # backtest, cli, updater (adapter sul checker comune).
    fundamental/      # Da QuantumValue: models (scoring value + campanelli
                      # d'allarme), config, cache, utils.
    common/           # Servizi condivisi: controllo aggiornamenti GitHub
                      # (updater.py), ricerca ticker (search.py), cache
                      # SQLite a TTL (cache.py), importer dati legacy
                      # (legacy_import.py).
    gui/              # GUI unificata PySide6: app.py (finestra principale +
                      # entry point), technical_view/_workers (da
                      # StockAnalyzer), fundamental_view/_workers (da
                      # QuantumValue, portata PyQt6 -> PySide6), theme.py.
tests/
    technical/  fundamental/  common/  gui/
```

## Installazione e uso

```bash
git clone https://github.com/enkas79/QuantumAnalyzer.git
cd QuantumAnalyzer
pip install -e ".[dev,gui]"
pytest                      # suite completa (i test GUI girano offscreen)
quantumanalyzer-gui         # app completa (tecnica + fondamentale)
quantumanalyzer-cli AAPL    # sola analisi tecnica da terminale
```

Al primo avvio, la GUI recupera automaticamente le API key e le preferenze di
un'eventuale installazione precedente di QuantumValue (migrazione one-shot,
senza sovrascrivere nulla di gia' configurato).

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

## Licenza

MIT, come entrambi i progetti originali.
