# claude-mode-deck

Indicatore hardware della permission mode di Claude Code su uno stream deck
**Ajazz AKP03E rev. 2** (`0300:3002`), tramite **OpenDeck**.

Progetto personale, slug `smartdeck`, mono-repo, un solo utente.
Ambiente: **Linux Mint 22.3** (base noble), sessione **X11**, bash.

## Come funziona

```
Claude Code --(hook)--> ~/.claude/cc-state/<tipo>/<sessione>.json
                                    |
                                    +--(polling 500 ms)--> plugin OpenDeck --> tasto
     ^                                                                          |
     +------------- Shift+Tab via sendkeys.py (XTEST) <------- pressione -------+
```

Due indicatori, due hook, due cartelle: `mode/` per la permission mode,
`activity/` per lo stato di attività (lavora / ti aspetta / ha finito /
inattivo).

## Stato per sessione

**Un file per sessione, non uno solo.** Il nome è il `session_id`, che è
l'unico discriminante disponibile: nei payload degli hook non c'è né un PID né
un TTY, e il `cwd` è identico per due sessioni sullo stesso progetto —
verificato il 19/08/2026 rileggendo 129 righe di log di eventi veri.

`SessionEnd` **cancella** il file della propria sessione. Per il terminale che
muore senza mandarlo c'è una scadenza, **diversa per stato**, perché una
scadenza unica ricreerebbe il difetto in versione lenta — un permesso aperto
mentre sei a pranzo non è una sessione morta:

| Stato | Scade dopo | Perché |
|---|---|---|
| `work` | 30 min | 19× il silenzio massimo osservato con "lavora" attivo (95,2 s su 50 chiamate), 3× il tetto di 600 s di una chiamata Bash |
| `wait` | 4 ore | **nessun dato**: dipende da quanto ci mette una persona a tornare. Scelta di giudizio, dichiarata come tale |
| `done` | 30 min | innocuo in sé, ma un verde abbandonato terrebbe il deck verde invece che grigio |
| `idle` | mai | non afferma niente |

**Aggregazione**: l'attività mostra lo stato **più grave** fra tutte le
sessioni (`wait` > `work` > `done` > `idle`) — se una qualsiasi sessione ti
aspetta devi saperlo, ovunque sia. Non dice *quale*: è il prezzo, ed è
accettato. La modalità invece mostra la sessione **più recente**, perché quel
tasto è anche un comando: premuto manda `Shift+Tab` alla finestra attiva.

L'hook legge `permission_mode` dal JSON degli eventi e lo scrive su file. Il
plugin Node lo rilegge ogni 500 ms e manda `setImage` al deck.

Dal 15 agosto 2026 il giro si chiude anche in senso inverso: premere il tasto
manda `Shift+Tab` alla finestra attiva, quindi lo stesso tasto mostra la
modalita' e la cambia. Serve `python3-xlib`; `CC_MODE_CYCLE=0` lo riporta in
sola lettura.

## Struttura

```
hook/cc-mode.mjs                  hook di Claude Code, permission mode
hook/cc-activity.mjs              hook, stato di attivita' (lavora/aspetta/finito)
hook/cc-observe.mjs               hook di sola osservazione, temporaneo
io.github.meobob.ccmode.sdPlugin/        plugin OpenDeck (manifest, plugin.mjs, icone)
  └── sendkeys.py                 manda una combinazione via XTEST
scripts/installa.sh               installa hook e plugin (livello 1, portabile)
scripts/check.sh                  diagnostica in sola lettura
scripts/install-hook.sh           installa l'hook, idempotente
scripts/profili-genera.py         come sono stati prodotti i profili in uso
scripts/profili-da-zero.py        genera i profili da zero (livello 2)
scripts/profili-installa.sh       li installa, con backup e OpenDeck fermo
scripts/manopole-installa.py      programma le tre manopole (di suo non scrive)
scripts/volume.sh                 volume di sistema per la manopola centrale
scripts/install-activity.sh       installa e registra l'hook di attivita'
scripts/install-observe.sh        installa/rimuove l'osservatore
scripts/attivita-installa.py      mette il tasto Activity sullo slot 2
tools/cattura-tasti.py            registra i byte che arrivano dal deck
tools/genera-multiaction.py       come si costruisce un profilo multi-action
tools/prova-plugin.py             prova il plugin contro un finto server OpenDeck
tools/prova-home-pulita.sh        prova gli script in un HOME vuoto
keys/                             17 icone PNG per i tasti (+ provino.png)
backup/                           profili OpenDeck salvati (ha un suo README, non si pubblica)
make_icons.py                     rigenera le icone di stato del plugin
make_activity_icons.py            rigenera le icone dell'indicatore di attivita'
make_key_icons.py                 rigenera le icone dei tasti
LAYOUT.md                         cosa va su ogni tasto
INSTALL.md                        procedura di installazione
README.md                         come funziona il codice
docs/CONTEXT.md                   contesto del progetto, com'e' cresciuto
docs/PROMPT.md                    prompt di apertura per Claude Code
docs/esempio-multiaction.json     un Multi Action come lo scrive OpenDeck
```

