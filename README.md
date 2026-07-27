# QuantumAnalyzer

App desktop (Python + PySide6) per analizzare un titolo azionario o un ETF da
due angolazioni complementari nella stessa finestra: **trend tecnico** e
**convenienza fondamentale**. Un'unica barra ticker condivisa avvia entrambe
le analisi in parallelo, senza dover aprire due programmi diversi e
incrociare i risultati a mano.

## Cosa fa

Una sola finestra con barra ticker condivisa (cronologia suggerita mentre si
digita, maiuscolo automatico) e due tab principali:

- **Analisi Tecnica (Trend)** — risponde a "il trend attuale e' affidabile?":
  EMA 50/200, RSI(14), volume relativo, ATR per il rischio, MACD/Bollinger
  opzionali, grafico prezzo, watchlist persistente e backtest.
- **Analisi Fondamentale (Value)** — risponde a "il prezzo e' giustificato
  dai fondamentali?", su tre sotto-tab:
  - *Analisi Strutturale Value*: Earnings Yield, ROIC, EV/EBITDA (qualita' e
    convenienza in stile Magic Formula di Greenblatt).
  - *Occasioni in Borsa*: P/E, P/S, PEG e 4 "campanelli d'allarme" di
    valutazione (P/E oltre la media storica, P/S fuori dai limiti tipici,
    margine EBIT in contrazione, Free Cash Flow negativo su piu' periodi).
  - *Valutazione ETF*: TER, AUM e rendimenti per lo screening di fondi
    passivi.

Nessuna delle due viste dice nulla su cio' che copre l'altra: un titolo puo'
avere un trend tecnico solido e fondamentali deboli, o viceversa — vederle
affiancate sullo stesso ticker aiuta a non guardare solo meta' del quadro.

Un unico menu (File / Visualizza / Guida / Aiuto) e un unico tema
chiaro/scuro coprono entrambe le viste: guida all'uso, configurazione delle
API dati esterne (FMP/Twelve Data/EODHD), export CSV e verifica
aggiornamenti sono tutti raggiungibili da li'.

## Struttura del repository

```
src/quantumanalyzer/
    technical/        # Motore di conferma del trend: engine, indicators,
                      # data, risk, backtest, cli, updater.
    fundamental/      # Scoring value investing, campanelli d'allarme,
                      # config, cache, utils.
    common/           # Servizi condivisi: controllo aggiornamenti GitHub
                      # (updater.py), ricerca ticker (search.py), cache
                      # SQLite a TTL (cache.py).
    gui/              # GUI unificata PySide6: app.py (finestra principale +
                      # entry point), technical_view/_workers,
                      # fundamental_view/_workers, theme.py.
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

In alternativa, gli installer pronti (.exe/.dmg/.deb) sono pubblicati su
[Releases](https://github.com/enkas79/QuantumAnalyzer/releases): ogni push
che aggiorna `version.txt` su `main` costruisce e pubblica automaticamente
una nuova release tramite GitHub Actions.

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

MIT.
