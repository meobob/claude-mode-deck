# Contesto progetto — Claude Code Mode / Ajazz AKP03E

> Ricaricami all'inizio della prossima sessione. Non ho memoria persistente tra
> conversazioni: questo file è il sostituto.

**Ultimo aggiornamento:** 14 agosto 2026, sera — *installazione completata e
verificata su hardware; layout deciso; configurazione dei tasti appena iniziata.*

## Obiettivo

Trasformare un **Ajazz AKP03E** (stream deck economico: 9 tasti di cui 6 con
schermo, 3 manopole, USB-C) in un pannello di controllo per **Claude Code CLI**,
replicando le funzioni della tastiera AhaKey-X1 vista su AliExpress.

## Ambiente — valori reali, non più ipotesi

- **Linux Mint 22.3**, base Ubuntu **noble** (24.04), sessione **X11** (Cinnamon)
- Windows come secondario (stessa config se possibile) — **mai provato**
- Strumento AI principale: Claude Code CLI (installer nativo, non npm:
  `~/.local/bin/claude` → `~/.local/share/claude/versions/…`)
- Dispositivo: `0300:3002` = AKP03E **rev. 2**, ID interno `n3-4250D2784745`

Versioni installate al 14 agosto 2026:

| Componente | Versione |
|---|---|
| OpenDeck (`.deb`) | 2.14.0 |
| Plugin AKP03 | 0.10.1 (INSTALL.md citava la 0.8.1) |
| `nodejs` (NodeSource) | 22.23.2-1nodesource1 → `/usr/bin/node` v22.23.2 |
| Plugin indicatore | 0.1.0 |

## La forma reale del dispositivo

**Correzione del 14 agosto 2026** a una cosa data per buona all'inizio. La scheda
prodotto descrive i tre tasti in basso come "tasti di cambio scena/pagina":
racconta cosa ne fa il software ufficiale Ajazz, **non** un vincolo dell'hardware.
Sotto OpenDeck sono tasti normali, solo senza schermo.

```
[ 1 ] [ 2 ] [ 3 ]     riga 1 — con schermo
[ 4 ] [ 5 ] [ 6 ]     riga 2 — con schermo
[ 7 ] [ 8 ] [ 9 ]     riga 3 — SENZA schermo
( A ) ( B ) ( C )     3 manopole
```

Conseguenza: **le pagine non sono gratis, vanno comprate spendendo tasti.**
Configurazione scelta: **tre profili**, con i tasti 7-8-9 su `Switch Profile`.
Costo 9 assegnazioni, resa 18 slot. Dettagli in `LAYOUT.md`.

Il prezzo vero non sono i tre tasti: è che **nessun tasto resta premibile senza
guardare**. I ciechi sono gli unici individuabili al tatto e se ne vanno tutti in
navigazione. Se dopo qualche giorno pesa, la via d'uscita è passare a due profili.

## Decisioni prese

| Decisione | Motivo |
|---|---|
| **OpenDeck** invece del software Ajazz ufficiale | Il software ufficiale non esiste per Linux (solo Windows 7+ / macOS 10.13+). OpenDeck è cross-platform e i profili si spostano tra piattaforme senza modifiche. |
| Plugin AKP03 non ufficiale `4ndv/opendeck-akp03` | L'AKP03E è nella lista dispositivi supportati (`0300:1002`, rev.2 `0300:3002`). Rischio noto: l'autore dichiara supporto garantito su Linux, "best effort" su Mac, **zero sforzo su Windows**. |
| Plugin indicatore scritto in **Node.js** | OpenDeck supporta plugin Node (richiede Node nativo, non Flatpak). Un plugin HTML/webview non avrebbe potuto leggere il filesystem. |
| Uso di `setImage`, non `setState` | La doc OpenAction ha un esempio evidentemente errato per `setState` (event `logMessage`, manca `context`). `setImage` è specificato in modo univoco. |
| Colore ignoto = grigio, bypass = magenta | Fail-safe: un indicatore non deve mai mostrare verde quando non sa. |
| Node 22 da NodeSource col **metodo manuale**, non `setup_22.x` | Lo script NodeSource verifica il nome in codice della distro; Mint riporta il proprio (`wilma`, `xia`…), non quello di Ubuntu. Il percorso `nodistro` non dipende dal nome in codice. **Confermato sul campo: ha funzionato al primo colpo.** |
| OpenDeck da `.deb`, non Flatpak e **mai AppImage** | Col Flatpak il plugin gira nel sandbox e deve leggere `~/.claude/cc-mode.json`: permessi non verificati. L'AppImage è sconsigliato dal progetto stesso. **Il `.deb` si è installato su base noble senza alcun problema di dipendenze.** |
| Installazione delegata a **Claude Code**, non a Cowork | Cowork esegue codice in una VM sandbox: non fa `sudo apt`, non scrive in `/etc/udev`, non parla con USB. E su Linux non risulta esserci una build ufficiale dell'app desktop (fonti discordanti). |
| **Tre profili** invece delle pagine native | I tasti ciechi non sono tasti pagina (vedi sopra). Tre profili con `Switch Profile` sui ciechi sono l'equivalente più vicino. |