## Percorsi reali di questa macchina

```
cartella plugin OpenDeck   ~/.config/opendeck/plugins
profili OpenDeck           ~/.config/opendeck/profiles/n3-4250D2784745/
log principale OpenDeck    ~/.local/share/opendeck/logs/opendeck.log
log del nostro plugin      ~/.config/opendeck/plugins/io.github.meobob.ccmode.sdPlugin/plugin.log
stato degli indicatori     ~/.claude/cc-state/{mode,activity}/<session_id>.json
```

Il log del plugin sta **dentro la sua cartella**, non nella cartella log di
OpenDeck: là esiste un file col nostro nome ma resta vuoto.

## Regole operative

**`sudo` non è utilizzabile da qui.** Niente tty, nessun helper askpass, e
nemmeno il prefisso `!` funziona. Ogni comando con `sudo` va passato all'utente
perché lo esegua in un terminale vero. Verificato, non dedotto.

**Non scrivere mai sui file di profilo di OpenDeck mentre OpenDeck gira.** Li
riscrive durante l'uso, non solo alla chiusura: al primo salvataggio le
modifiche esterne spariscono. Leggerli è sicuro.

Vale anche per le **cancellazioni**: tiene i profili in memoria e all'uscita
scrive `Successfully flushed all stale profiles on exit`, quindi un file
cancellato mentre gira ricompare. E se cancelli il profilo *attivo*, ricordati
di rimettere `selected_profile` su uno che esiste, in
`profiles/n3-4250D2784745.json`.

A OpenDeck fermo, invece, **generare profili da script funziona**: lo schema è
noto e documentato in LAYOUT.md, e i tre profili in uso sono nati così.

**Chiudere la finestra di OpenDeck non lo riavvia.** Resta nella tray; il
rilancio lascia uno zombie e ripresenta la vecchia istanza con la lista dei
plugin letta all'avvio. Serve *Quit* dalla tray, o `kill <PID>`.

**Per sapere se OpenDeck gira, usa `pgrep -x opendeck`, non un grep sulla riga
di comando.** Sia `ps ... | grep '[o]pendeck'` sia `pgrep -f 'bin/opendeck'`
pescano il comando stesso che stai lanciando, se da qualche parte contiene quel
testo — per esempio il percorso di `plugin.log`. Risultato: "OpenDeck e' vivo"
mentre e' fermo da un pezzo. Ci sono cascato due volte in un'ora.
Il nome esatto del processo e' `opendeck`; `pgrep -x` guarda quello.

**`opendeck --version` non stampa la versione: avvia OpenDeck.** Il flag non
esiste, viene ignorato, e parte l'applicazione intera — che non termina, quindi
un `$(opendeck --version)` resta appeso per sempre. Ci è cascato `check.sh`
stesso fino al 17/08/2026: con OpenDeck già acceso non si notava, a OpenDeck
fermo lo faceva ripartire di nascosto, plugin compresi. La versione si legge da
`dpkg-query -W -f='${Version}' opendeck`, che non esegue niente.

