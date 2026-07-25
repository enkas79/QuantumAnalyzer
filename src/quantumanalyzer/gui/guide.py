"""
Guida unificata dell'app: unisce in un'unica finestra le due guide che
prima erano separate (Analisi Tecnica, da StockAnalyzer; Analisi
Fondamentale, da QuantumValue), ciascuna raggiungibile da una propria voce
del menu "Guida". Un solo GUIDE_HTML con indice a due riquadri in testa e
ancore interne (#tecnica, #fondamentale), che QTextBrowser naviga di serie
senza codice aggiuntivo.
"""

from typing import Optional

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout, QWidget

GUIDE_HTML = """\
<a name="top"></a>
<table width="100%" cellspacing="0" cellpadding="0" style="background-color:#2c3e50; margin-bottom:14px;">
<tr><td style="padding:18px 22px;">
<span style="color:#ffffff; font-size:21px; font-weight:bold;">&#128218; Guida QuantumAnalyzer</span><br>
<span style="color:#bdc3c7; font-size:12px;">Analisi Tecnica (trend-confirmation) e Analisi Fondamentale (value investing), sullo stesso titolo</span>
</td></tr>
</table>

<table width="100%" cellspacing="8" cellpadding="0">
<tr>
<td width="50%" valign="top" style="background-color:#eaf3fb; border:1px solid #2980b9; padding:10px;">
<a href="#tecnica" style="color:#2980b9; font-weight:bold; font-size:14px; text-decoration:none;">&#9654; Analisi Tecnica</a><br>
<span style="color:#555555; font-size:11px;">Ricerca, periodo/intervallo, leg del punteggio, rischio, grafico, watchlist, backtest, impostazioni</span>
</td>
<td width="50%" valign="top" style="background-color:#eafaf1; border:1px solid #27ae60; padding:10px;">
<a href="#fondamentale" style="color:#27ae60; font-weight:bold; font-size:14px; text-decoration:none;">&#9654; Analisi Fondamentale</a><br>
<span style="color:#555555; font-size:11px;">Value investing (EY, ROIC, EV/EBITDA), occasioni in borsa, ETF</span>
</td>
</tr>
</table>

<a name="tecnica"></a>
<h2 style="color:#2980b9; border-bottom:2px solid #2980b9; padding-bottom:4px; margin-top:24px;">&#128200; Analisi Tecnica</h2>
<p style="color:#555555;">Risponde alla domanda: <i>il trend attuale e' affidabile?</i> Punteggio a leg basato su EMA 50/200, RSI(14), volume relativo, con MACD/Bollinger opzionali; ATR e size suggerita per il rischio.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">1. Come cercare un titolo</h3>
<p>Nel campo Ticker puoi inserire un ticker (es. <i>AAPL</i>) oppure il nome
dell'azienda (es. <i>Eni</i>). Dopo un paio di lettere compare un elenco
di aziende corrispondenti con simbolo e borsa (es. <i>ENI.MI</i> &mdash; Eni
S.p.A., Milan): seleziona quella giusta dall'elenco prima di premere
"Analizza", cosi' il ticker usato e' esattamente quello scelto. Se scrivi
un ticker esatto gia' noto (es. <i>AAPL</i>) puoi anche analizzare
direttamente senza passare dall'elenco.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">2. Periodo e intervallo</h3>
<p>Il periodo va da una settimana a 5 anni. L'elenco degli intervalli
disponibili si aggiorna automaticamente in base al periodo scelto, in
modo da garantire sempre almeno 200 candele (necessarie per calcolare
l'EMA200 in modo affidabile): per i periodi corti (settimana, mese, 3/6
mesi) vengono proposti solo intervalli intraday (es. 5m, 30m, 1h),
mentre da 1 anno in su resta disponibile anche il giornaliero. La stima
del numero di candele e' mostrata sotto i menu.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">3. Leg opzionali</h3>
<p>Le caselle MACD e Bollinger Bands aggiungono due leg di conferma
facoltativi (disattivati di default). Se li attivi, il punteggio si
ricalcola automaticamente includendo il loro peso, quindi il punteggio a
3 leg di default non cambia finche' restano spenti. Le stesse caselle
aggiungono anche il relativo indicatore alla scheda Grafico (pannello
MACD sotto il prezzo, bande di Bollinger sovrapposte al prezzo):
l'effetto si vede subito, anche senza rilanciare l'analisi.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">4. Come leggere il risultato</h3>
<ul>
<li><b>Direzione</b> (bullish/bearish/neutral): stabilita <u>solo</u> dal
leg trend (EMA50 rispetto a EMA200). Gli altri leg &mdash; momentum, volume,
ed eventualmente macd/bollinger &mdash; non possono cambiarla: possono solo
confermarla, restare neutri, o metterle veto. Per questo la direzione
puo' restare "bullish"/"bearish" anche con punteggio basso e 0
conferme: indica il regime di fondo (EMA50 sopra o sotto EMA200), non
che sia il momento di agire.</li>
<li><b>Confidenza (0-100)</b> e <b>conferme</b>: quanto gli altri leg
supportano quella direzione <i>adesso</i>. Un punteggio basso o
ambiguo &mdash; anche con direzione bullish/bearish &mdash; significa che il
mercato non da' un'indicazione chiara: non e' un segnale binario di
buy/sell.</li>
<li><b>Esempio</b>: EMA50 sopra EMA200 (struttura rialzista) ma prezzo
sotto EMA50 (pullback), RSI neutro e volume sottile &rarr; puoi vedere
"BULLISH" con punteggio 37/100 e 0/3 conferme. Non e' un errore: la
direzione riflette solo la struttura EMA50/200, mentre il punteggio
basso dice che nessun altro leg conferma un ingresso adesso.</li>
</ul>

<h3 style="color:#2c3e50; margin-bottom:2px;">5. I leg</h3>
<ul>
<li><b>trend</b> (EMA 50/200): l'unico che stabilisce la direzione
(bullish se EMA50 &gt; EMA200, bearish se EMA50 &lt; EMA200). Il suo stato
puo' essere solo confirm (prezzo anche lui sopra/sotto EMA50, in
accordo) o neutral (prezzo in pullback/rimbalzo): mai veto, perche' e'
lui a definire la direzione stessa.</li>
<li><b>momentum</b> (RSI 14): filtro, non trigger. Conferma il trend,
resta neutro, oppure mette veto se il trend e' gia' esteso in
ipercomprato/ipervenduto.</li>
<li><b>volume</b> (relativo alla media a 20 giorni): conferma se il
movimento e' supportato da volume, veto se e' sottile e quindi a rischio
falso segnale.</li>
<li><b>macd</b> (opzionale): confronta la MACD line con la signal line;
conferma se concorde con la direzione del trend, veto se in contrasto.</li>
<li><b>bollinger</b> (opzionale): veto se il prezzo e' gia' oltre la banda
nella direzione del trend (movimento troppo esteso, rischio
ritracciamento/rimbalzo), altrimenti conferma.</li>
</ul>
<table cellspacing="0" cellpadding="4"><tr>
<td style="color:#2e7d32; font-weight:bold;">&#9632; Verde = conferma</td>
<td style="color:#757575; font-weight:bold;">&#9632; Grigio = neutro</td>
<td style="color:#c62828; font-weight:bold;">&#9632; Rosso = veto</td>
</tr></table>

<h3 style="color:#2c3e50; margin-bottom:2px;">6. Rischio e position sizing</h3>
<ul>
<li><b>Prezzo</b>: ultima chiusura disponibile per il ticker.</li>
<li><b>ATR</b> (Average True Range, 14 periodi): volatilita' media
recente in valuta. Non entra nel punteggio di confidenza &mdash; serve solo
a dimensionare il rischio.</li>
<li><b>Stop suggerito</b>: distanza dal prezzo per un eventuale
stop-loss, pari ad ATR &times; 1.5 di default. E' una distanza basata sulla
volatilita' storica, non un livello garantito ne' legato a
supporti/resistenze specifici del titolo.</li>
<li><b>Capitale</b> e <b>Rischio per trade (%)</b>: quanto sei disposto
a perdere in valuta se lo stop viene toccato (es. capitale 10.000 e
rischio 1% = 100 di perdita massima accettata).</li>
<li><b>Size suggerita</b>: azioni = (capitale &times; rischio%) &divide; stop
suggerito, arrotondato per difetto. Esempio: capitale 10.000, rischio
1% (cioe' 100), stop 3.00 &rarr; 33 azioni. A parita' di rischio in valuta,
uno stop piu' stretto (titolo meno volatile) alza la size, uno piu'
largo (titolo piu' volatile) la abbassa.</li>
<li>Questi numeri sono un calcolo meccanico sui parametri che inserisci,
non una raccomandazione di investimento.</li>
</ul>

<h3 style="color:#2c3e50; margin-bottom:2px;">7. Scheda Grafico</h3>
<p>Mostra il prezzo con EMA50/EMA200 sovrapposte e, sotto, l'RSI(14) con le
soglie di ipercomprato (70) e ipervenduto (30), per l'ultimo ticker
analizzato nella scheda Analisi. Se in "Indicatori opzionali" (scheda
Analisi) sono attivi MACD e/o Bollinger Bands, compaiono anche qui: le
bande sovrapposte al prezzo, il MACD in un pannello proprio sotto
l'RSI.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">8. Scheda Watchlist</h3>
<p>Aggiungi piu' ticker a una lista salvata tra le sessioni. "Analizza
tutti" li scarica e valuta uno alla volta su un thread separato, senza
bloccare l'interfaccia, e popola una tabella ordinabile (clicca
sull'intestazione di una colonna per ordinare) con direzione,
confidenza e conferme. Un ticker che fallisce (es. non trovato) resta
visibile in tabella con l'errore, senza interrompere l'analisi degli
altri. Doppio click su una riga (o selezionala e premi "Carica
selezionato") per aprirla nella scheda Analisi e nel Grafico.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">9. Backtest (da codice, non ancora in questa finestra)</h3>
<p>Il modulo <i>stockanalyzer.backtest</i> fa scorrere il motore su una
finestra storica crescente e confronta ogni chiamata direzionale
(bullish/bearish; i casi neutral non contano) con il rendimento
realizzato un certo numero di candele dopo, per verificare quanto le
chiamate del motore siano state coerenti con i movimenti successivi.
Non e' un simulatore di trading: nessun costo, slippage o size viene
modellato, e' solo un controllo di coerenza del punteggio. Si usa cosi':</p>
<table width="100%" cellspacing="0" cellpadding="8" style="background-color:#f4f4f4; border:1px solid #d9d9d9;"><tr><td>
<code>from stockanalyzer.backtest import run_backtest<br>
result = run_backtest(df, forward_bars=10, step=5)<br>
print(result.hit_rate, result.avg_forward_return)<br>
print(result.by_score_bucket)&nbsp;&nbsp;# dettaglio per fascia di punteggio</code>
</td></tr></table>
<p><i>forward_bars</i> e' quante candele dopo si misura il rendimento,
<i>step</i> ogni quante candele si ripete il test (per velocita').
<i>result.by_score_bucket</i> suddivide i risultati in tre fasce di
punteggio (0-33, 34-66, 67-100) per vedere se un punteggio piu' alto
corrisponde davvero a un tasso di successo migliore.</p>

<h3 style="color:#2c3e50; margin-bottom:2px;">10. Impostazioni salvate e aggiornamenti</h3>
<p>Ticker, periodo, intervallo, watchlist e tema (menu Visualizza) vengono
ricordati automaticamente alla chiusura e ripristinati al riavvio.
All'avvio l'app controlla in background, su GitHub, se e' disponibile
una versione piu' recente: se si', mostra un avviso con il link alla
release, senza scaricare o installare nulla in automatico.</p>

<p align="right"><a href="#top" style="font-size:11px; color:#2980b9; text-decoration:none;">&#8593; Torna all'indice</a></p>

<hr style="border:none; border-top:1px solid #d9d9d9; margin:26px 0;">

<a name="fondamentale"></a>
<h2 style="color:#27ae60; border-bottom:2px solid #27ae60; padding-bottom:4px; margin-top:10px;">&#128176; Analisi Fondamentale</h2>
<p style="color:#555555;">Risponde alla domanda: <i>il prezzo attuale e' giustificato dai fondamentali?</i> Questa sezione si basa sui principi del <i>Value Investing</i> per valutare la reale qualita' e convenienza di un'azienda sul mercato, abbinandoli a un'analisi rapida delle <b>Occasioni in Borsa</b> e degli <b>ETF</b>.</p>

<h3 style="color:#2980b9; margin-bottom:2px;">Analisi Core: Qualita' e Valore (Value Investing)</h3>

<h4 style="color:#2980b9; margin-bottom:2px;">1. Earnings Yield (EY) &mdash; Il "Re" del Valore</h4>
<p>L'Earnings Yield e' il reciproco del rapporto P/E ed e' calcolato nella sua forma piu' robusta (utilizzata da Joel Greenblatt nella <i>Magic Formula</i>).</p>
<ul>
<li><b>Formula:</b> EBIT / Enterprise Value (EV)</li>
<li><b>Perche' funziona:</b> A differenza del semplice P/E, l'EV include il debito e sottrae la cassa, fornendo una visione reale di quanto "costa" l'intera azienda rispetto ai suoi utili operativi.</li>
<li><b>Dati Statistici:</b> Strategie basate sull'acquisto del decile con il piu' alto Earnings Yield hanno storicamente sovraperformato l'S&amp;P 500 con un <i>win rate</i> superiore al <b>65-70%</b> su orizzonti di 10 anni.</li>
</ul>

<h4 style="color:#2980b9; margin-bottom:2px;">2. Return on Invested Capital (ROIC) &mdash; Il Proxy della Qualita'</h4>
<p>Il ROIC misura l'efficienza con cui un'azienda genera profitti dal capitale investito (sia debito che equity).</p>
<ul>
<li><b>Formula:</b> NOPAT / Capitale Investito</li>
<li><b>Perche' funziona:</b> Identifica le aziende con un "Moat" (fossato economico) elevato. Un ROIC costantemente superiore al costo del capitale (WACC) e' il principale motore della creazione di valore a lungo termine.</li>
<li><b>Dati Statistici:</b> L'integrazione del ROIC in una strategia "Magic Formula" (combinato con l'Earnings Yield) ha prodotto rendimenti medi annui del <b>26,4% nel periodo 1991-2024</b>, battendo il mercato in 23 anni su 34 (win rate del <b>67,6%</b>).</li>
</ul>

<h4 style="color:#2980b9; margin-bottom:2px;">3. Enterprise Value to EBITDA (EV/EBITDA) &mdash; L'Indicatore di Resilienza</h4>
<p>Questo multiplo e' considerato molto piu' affidabile del Price-to-Book (P/B) o del P/E per confrontare aziende con diverse strutture di capitale.</p>
<ul>
<li><b>Perche' funziona:</b> L'EBITDA e' meno soggetto a manipolazioni contabili rispetto all'utile netto, e l'EV neutralizza le differenze di leva finanziaria tra le aziende.</li>
<li><b>Dati Statistici:</b> Studi di <i>O'Shaughnessy Asset Management</i> indicano che l'EV/EBITDA ha un "quintile spread" (la differenza di rendimento tra i titoli piu' economici e quelli piu' costosi) del <b>6,0%</b>, superando significativamente il 2,8% del P/B e il 5,1% del P/E.</li>
</ul>

<h3 style="color:#27ae60; margin-bottom:2px;">Come trovare Occasioni in Borsa (i 4 indicatori rapidi)</h3>
<p>Questa sezione si concentra sui multipli di mercato essenziali per capire se si sta pagando il giusto prezzo in rapporto alla crescita e ai ricavi:</p>
<ul>
<li><b>P/E (Price/Earnings):</b> indica quanto stai pagando per ogni euro di utile. <b>Ideale se P/E &lt; 20</b>. Buon prezzo rispetto agli utili.</li>
<li><b>P/S (Price/Sales):</b> misura quanto il mercato paga un'azienda rispetto ai suoi ricavi. <b>Ideale se P/S &lt; 2</b>. Buon prezzo rispetto ai ricavi.</li>
<li><b>PEG (Price/Earnings to Growth):</b> indica quanto stai pagando per ogni euro di utile, considerando anche il tasso di crescita atteso. <b>Ideale se PEG &lt; 1</b>. Buon prezzo rispetto alla crescita degli utili.</li>
<li><b>EV/EBITDA:</b> indica quanto stai pagando per l'intero business, debiti inclusi. <b>Ideale se EV/EBITDA &lt; 10</b>. Buon prezzo rispetto ai flussi operativi.</li>
</ul>

<h3 style="color:#8e44ad; margin-bottom:2px;">Valutazione ETF (Exchange Traded Funds)</h3>
<p>Gli ETF sono strumenti passivi. La loro valutazione si basa sull'efficienza dei costi, la liquidita' e il tracking dell'indice:</p>
<ul>
<li><b>TER (Total Expense Ratio):</b> misura i costi annuali di gestione. <b>Ideale se &lt; 0,25%</b>. Costi bassi massimizzano l'interesse composto nel lungo termine.</li>
<li><b>AUM (Dimensione del Fondo):</b> misura il capitale totale gestito (in milioni). <b>Ideale se &gt; 500M</b>. Fondi piu' grandi sono piu' liquidi e hanno un rischio minore di chiusura o delisting.</li>
<li><b>Rendimento (Performance 1Y/3Y):</b> valuta la bonta' del trend. Rendimenti positivi e costanti indicano un asset in salute.</li>
</ul>

<p align="right"><a href="#top" style="font-size:11px; color:#27ae60; text-decoration:none;">&#8593; Torna all'indice</a></p>
"""


class UnifiedGuideDialog(QDialog):
    """Guida unica dell'app: sostituisce le due finestre separate
    (technical_view._build_guide_dialog, fundamental_view.GuideDialog) con
    un'unica finestra indicizzata, aperta dall'unica voce "Guida" del menu."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Guida")
        self.setMinimumSize(820, 700)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(GUIDE_HTML)
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