## Cosa replica l'AhaKey-X1 e cosa no

| Funzione AhaKey | Sull'AKP03E |
|---|---|
| Tasti scorciatoia con icone | ✅ 18 slot (6 tasti con schermo × 3 profili), l'AhaKey ne ha 12 — ma costano 3 tasti ciechi per la navigazione |
| Manopole | ✅ 3, per scroll/volume/zoom — **mai mappate** |
| Input vocale | ✅ **nativo in Claude Code**: `/voice tap` — tap per iniziare, tap per fermare, invio automatico. Un tasto del deck basta. Il mic dell'AhaKey non è nemmeno incluso nel prodotto originale. |
| Leva di auto-approvazione | ⚠️ parziale: Shift+Tab cicla le modalità (`chat:cycleMode`). Non esiste un'azione per saltare a una modalità specifica — feature request aperta (issue anthropics/claude-code#32604). |
| Barra LED con stato dell'IDE | ✅ **funzionante su hardware reale dal 14 agosto 2026**, ma non in tempo reale (vedi limiti) |

## Stato attuale — FATTO E VERIFICATO SU HARDWARE

Tutte le fasi di INSTALL.md eseguite e superate. **Il progetto funziona.**
Non è più "mai testato su hardware reale".

- `hook/cc-mode.mjs` — installato in `~/.claude/hooks/`, registrato su
  `UserPromptSubmit`, `PreToolUse`, `SessionEnd`. **Verificato contro Claude
  Code vero**, non più solo con input finti: scrive `mode`, `reason`, `ts`,
  `session_id`, `cwd`.
- `io.github.meobob.ccmode.sdPlugin/` — copiato in `~/.config/opendeck/plugins/`,
  registrato da OpenDeck, processo `node plugin.mjs` attivo. **Verificato
  end-to-end sul deck fisico**: `auto` → ambra AUTO, `default` → rosso MANUAL.
- Regole udev `40-opendeck-akp03.rules` in `/etc/udev/rules.d/`. Contengono
  `0300:3002` sia in sezione `usb` sia in sezione `hidraw`.
- Catena completa dimostrata: Shift+Tab → messaggio → hook → `cc-mode.json` →
  polling del plugin → `setImage` → il tasto cambia colore.
- `scripts/check.sh` **v2** — riscritta, tutti i difetti della v1 corretti.
- `README.md` aggiornato (sezione "verificato", limiti 4 e 5 nuovi, nota Wayland).
- `LAYOUT.md` + `keys/` con 17 icone — layout progettato, **non ancora
  configurato sul deck**.

## Percorsi reali di questa macchina

Da non riscoprire. Nessuno di questi era scritto nei documenti.

```
cartella plugin OpenDeck   ~/.config/opendeck/plugins
profili                    ~/.config/opendeck/profiles/n3-4250D2784745/Default.json
indice profili             ~/.config/opendeck/profiles/n3-4250D2784745.json
immagini dei tasti         ~/.config/opendeck/images/n3-4250D2784745/Default/
log principale OpenDeck    ~/.local/share/opendeck/logs/opendeck.log
log per-plugin (OpenDeck)  ~/.local/share/opendeck/logs/plugins/*.log   ← vuoto per il nostro
log del nostro plugin      ~/.config/opendeck/plugins/io.github.meobob.ccmode.sdPlugin/plugin.log
icone dei tasti (sorgenti) ~/dev/claude-mode-deck/keys/{1-guida,2-contesto,3-regolazioni}
```

`n3-4250D2784745` è l'ID del deck; il prefisso `n3` viene dal `DeviceNamespace`
dichiarato nel manifest del plugin akp03.

Il plugin indicatore scrive il proprio log **dentro la sua cartella**
(`LOG_FILE` = `join(HERE, "plugin.log")` in `plugin.mjs`), non nella cartella log
di OpenDeck. Quest'ultima contiene un file col nostro nome ma resta **vuoto**,
perché il plugin non usa stdout/stderr. Il rischio è guardare nell'altro e
concludere che il plugin non parte.

---

# Verbale — sessione installazione (14 agosto, mattina)