**Il node che conta è `/usr/bin/node`**, non quello del `PATH`. In `~/.local/bin`
c'è un secondo Node 22 estratto a mano; OpenDeck, lanciato dalla sessione
grafica, usa quello di sistema. Il criterio non è la versione ma la presenza
della classe `WebSocket`:
`/usr/bin/node -e 'console.log(typeof WebSocket)'`.

**La penna sul file di contesto è della chat Claude.ai, non di qui.** A fine
sessione proponi le modifiche a `smartdeck_CONTEXT.md` nel riepilogo; non
riscrivere il file. È già successo che due copie divergessero.

**Un comando che finisce in un documento va eseguito almeno una volta, o
dichiarato come non provato.** È successo due volte in tre giorni. Il 17/08 con
`genera-multiaction.py`. Il 19/08 col comando di disinstallazione appena scritto
in `INSTALL.md`: usava `install-hook.sh --rimuovi`, opzione che non esiste — e
quello script le opzioni sconosciute le ignora e **installa**. Chi avesse
seguito quella riga per disinstallare avrebbe reinstallato. Un comando scritto e
mai eseguito è una supposizione con l'aspetto di un'istruzione.

**Prima di `unzip -o` su un archivio del progetto, fai `unzip -l`.** Il browser
rinomina i download quando il nome è occupato, e un archivio vecchio riporta
indietro il progetto di settimane. È già successo.

## Verifica

```bash
./scripts/check.sh          # stato completo, sola lettura, non chiede sudo
```

Nessun test automatico. Dopo una modifica al plugin: riavviare OpenDeck **dalla
tray** e controllare `plugin.log`.

Dopo una modifica a una sequenza di tasti c'è invece una verifica vera, e non
costa niente: `tools/cattura-tasti.py`. Si lancia in un terminale
**neutro** (mai quello di Claude Code, o i tasti finiscono nella sessione), gli
si dà il focus, si premono i tasti del deck e lui registra ogni byte con
l'orario. È così che si è visto che i due `Esc` del Rewind arrivano a 0,0 ms di
distanza: a occhio non si vedeva.

## Cosa non toccare

- `~/.claude/settings.json` a mano: usa `scripts/install-hook.sh`, che fa il
  backup ed è idempotente.
- I file in `~/.config/opendeck/` in scrittura.
- `make_icons.py` e `make_key_icons.py` producono PNG rigenerabili: modifica lo
  script, non i PNG.

## Limiti noti — non sono bug da inseguire

1. L'indicatore si aggiorna al prossimo evento (prompt o tool call), non quando
   premi Shift+Tab. Gli hook ricevono `permission_mode` ma scattano sugli
   eventi; la status line ha il trigger giusto ma non riceve la modalità.
   **Misurato il 15/08/2026**: invio del messaggio alle 20:03:37, ridisegno del
   tasto alle 20:03:38.090. Vale anche premendo l'indicatore stesso — per
   questo mostra un puntino di attesa che scade dopo 6 secondi.
2. ~~Un solo file di stato: con più sessioni vince l'ultima.~~ **Risolto il
   19/08/2026.** Era il difetto peggiore del progetto, e non era teorico: una
   sessione mostrava `ti aspetta` con una richiesta di permesso aperta a
   schermo, e la notifica di inattività di *un'altra* sessione l'ha
   sovrascritta dopo 18 secondi. Ora ogni sessione ha il suo file in
   `~/.claude/cc-state/`, e il plugin aggrega. Vedi "Stato per sessione".
3. Il deck manda tasti alla finestra attiva: il terminale deve avere il focus.
   Vale anche per `sendkeys.py`, che usa la stessa strada (XTEST).
4. Un tasto appena creato resta `?` finché non lo premi una volta. Sparisce al
   riavvio di OpenDeck. Il perché sta nel codice: `willAppear` non arriva per un
   tasto nato mentre il plugin gira, e il `keyDown` è l'unico altro punto che
   forza il primo disegno.
5. Dentro un `Multi Action` l'indicatore non disegna: il contenitore si tiene la
   faccia del tasto. Misurato in tre varianti. È il motivo per cui la pressione
   che cicla la modalità sta nel plugin e non in un'azione impilata.
