# Piano di migrazione: fusione StockAnalyzer + QuantumValue

Questo documento descrive cosa e' gia' stato fatto e cosa resta da fare per
arrivare a un'unica app GUI che sostituisca [StockAnalyzer]
(https://github.com/enkas79/StockAnalyzer) e [QuantumValue]
(https://github.com/enkas79/QuantumValue). E' pensato per essere eseguito a
pezzi (un milestone = una PR), non tutto insieme.

## Stato di avanzamento

| Milestone | Stato |
|---|---|
| M1 — Scaffold logica core | ✅ Fatto |
| M2 — Porting GUI QuantumValue a PySide6 | ✅ Fatto (13 test GUI portati e verdi; le librerie Qt di sistema si sono rivelate installabili, quindi il porting e' stato testato davvero, non solo compilato) |
| M3 — Spostamento GUI StockAnalyzer | ✅ Fatto (17 test GUI portati) |
| M4 — Finestra unificata con barra ticker condivisa | ✅ Fatto (entry point `quantumanalyzer-gui`; prima iterazione "sottile": le tab conservano i propri menu) |
| M5 — Deduplicazione servizi | ✅ Parziale: controllo aggiornamenti unificato in `common/updater.py` (con fix di un bug latente RetryError). Restano: ricerca ticker, cache condivisa, unificazione watchlist/recenti |
| M6 — CI | ✅ Parziale: `ci.yml` esegue l'intera suite (GUI incluse, offscreen). Resta: pipeline installer unificata (PyInstaller + Inno Setup/.deb/.dmg) |
| M7 — Migrazione dati utenti esistenti | ✅ Fatto (`common/legacy_import.py`, one-shot all'avvio della GUI) |
| M8 — Destino dei repo originali | ⏳ Decisione dell'autore |

Lavori residui in ordine di valore: pipeline installer (M6), ricerca ticker e
cache condivise (M5), unificazione watchlist/ticker recenti (M4.3), mypy in CI.

Il resto del documento e' il piano originale, conservato come riferimento per
i dettagli e le motivazioni delle scelte.

## Stato attuale (M1 — fatto in questo scaffold)

- [x] Repository creato, `src/quantumanalyzer/technical/` (da StockAnalyzer) e
      `src/quantumanalyzer/fundamental/` (da QuantumValue, parti non-GUI)
      portati con import adattati al nuovo pacchetto.
- [x] Test portati (esclusi quelli di GUI/controller): 144 test passano.
- [x] `pyproject.toml`/`requirements.txt` unificati per la sola logica core
      (nessuna dipendenza GUI ancora dichiarata).
- [x] `version.txt` unico alla radice (parte da `0.1.0`, nuovo progetto).
- [x] Identita' app rinominata nei moduli portati (logger, keyring service,
      cartella cache/log `~/.quantumanalyzer/`, `GITHUB_REPO` in config.py)
      per non confliggere con le installazioni esistenti di QuantumValue.

Quello che **non** e' stato fatto (deliberatamente, per tenere questo primo
passo verificabile e a basso rischio): nessuna GUI, nessuna deduplicazione di
logica fra i due sotto-pacchetti, nessuna pipeline di build/release.

## M2 — Decisione framework GUI e porting di QuantumValue

**Decisione da prendere prima di scrivere codice**: StockAnalyzer usa
**PySide6** (LGPL, libero anche per distribuzione closed-source), QuantumValue
usa **PyQt6** (GPL o licenza commerciale Riverbank a pagamento per uso
closed-source). Consiglio: **unificare su PySide6**, perche':
- E' gia' la scelta di uno dei due programmi (meno codice da riscrivere in
  totale, dato che QuantumValue ha la GUI piu' grande delle due — `views.py`
  e' ~68KB contro i file GUI di StockAnalyzer).

  Attenzione pero': in termini di *quantita*' di porting, spostare QuantumValue
  su PySide6 e' comunque il lavoro piu' grosso di questo piano, perche' la sua
  GUI e' la piu' grande delle due. La scelta di PySide6 minimizza il rischio
  di licenza, non lo sforzo di porting.
- Se QuantumValue Analysis viene distribuito come eseguibile gratuito (come
  suggerisce il README con gli installer Inno Setup/deb/dmg), PyQt6 senza
  licenza commerciale pone un problema di licenza GPL per la distribuzione
  closed-source; PySide6 no.

Passi:
1. Portare `views.py`, `controllers.py`, `theme.py`, `main.py` di QuantumValue
   in `src/quantumanalyzer/gui/fundamental_view.py` (o piu' file), traducendo
   l'API PyQt6 -> PySide6:
   - `pyqtSignal` -> `Signal`, `pyqtSlot` -> `Slot`
   - `from PyQt6.QtWidgets import X` -> `from PySide6.QtWidgets import X`
     (stesso modulo per `QtCore`/`QtGui`)
   - Verificare le differenze minori di enum (`Qt.AlignmentFlag` ecc. sono
     gia' scritte in stile "PyQt6 nuovo" in QuantumValue, che e' quasi
     identico alla sintassi PySide6 — il porting e' in gran parte meccanico)
2. Far girare la sola vista fondamentale standalone (finestra singola, non
   ancora integrata nel resto) per validare che il porting non abbia rotto
   nulla, con gli stessi test manuali descritti nel README di QuantumValue.
3. Portare la suite di test GUI di QuantumValue (`test_controllers.py`,
   `test_views_workers.py`, `pytest-qt`) adattandola a PySide6.

**Nota ambientale**: in questa sessione non e' stato possibile eseguire i
test GUI di nessuno dei due repo originali (libreria di sistema `libEGL.so.1`
mancante nel sandbox e non installabile per un problema del mirror apt). Chi
riprende da qui deve verificare in un ambiente con Qt disponibile (o via CI,
vedi M6) prima di considerare il porting GUI concluso.

## M3 — Porting della GUI tecnica (StockAnalyzer)

Gia' su PySide6, quindi il lavoro qui e' principalmente di **spostamento**,
non di traduzione:
1. Copiare `stockanalyzer/gui/main_window.py` e `worker.py` in
   `src/quantumanalyzer/gui/technical_view.py` (o mantenere due file),
   aggiornando gli import da `from ..data import ...` / `from ..engine import
   ...` a `from ..technical.data import ...` / `from ..technical.engine import
   ...`.
2. Portare `test_gui_main_window.py`.

## M4 — Finestra principale unificata

Obiettivo: un'unica finestra con un campo ticker condiviso che alimenta
entrambe le analisi.

1. Nuova `MainWindow` in `src/quantumanalyzer/gui/main_window.py` con tab:
   **Analisi Tecnica** (da StockAnalyzer) | **Analisi Fondamentale** +
   **Occasioni in Borsa** + **Campanelli d'Allarme** (da QuantumValue) | **ETF**
   (da QuantumValue) | **Watchlist** (da StockAnalyzer).
2. Un solo campo di ricerca ticker in cima: al submit, avvia in parallelo (due
   `QThread`/worker separati, uno per `technical.data.fetch_ohlcv` e uno per
   `fundamental.models.FinancialDataFetcher.fetch_data`) entrambi i fetch,
   popolando le tab rispettive quando ciascuno termina — senza bloccare l'uno
   sull'altro, dato che oggi impiegano tempi diversi (OHLCV via yfinance e'
   tipicamente piu' veloce del fetch fondamentali con hedging FMP).
3. Decidere il comportamento di "Watchlist" (StockAnalyzer) vs "Ticker
   Recenti" (QuantumValue): sono concettualmente lo stesso tipo di lista
   (ticker salvati fra sessioni); valutare se unificarle in un'unica lista
   condivisa fra le tab o tenerle separate perche' rispondono a scopi diversi
   (watchlist = titoli da ri-analizzare, recenti = cronologia di ricerca).

## M5 — Deduplicazione dei servizi condivisi

Le due basi di codice duplicano indipendentemente le stesse funzionalita'.
Non sono state deduplicate in questo scaffold (per rischio/tempo), ma sono i
candidati piu' chiari per farlo qui:

| Funzionalita' | StockAnalyzer | QuantumValue | Azione proposta |
|---|---|---|---|
| Controllo aggiornamenti GitHub | `technical/updater.py` (dataclass `UpdateInfo`, `urllib`) | `fundamental/models.py::check_for_updates` + `pick_release_asset` (`requests`, con retry `tenacity`) | Unificare in `quantumanalyzer/common/updater.py`, tenendo il supporto retry di QuantumValue (piu' robusto) |
| Ricerca ticker per nome | `technical/data.py::search_candidates` (`yf.Search`) | `fundamental/models.py::search_by_name` (endpoint HTTP diretto Yahoo) | Unificare in `quantumanalyzer/common/search.py`; scegliere un solo meccanismo (valutare quale dei due e' piu' affidabile in produzione) |
| Cache locale | Cache su disco 15 minuti (vedi README StockAnalyzer) | SQLite con scadenza 1 ora (`fundamental/cache.py`) | TTL diversi per motivi diversi (prezzi intraday vs fondamentali trimestrali): tenere due cache separate ma sulla stessa implementazione condivisa in `common/cache.py`, parametrizzata per TTL |
| Impostazioni persistite | `QSettings` (org/app StockAnalyzer) | `QSettings` (org/app QuantumValue) + keyring per le API key | Un solo namespace `QSettings` per QuantumAnalyzer (vedi M7 per la migrazione dei dati esistenti) |
| Retry HTTP | Nessuno (fallback Yahoo -> Stooq) | Decoratore `tenacity` su tutte le chiamate esterne | Nessuna azione obbligatoria: modelli di resilienza diversi per problemi diversi, non necessariamente da unificare |

## M6 — Packaging e CI unificati

- Un solo workflow GitHub Actions (oggi entrambi i repo ne hanno uno separato
  per PyInstaller + Inno Setup/`.deb`/`.dmg`) che legge `version.txt` alla
  radice di questo repo.
- La CI deve eseguire anche i test GUI (`pytest-qt`) con `QT_QPA_PLATFORM=
  offscreen` e le librerie di sistema Qt installate — verificare cosa fanno
  gia' i workflow dei due repo originali per questo, dato che nel sandbox di
  sviluppo usato per preparare questo scaffold non e' stato possibile
  installarle (mirror apt non raggiungibile per `libegl-mesa0`).
- Un solo installer (`QuantumAnalyzer-Setup-vX.Y.Z.exe`/`.deb`/`.dmg`) al posto
  dei due separati.

## M7 — Migrazione dati utenti esistenti

Chi ha gia' installato QuantumValue e/o StockAnalyzer ha dati locali sparsi
in posti diversi da quelli usati da questo scaffold (che usa gia'
`~/.quantumanalyzer/` — vedi sopra):
- API key FMP/TwelveData/EODHD salvate nel portachiavi di sistema sotto il
  servizio `"QuantumValue"` (il codice portato qui usa gia' `"QuantumAnalyzer"`
  come nuovo nome di servizio, quindi le chiavi esistenti **non** verrebbero
  trovate automaticamente).
- Cache SQLite (`~/.quantumvalue/cache/quantumvalue_cache.db`) e log
  (`~/.quantumvalue/quantumvalue_debug.log`).
- `QSettings` con watchlist/ticker recenti/tema per entrambi i programmi.

Prima del rilascio pubblico di QuantumAnalyzer, serve un piccolo importer
one-shot al primo avvio che, se trova i vecchi percorsi
`~/.quantumvalue/`, offra di migrare API key (ri-leggendole dal vecchio nome
di servizio keyring) e le impostazioni. Senza questo passo gli utenti
esistenti perdono silenziosamente le chiavi API salvate passando al nuovo
programma.

## M8 — Cosa fare dei due repository originali

Questa e' una decisione che spetta a te, non qualcosa che va deciso in un
piano tecnico: quando QuantumAnalyzer raggiunge la parita' di funzionalita',
puoi scegliere fra continuare a mantenere StockAnalyzer/QuantumValue in
parallelo, archiviarli (read-only, con un README che punta qui), o cancellarli.
Nessuna di queste azioni e' stata presa automaticamente in questo scaffold.

## Stima di sforzo indicativa

| Milestone | Sforzo | Rischio |
|---|---|---|
| M2 (porting GUI QuantumValue a PySide6) | Grande (file piu' grosso da tradurre) | Medio (traduzione API in gran parte meccanica, ma va testata a mano: nessun test GUI eseguibile in questo sandbox) |
| M3 (spostamento GUI StockAnalyzer) | Piccolo | Basso |
| M4 (finestra unificata) | Medio | Medio (decisioni di UX: layout tab, comportamento watchlist) |
| M5 (deduplicazione servizi) | Medio | Basso (codice puro, ben testabile) |
| M6 (CI/packaging) | Medio | Basso |
| M7 (migrazione dati utente) | Piccolo | Alto se saltato (perdita silenziosa di API key per gli utenti esistenti) |