## Cosa ha funzionato senza intoppi

- Rilevamento hardware: `0300:3002` visto da `lsusb` al primo colpo
- Node 22 da NodeSource, metodo `nodistro`: nessun problema
- OpenDeck `.deb` su base noble: nessuna dipendenza mancante
- `install-hook.sh`: backup, merge in `settings.json`, prova a vuoto — tutto ok
- Regole udev: il deck ha funzionato subito dopo ricollegamento e riavvio

## Cosa non ha funzionato, e perché

### 1. `sudo` è inutilizzabile da dentro Claude Code — il problema principale

Non c'è tty, quindi `sudo` non può leggere la password. Nessuna via d'uscita:

- `sudo -n true` → `è necessaria una password`
- `! sudo -v` (prefisso bang di Claude Code) → `è richiesto un terminale per
  leggere la password`
- nessun helper askpass installato (e installarne uno richiede `sudo`: circolo
  chiuso)
- `pkexec` esiste con `DISPLAY=:0`, ma i comandi di INSTALL.md con le pipe
  (`curl | sudo gpg`, `echo | sudo tee`) non si traducono sotto `pkexec`

**Conseguenza operativa: ogni comando con `sudo` va eseguito dall'utente in un
terminale vero.** Le fasi 1, 2 e la parte udev della 3 sono di fatto `[UTENTE]`.
Metterlo in conto fin dall'inizio la prossima volta.

### 2. Node 22 c'era, ma nel posto sbagliato

`check.sh` v1 mostrava `[OK] node v22.22.3 in ~/.local/bin/node`. Verde
fuorviante: `/usr/bin/node` era **v18.19.1** (pacchetto Ubuntu). OpenDeck
lanciato dal menu grafico avrebbe pescato il v18 e il plugin sarebbe morto sul
`WebSocket` globale. La v1 avvisava solo per i node provenienti da `~/.nvm`; un
tarball estratto in `~/.local` passava inosservato. **Corretto nella v2.**

`~/.local/node22` è un tarball estratto a mano (giu 2026) con dentro solo
`corepack` e `npm`: nessun pacchetto installato dall'utente, niente ci dipende.
Lasciato dov'è. Ora convivono due Node 22: v22.22.3 nella shell interattiva,
v22.23.2 in `/usr/bin` per OpenDeck.

### 3. Il conflitto `dpkg` previsto non si è verificato

INSTALL.md prevede un conflitto con `libnode-dev` e dà un rimedio. Su questa
macchina `libnode-dev` non era installato: c'erano `nodejs`, `nodejs-doc` e
`libnode109`. `apt` ha rimosso i tre e installato NodeSource **senza chiedere
nulla**. Rimosso anche `node-acorn` (unico dipendente), senza conseguenze.

### 4. Chiudere la finestra di OpenDeck NON lo riavvia — costato una diagnosi intera

Dopo aver copiato il plugin, l'azione *Permission mode* non compariva fra quelle
assegnabili. Sospetto iniziale sbagliato: il manifest (al nostro manca il campo
`Description`, presente in entrambi i plugin funzionanti).

La causa vera, trovata guardando i processi:

```
/usr/bin/opendeck   PID 3073517   avviato 16:04:04   ancora vivo
plugin copiato                    16:18:21
PID 3099742         avviato 16:19:12   [opendeck] <defunct>
```

OpenDeck resta in esecuzione nella tray quando chiudi la finestra. Rilanciarlo
crea un processo che rileva l'istanza esistente, esce lasciando uno zombie, e
riporta in primo piano la vecchia finestra — **con la lista dei plugin letta
all'avvio precedente**. L'icona del plugin si vede (letta dal disco), le azioni
no (vengono dal manifest caricato all'avvio).

**Serve un'uscita vera dalla tray (Quit), oppure `kill <PID>`.** Il
`Description` mancante era un falso indiziato: irrilevante. **La v2 di
`check.sh` ora rileva da sola questa condizione.**

### 5. `willAppear` non arriva quando trascini l'azione su un tasto

Appena messa l'azione sul tasto restava `?` (immagine di default del manifest)
benché il plugin avesse già letto `auto`.

Isolato senza toccare il codice: **premendo il tasto** diventava ambra AUTO. Il
gestore `keyDown` fa lo stesso lavoro del `willAppear` ma per un percorso
diverso, quindi il filtro sull'UUID e `setImage` funzionano — il buco è solo in
`willAppear`.

**Al riavvio di OpenDeck il tasto si dipinge da solo.** Il problema riguarda
esclusivamente il primo drag-and-drop: capita una volta per tasto, la cura è
premerlo. Nell'uso quotidiano non si incontra.

Effetto collaterale utile: `paint()` registra il contesto in `contexts`. Un tasto
mai raggiunto da `willAppear` non verrebbe mai ridipinto da `paintAll`; una
pressione lo registra e da lì in poi segue i cambi di modalità.

### 6. Tre difetti in `check.sh` v1 — tutti corretti nella v2

- **Falsi negativi sui plugin.** `[NO] Plugin akp03 non risulta installato` con i
  plugin perfettamente funzionanti. Causa: `set -o pipefail` + `grep -q`, che
  esce appena trova la corrispondenza, manda `SIGPIPE` al `while` a monte e fa
  uscire la pipeline con 141. **Precisazione emersa poi:** era una corsa **non
  deterministica** — 4 `[OK]` e 6 `[NO]` su 10 esecuzioni identiche — e si
  innescava solo con due cartelle candidate.
- **Discovery ingannata dalla cartella dei log**: `~/.local/share/opendeck/logs/
  plugins` corrispondeva al pattern. La v2 accetta solo cartelle che contengono
  `*.sdPlugin`.
- **Controllo Node sul PATH invece che su `/usr/bin`**: la v2 controlla entrambi
  gli interpreti e **prova davvero la classe `WebSocket`** invece di dedurla dal
  numero di versione.

## Comandi che sono serviti e che nei documenti non c'erano

```bash
# Capire se sudo è utilizzabile prima di tentare qualsiasi cosa
sudo -n true

# Verificare il node che conta davvero, non quello del PATH
/usr/bin/node --version
/usr/bin/node -e 'console.log(typeof WebSocket === "function" ? "ok" : "ASSENTE")'

# Valutare l'impatto della sostituzione di nodejs prima di eseguirla
apt-cache rdepends --installed nodejs
apt-cache rdepends --installed libnode109

# Scoprire che OpenDeck non è stato riavviato davvero — il comando decisivo
ps -eo pid,lstart,etime,cmd | grep '[o]pendeck'

# Log di OpenDeck: conferma la registrazione dei plugin
grep -iE 'Registered|error' ~/.local/share/opendeck/logs/opendeck.log

# Confrontare il nostro manifest con quelli dei plugin funzionanti
python3 -c "import json;d=json.load(open('<path>/manifest.json'));[print(k,'=',json.dumps(d[k])[:120]) for k in sorted(d)]"
```

Due correzioni ai comandi di INSTALL.md:

- **Fase 0**, `sudo apt-get install -y usbutils jq`: non è servito, entrambi
  erano già presenti (come `wget` e `curl`).
- **Fase 5**, `cp -r io.github.meobob.ccmode.sdPlugin <PLUGINS_DIR>/`: il percorso è
  relativo alla cartella del progetto. Lanciato dalla home fallisce. Usare il
  percorso assoluto.

---

# Verbale — sessione layout e profili (14 agosto, sera)

## La trappola dei due archivi

Il browser aveva rinominato il download nuovo perché il nome era occupato:

```
claude-mode-deck.zip     36849 bytes  15:12   ← VECCHIO (CONTEXT 1 ago, check.sh v1)
claude-mode-deck_1.zip   88681 bytes  20:04   ← quello buono
```

Seguire l'istruzione alla lettera (`unzip -o claude-mode-deck.zip`) avrebbe
riportato indietro il progetto di due settimane. **Controllare sempre
`unzip -l` prima di `unzip -o`.**

Anche l'archivio giusto conteneva un `CONTEXT.md` costruito sulla versione del
1 agosto: `unzip -o` ha sovrascritto il verbale dell'installazione, recuperato
da una copia messa da parte prima di estrarre. Se un archivio contiene un file
che hai appena aggiornato, mettilo al riparo prima.

## Contenuto di `keys/` — 17 PNG

| Cartella (percorso assoluto sotto `~/dev/claude-mode-deck/keys/`) | PNG | File |
|---|---|---|
| `1-guida` | **5** | `1-voce` `2-modo` `3-stop` `4-rewind` `5-task` |
| `2-contesto` | 6 | `1-storico` `2-cerca` `3-editor` `4-stash` `5-riprendi` `6-a-parte` |
| `3-regolazioni` | 6 | `1-modello` `2-thinking` `3-fast` `4-sfondo` `5-ferma` `6-config` |

La pagina 1 ne ha cinque: il sesto slot è tenuto libero per l'indicatore, con la
posizione da decidere dopo la prova sul campo.

## OpenDeck: profili

- **I profili si raggruppano col prefisso nel nome**, non scegliendo una
  cartella: si crea un profilo chiamato `Claude/1-guida` e la cartella `Claude`
  nasce da sola.
- **Prima i tre profili, poi i tasti di navigazione**: `Switch Profile` deve
  poter puntare a un profilo che esiste già.
- **OpenDeck riscrive i profili durante l'uso, non solo alla chiusura.**
  `Default.json` modificato alle 20:20 con l'app avviata alle 20:17. Quindi si
  può leggere il JSON senza chiudere l'applicazione. Resta vero il contrario:
  **scrivere quei file dall'esterno mentre OpenDeck gira significa perderli** al
  prossimo salvataggio.

## Rimasto in sospeso

- I 3 `Switch Profile` sono assegnati sui tasti ciechi ma **puntano a profili
  che non esistono ancora**.
- Lo **schema JSON di uno slot non è mai stato letto**: la domanda "conviene
  generare i tasti da script o farli a mano nella GUI?" resta senza risposta.
- Il **test degli `Alt`** (`Alt+P`, `Alt+T`, `Alt+O`) non è stato eseguito. È il
  gate della pagina 3: molti terminali si mangiano `Alt` per gli acceleratori
  dei menu. Va fatto **prima** di configurare `3-regolazioni`.

## Limiti noti, da non riscoprire ogni volta

1. L'indicatore si aggiorna al prossimo evento (prompt o tool call), non
   nell'istante in cui premi Shift+Tab. Motivo: gli hook ricevono
   `permission_mode` ma scattano sugli eventi; la status line invece si
   ri-esegue **quando la modalità cambia** ma nel suo JSON la modalità non c'è.
   Trigger senza valore, valore senza trigger.
   **Confermato sul campo.**
2. Un solo file di stato: con più sessioni Claude Code in parallelo vince
   l'ultima che scrive.
3. Il deck manda tasti alla finestra attiva → il terminale deve avere il focus.
4. Invio di tasti sintetici su Wayland: **non rilevante qui** (X11 confermato),
   resta aperto per un'eventuale migrazione.
5. Un tasto appena creato resta `?` finché non lo premi una volta. Sparisce al
   riavvio di OpenDeck.
6. Nessun tasto resta premibile al buio: i tre ciechi sono occupati dalla
   navigazione fra profili.

## Cosa Claude Code ha scoperto di sé stesso

- **Claude Code ricarica `settings.json` a caldo.** Gli hook installati da
  `install-hook.sh` sono diventati attivi nella sessione già in corso, senza
  riavvio: la prova è il `session_id` della sessione corrente comparso in
  `cc-mode.json` un secondo dopo l'installazione.
- L'hook scrive più campi di quanto suggerisse il README: `mode`, `reason`
  (nome dell'evento), `ts`, `session_id`, `cwd`.
- La modalità `auto` è quella in cui gira una sessione che esegue comandi senza
  chiedere conferma a ogni chiamata.

## Prossimi passi non ancora fatti

- [x] ~~Installare e provare tutto sull'hardware~~ — **fatto il 14 ago 2026**
- [x] ~~Aggiornare README.md~~ — **fatto il 14 ago 2026**
- [x] ~~Correggere i difetti di `check.sh`~~ — **fatto**, v2 verificata sul campo
- [x] ~~Progettare il layout~~ — **fatto**, vedi `LAYOUT.md` e `keys/`
- [ ] **Creare i tre profili** `Claude/1-guida`, `Claude/2-contesto`,
      `Claude/3-regolazioni` (i `Switch Profile` già assegnati li aspettano)
- [ ] **Test `Alt+P` / `Alt+T` / `Alt+O`** nel terminale — gate della pagina 3
- [ ] **Leggere lo schema di uno slot** in `Default.json` e decidere
      script-vs-GUI per i 17 tasti
- [ ] Configurare i tasti seguendo `LAYOUT.md`
- [ ] Decidere la posizione dell'indicatore (sesto slot di pagina 1)
- [ ] Mappare le 3 manopole
- [ ] Cambio automatico di profilo sulla finestra del terminale
- [ ] Verificare il plugin AKP03 su Windows (rischio alto)
- [ ] Valutare se aggiungere `Description` al manifest del plugin indicatore:
      non è risultato necessario, ma è l'unico campo che i due plugin
      funzionanti hanno e il nostro no

## Riferimenti utili

- Plugin AKP03: https://github.com/4ndv/opendeck-akp03
- OpenDeck: https://github.com/nekename/OpenDeck
- API OpenAction: https://openaction.amankhanna.me/
- Hook Claude Code: https://code.claude.com/docs/en/hooks
- Scorciatoie Claude Code: https://code.claude.com/docs/en/interactive-mode
