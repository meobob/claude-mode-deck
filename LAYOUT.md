# LAYOUT.md — i 18 slot dell'AKP03E per Claude Code

Tre pagine, una per ogni momento: **guidare**, **guardare indietro**, **regolare**.
Tutte le scorciatoie sono verificate sulla documentazione ufficiale di Claude
Code (`interactive-mode`), non sulla memoria.

Le icone stanno in `keys/`, una cartella per pagina, gia' colorate per pagina:
verde-acqua, viola, grigio. Rigenerabili con `python3 make_key_icons.py`.

## La forma reale del dispositivo

**Correzione a una cosa che avevo dato per buona.** La scheda prodotto descrive
i tre tasti in basso come "tasti di cambio scena/pagina". Verificato sul campo
il 14 agosto 2026: **sotto OpenDeck sono tasti normali come gli altri**. Quella
descrizione racconta cosa ne fa il software ufficiale Ajazz, non un vincolo
dell'hardware.

Quindi il dispositivo e':

```
[ 1 ] [ 2 ] [ 3 ]     riga 1 — con schermo
[ 4 ] [ 5 ] [ 6 ]     riga 2 — con schermo
[ 7 ] [ 8 ] [ 9 ]     riga 3 — SENZA schermo
( A ) ( B ) ( C )     3 manopole
```

Nove tasti, sei con schermo. Le pagine non sono gratis: vanno comprate
spendendo tasti.

## Configurazione scelta: tre profili

I tre tasti ciechi (7, 8, 9) fanno `Switch Profile`, **identici in tutti e tre i
profili**, cosi' la navigazione e' sempre nello stesso posto sotto le dita:

| Tasto | Va a |
|---|---|
| 7 (basso sinistra) | pagina 1 — guida |
| 8 (basso centro) | pagina 2 — contesto |
| 9 (basso destra) | pagina 3 — regolazioni |

Costo: 9 assegnazioni solo per navigare. Resa: 18 slot con icona.

Il prezzo vero non e' quello. E' che **nessun tasto resta premibile senza
guardare**: i tre ciechi sono gli unici che si trovano al tatto, e sono occupati
dalla navigazione. `Esc` e `Shift+Tab` finiscono su tasti con schermo, e per
premerli devi guardare. Se dopo qualche giorno questo pesa, la via d'uscita e'
passare a due profili e liberare un tasto cieco.

### Nomi dei profili

OpenDeck raggruppa i profili in cartelle se prefissi il nome con
`cartella/nome`. Consigliati:

```
Claude/1-guida
Claude/2-contesto
Claude/3-regolazioni
```

**Crea prima i tre profili, poi assegna i tasti di navigazione.** `Switch
Profile` deve poter puntare a un profilo che esiste gia'.

### Cambio automatico di profilo

Configurato e provato il 19/08/2026. Non risolve il vincolo del focus — i tasti
vanno comunque alla finestra attiva — ma smetti di vedere comandi inutili
quando sei altrove.

**Non sta nelle impostazioni**, dove verrebbe naturale cercarlo. Sta nella
gestione profili: menu a tendina del profilo **in alto a destra** -> ultima
voce **`Edit...`** -> nella finestra che si apre, il pulsante **`Application
profiles`**. Lì si scelgono `Select application...` e `Select profile...`.

Tre cose che non si indovinano:

1. **L'elenco delle applicazioni non e' quello delle applicazioni installate**,
   ma quello delle finestre che OpenDeck ha visto diventare attive mentre
   girava: controlla il focus ogni 250 ms e lo costruisce strada facendo. Se la
   tua non c'e', dalle il focus e torna indietro.
2. **Il nome registrato e' la classe della finestra, non il processo.**
   gnome-terminal compare come `Gnome-terminal`.
3. **Serve anche un profilo predefinito**, altrimenti funziona in un verso
   solo: entrando sul terminale il deck passa a `Claude/1-guida`, uscendo resta
   com'e'. Si imposta nello stesso pannello, voce `Default profile`. Qui e' un
   profilo vuoto.

Il file e' `~/.config/opendeck/applications.json`, nella forma
applicazione -> deck -> profilo, con **un profilo solo per applicazione**:

```json
{
  "Gnome-terminal":   { "n3-4250D2784745": "Claude/1-guida" },
  "opendeck_default": { "n3-4250D2784745": "5" }
}
```

Il guadagno vero non e' risparmiare comandi inutili: e' che il deck diventa un
**indicatore del focus**. Se mostra i tasti di Claude, il focus e' sul
terminale — la condizione da cui dipende ogni tasto di questo progetto.

Due effetti collaterali da conoscere. Ogni volta che il terminale riprende il
focus il deck torna a `1-guida`: la pagina su cui eri non viene ricordata. E il
profilo predefinito, essendo vuoto, non ha i tre tasti di navigazione, quindi
da lì si torna indietro solo ridando il focus al terminale.

---

## Pagina 1 — guida (profilo `Claude/1-guida`)

Tasti 1-6, cioe' le due righe con schermo.

| # | Tasto | Azione OpenDeck | Cosa fa | Icona |
|---|---|---|---|---|
| 1 | Voce | Hotkey `Space` | Dettatura. Richiede `/voice tap` attivo | `keys/1-guida/1-voce.png` |
| 2 | — | *slot vuoto nel profilo* | Era `Shift+Tab`, oggi ridondante col tasto 6 | `2-modo.png`, inutilizzata |
| 3 | Stop | Hotkey `Esc` | Interrompe Claude a meta' turno | `3-stop.png` |
| 4 | Rewind | `Simulate Input`: `Esc` su `down`, `Esc` su `up` | Menu rewind (a input vuoto). Basta un tocco | `4-rewind.png` |
| 5 | Task | Hotkey `Ctrl+T` | Mostra o nasconde la checklist | `5-task.png` |
| 6 | Stato | Azione *Permission mode* | Mostra la modalita' **e la cicla** se premuto | — |

**Il tasto 2 e il tasto 6 facevano la stessa cosa.** Dal 15 agosto 2026 premere
l'indicatore cicla le modalita' come `Shift+Tab`, quindi il tasto 2 e' diventato
ridondante ed e' stato **svuotato**: nel profilo `keys[1]` e' `null`. Lo slot e'
libero e non e' stato ancora riassegnato.

Verificato il 18/08/2026 rileggendo il profilo. E' anche il motivo per cui torna
il conto dei 17 tasti che trasmettono: **cinque** in pagina 1, non sei, piu' sei
e sei.

Perche' non si e' invece messo tutto sul tasto 6 impilando due azioni: si e'
provato, e non funziona. Vedi "Multi Action" piu' avanti.

## Pagina 2 — contesto (profilo `Claude/2-contesto`)

| # | Tasto | Azione OpenDeck | Cosa fa |
|---|---|---|---|
| 1 | Storico | Hotkey `Ctrl+O` | Apre **e chiude** il transcript viewer: e' un interruttore |
| 2 | Cerca | Hotkey `Ctrl+R` | Ricerca nella cronologia dei prompt |
| 3 | Editor | Hotkey `Ctrl+G` | Apre il prompt nell'editor esterno |
| 4 | Stash | Hotkey `Ctrl+S` | Mette da parte il prompt; ripremuto lo ripristina |
| 5 | Riprendi | Testo `/resume` + Invio | Riapre una sessione precedente |
| 6 | A parte | Testo `/btw ` **senza** Invio | Domanda laterale: scrivi tu il resto |

Il tasto 6 non manda Invio di proposito: `/btw` da solo riapre l'ultima
risposta, mentre quasi sempre vuoi scriverci dietro una domanda.

## Pagina 3 — regolazioni (profilo `Claude/3-regolazioni`)

| # | Tasto | Azione OpenDeck | Cosa fa |
|---|---|---|---|
| 1 | Modello | Hotkey `Alt+P` | **Apre** il selettore dei modelli: scegli e confermi con Invio |
| 2 | Thinking | Hotkey `Alt+T` | **Apre** la finestra del thinking: scegli e confermi con Invio |
| 3 | Fast | Testo `/fast` + Invio | Fast mode on/off |
| 4 | Sfondo | Hotkey `Ctrl+B` | Manda in background il comando in corso. **Solo mentre un task gira** |
| 5 | Ferma | `Simulate Input`: `Ctrl+X Ctrl+K` su `down`, di nuovo su `up` | Ferma i subagent (il secondo colpo e' la conferma) |
| 6 | Config | Testo `/config` + Invio | Impostazioni. **Provarlo non e' gratis**, vedi sotto |

**Il tasto Config non si prova a cuor leggero.** Apre un'interfaccia dove si
toccano impostazioni **persistenti**, e basta un Invio di troppo per cambiarne
una senza accorgersene: la prova del 18/08/2026 ha lasciato
`autoCompactEnabled` su `false` in `~/.claude/settings.json`, ed e' stato
necessario rimetterlo a posto a mano. **Chi rifara' TBD-7 deve saperlo prima,
non dopo.** Due dettagli che rendono facile l'incidente: il pannello **non** si
chiude al primo `Esc` se il campo di ricerca ha il focus, e la voce selezionata
si commuta con Invio.

**`Ctrl+B` e' legato al contesto `Task`, non a `Chat`.** Fuori da un task in
corso non e' un tasto rotto: e' un tasto che in quel momento non esiste.
Provarlo a vuoto non dimostra niente.

## Manopole

Uguali su tutte e tre le pagine, per la stessa ragione dei tre tasti ciechi:
restano sotto le dita qualunque pagina sia attiva.

**Installate il 19/08/2026** con `scripts/manopole-installa.py` e provate tutte
e tre sul deck: funzionano. Lo script di suo non scrive niente — mostra e basta
— e con `--scrivi` pretende OpenDeck fermo e fa il backup dei tre profili.

| # | Rotazione | Pressione |
|---|---|---|
| 1 | Freccia su / freccia giu' | `Ctrl+O` (apri il transcript da scorrere) |
| 2 | Volume di sistema, con `pactl` | Muto, con `pactl` |
| 3 | Zoom del terminale (`Ctrl` + `+` / `Ctrl` + `-`) | Zoom originale (`Ctrl+0`) |

A differenza dei tasti, le manopole **non hanno schermo**: non c'e' il `?` da
sbloccare con una prima pressione descritto nei limiti noti.

**Schema dello slot**, letto il 19/08/2026 configurandone una nella GUI invece
di dedurlo: `sliders` e' una lista di **tre**, l'indice e' la posizione
(0 = sinistra), e l'oggetto ha la stessa forma di quello di un tasto
(`action`, `children`, `context`, `current_state`, `settings`, `states`).
Cambia il contesto: i tasti sono `Keypad.<posizione>.<stato>`, le manopole
**`Encoder.<posizione>.<stato>`**.

I campi delle impostazioni stanno nei property inspector delle azioni, dentro
`plugins/com.amansprojects.starterpack.sdPlugin/propertyInspector/`:
`Simulate Input` ha `down`, `up`, `anticlockwise`, `clockwise`; `Run Command`
ha `down`, `up`, `rotate`, `file`, `show`. Su encoder `down` e' la **pressione**
("Dial down" nella GUI). Differenza che conta: **Simulate Input ha una casella
per verso di rotazione, Run Command ne ha una sola**, `rotate`, dove `%d`
diventa il numero di scatti — negativo in senso antiorario.

I nomi dei tasti accettati (`UpArrow`, `DownArrow`, `Control`, `Unicode`, e le
azioni `Press`, `Release`, `Click`) si leggono nel binario del plugin. Provati
sul deck il 19/08: la sintassi passa, e `Key(Unicode('+'), Click)` produce il
keysym `plus` sulla tastiera italiana.

**Lo zoom non e' `Ctrl+Shift++`**, come diceva questo documento fino al
19/08/2026. Le scorciatoie in vigore qui sono `<Control>plus`,
`<Control>minus`, `<Control>0`, lette da `gsettings` sotto
`org.gnome.Terminal.Legacy.Keybindings` — schema rilocabile, serve il percorso
`/org/gnome/terminal/legacy/keybindings/` — e senza personalizzazioni in
`dconf`. Sulla tastiera italiana il `+` e' gia' senza maiuscolo. Provate il
19/08 mandandole con XTEST, cioe' la stessa strada del deck: lo zoom risponde e
torna al valore di partenza. Le gestisce **gnome-terminal, non Claude Code**,
quindi valgono anche mentre Claude Code lavora. Conseguenza da tenere a mente:
`Ctrl+-` in Claude Code sarebbe `chat:undo`, ma se il terminale se lo prende
prima non lo raggiungi — dentro Claude Code non e' stato provato.

**Per il volume non esiste un'azione pronta.** Il plugin starterpack ha cinque
azioni in tutto — Run Command, Open URL, Simulate Input, Switch Profile,
Device Brightness — e nessuna tocca il volume di sistema. Si passa da
`Run Command` con `pactl`, verificato il 19/08 su questa macchina alzando,
riabbassando e ripristinando il valore grezzo di partenza:

```
pactl set-sink-volume @DEFAULT_SINK@ +5%
pactl set-sink-volume @DEFAULT_SINK@ -5%
pactl set-sink-mute   @DEFAULT_SINK@ toggle
```

La manopola 1 fa due cose diverse a seconda di dove sei: nel transcript viewer
scorre, nel prompt naviga la cronologia. Non e' un difetto — sono le frecce che
si comportano cosi'.

Le scorciatoie di zoom della manopola 3 dipendono dall'emulatore di terminale,
non da Claude Code: verifica quali sono le tue.

---

## Due strade per configurarlo

**A — a mano nella GUI.** Diciassette assegnazioni piu' nove di navigazione.
Nessun rischio, nessuna sorpresa, mezz'ora abbondante.

**B — generando il profilo.** OpenDeck salva i profili come **file JSON nella
cartella di configurazione**, con `.temp` e `.bak` per il recupero. In teoria si
puo' scrivere il profilo da uno script invece che a mano.

**Aggiornamento del 15 agosto 2026: la strada B e' stata percorsa e lo schema
adesso e' noto.** I tre profili in uso sono stati generati da script, e OpenDeck
li ha accettati e riscritti senza cambiarne il contenuto. Non e' piu' "in
teoria".

La forma, ricavata dai file veri:

```
{
  "infobars": [],
  "keys": [ 9 slot ],          // uno per tasto, in ordine di posizione
  "sliders": [null, null, null] // le manopole
}
```

Ogni slot e' **un oggetto con una sola azione** — non un array di azioni
impilabili — oppure `null` se il tasto e' vuoto. I campi che contano sono
`action` (una copia del manifest dell'azione), `settings` (la configurazione
vera, per esempio la stringa RON del tasto da mandare), `states` (cosa disegna)
e `context`, nella forma `Keypad.<posizione>.<indice>`. Un `Multi Action` mette
i suoi figli in `children`, e i figli prendono indice 1, 2, …

### Le icone personalizzate

Non stanno nel profilo. Il campo `image` di uno stato diventa il **nome** di un
file, e il file vive in un albero parallelo:

```
~/.config/opendeck/images/<device>/<profilo>/<context>/0.png
```

quindi per l'icona del tasto 1 della pagina guida:

```
images/n3-4250D2784745/Claude/1-guida/Keypad.0.0/0.png     e  "image": "0.png"
```

Lo `0` e' l'indice dello stato, non un nome arbitrario. La regola e' stata
ricavata da come OpenDeck salva le immagini che il plugin gli manda con
`setImage`, e poi applicata alle 16 icone dei tasti: OpenDeck le ha rilette,
riscritte e tenute.

Conseguenza pratica: **chi ripristina un profilo deve ripristinare anche le
immagini**, altrimenti i tasti restano senza icona. In `backup/` le due cose
stanno insieme apposta.

I tre tasti in basso non hanno schermo: assegnare loro un'icona non serve a
niente.

Restano due regole non negoziabili:

1. **Esci davvero da OpenDeck prima di scrivere** (Quit dalla tray). Tiene i
   profili in memoria e li riscrive: modificarli mentre gira significa perderli.
   Vale anche per le cancellazioni — un file cancellato ricompare all'uscita.
2. **Backup prima.** In `backup/` c'e' la copia dei profili in uso.

---

## Cosa e' stato verificato davvero

Il 15 agosto 2026 i 17 tasti sono stati catturati uno per uno in un terminale
neutro, registrando i byte con l'orario (`tools/cattura-tasti.py`).
**Diciassette su diciassette mandano esattamente i byte previsti.**

Tre previsioni di questo documento sono state smentite o corrette:

1. **`Alt+P` e `Alt+T` passano.** Erano dati per probabili vittime degli
   acceleratori dei menu del terminale: arrivano invece come `ESC p` / `ESC t`,
   la codifica giusta. Nessun rimedio necessario.
2. **`Ctrl+X Ctrl+K` trasmetteva, ma il tasto era incompleto.** I due byte
   arrivavano a 2 ms l'uno dall'altro, pero' l'accordo c'era **una volta sola**,
   mentre per confermare va ripetuto entro 3 secondi: il tasto faceva meta' del
   lavoro. **Corretto il 16/08, misurato il 18/08** — vedi sotto.
3. **`Esc Esc` arrivava senza pausa: 0,0 ms fra i due.** Il profilo aveva un
   singolo `Simulate Input` con `[Key(Escape, Click), Key(Escape, Click)]`, non
   la multi-azione con pausa che questo documento prescriveva. Due Esc nello
   stesso millisecondo hanno buone probabilita' di essere letti come uno solo.
   **Corretto il 16/08, misurato il 18/08** — vedi sotto.

Vincolo confermato per tutti: **il terminale deve avere il focus**. Il deck
manda tasti alla finestra attiva, non a Claude Code in quanto tale.

### 18 agosto 2026 — le due correzioni, misurate

Il 16/08 la pausa era stata ottenuta **spostando il secondo colpo su `up`**: un
solo `Simulate Input`, l'azione di `down` alla pressione e quella di `up` al
rilascio, cosi' la pausa diventa il tempo in cui tieni premuto. Scritto e
installato allora, **misurato solo il 18/08** con `tools/cattura-tasti.py`.

- **Rewind**: su 16 pressioni, sempre **due `Esc`**, separati da 64 ms a
  1671 ms, cioe' esattamente quanto tieni premuto. Il menu rewind si apre
  davvero dentro Claude Code e **basta un tocco secco**: tenerlo non serve.
- **Ferma**: **due accordi `Ctrl+X Ctrl+K` distinti** a 78 ms, dentro la
  finestra dei 3 secondi. Claude Code risponde al primo con `Press ctrl+x
  ctrl+k again to stop background agents`: il secondo colpo e' la conferma.
- **Controllo**: `Stop`, che ha solo `down`, tenuto premuto 2 secondi manda
  **un solo `Esc`**. Nessuna ripetizione automatica in gioco, su nessun tasto.

Trappola di lettura, costata una diagnosi sbagliata prima di accorgersene:
`cattura-tasti.py` separa con `---` dopo mezzo secondo di silenzio, e con un
tasto `down`/`up` quel taglio **non** cade fra una pressione e l'altra. Conta i
byte, non i gruppi: un tasto `down`/`up` ne produce sempre un numero **pari**.

### 18 agosto 2026 — prova semantica (TBD-7)

Che i byte partano non dice che Claude Code reagisca: sono due affermazioni
diverse. Il secondo tratto e' stato provato mandando gli stessi byte a sessioni
`claude` usa-e-getta dentro uno pseudo-terminale, e rileggendo lo schermo.

Fanno quello che questo documento promette: `Ctrl+O` (interruttore del
transcript), `Ctrl+R` (ricerca nei prompt), `Ctrl+G` (editor esterno,
verificato con un editor finto che scriveva un marcatore nel file), `Ctrl+S`
(stash **e** ripristino), `/resume`, `/btw ` (scrive e **non** manda), `Alt+P`,
`Alt+T`, `/config`, `Ctrl+X Ctrl+K`. `/fast` commuta davvero, provato a mano.

Restano con riserva: `Ctrl+T` non dice niente in una sessione senza checklist,
`Ctrl+B` niente senza un task in corso, e `Voce` (`Space`) non e' stato provato
per non far partire la dettatura.

**`Alt+O` esiste ancora**, al contrario di quanto diceva il punto 1:
`~/.claude/keybindings.json` lo lega a `chat:fastMode`. Provato tre volte a
campo pulito, pero', **non produce nessun cambiamento visibile**. La
scorciatoia c'e', l'effetto non si vede: finche' non si capisce perche', il
tasto Fast resta su `/fast` + Invio.

Nota di metodo: `~/.claude/keybindings.json` dice **cos'e' legato**, non **cosa
succede**. `Ctrl+L` risulta legato a `chat:clearInput` e non svuota il campo.
Per questo servono tutte e due le prove, la cattura dei byte e la prova a
schermo.

## Multi Action: esegue, ma non disegna

OpenDeck ha un contenitore `Multi Action` che esegue piu' azioni in sequenza.
E' la via ovvia per unire due tasti in uno — ed e' stata provata il 15 agosto
2026 su un profilo usa-e-getta, con tre varianti: indicatore dopo il tasto,
indicatore prima, indicatore da solo.

**Tutte e tre hanno mostrato l'icona del contenitore.** La sequenza viene
eseguita davvero (la modalita' cambiava), ma il contenitore si tiene la faccia
del tasto e l'azione che sta dentro non disegna piu'. Per un'azione il cui
unico scopo e' *mostrare* qualcosa, e' il compromesso peggiore: un tasto che
agisce e smette di dirti dove sei.

Per questo la pressione che cicla la modalita' e' finita **dentro il plugin**
(`sendkeys.py`), che lascia una sola azione sullo slot.

Quello che si e' imparato resta comunque utile: **so scrivere un multi-action
che OpenDeck accetta senza correggerlo**, contesti dei figli compresi
(`Keypad.<posizione>.<indice>`, il contenitore e' `.0` e i figli `.1`, `.2`…).
Per il Rewind non e' servito — la pausa si e' ottenuta con `down`/`up`, senza
contenitore — ma resta pronto se un giorno servira' una sequenza vera. Il
riferimento e'
`docs/esempio-multiaction.json`, e `tools/genera-multiaction.py` mostra come e'
stato costruito.

---

## Due tasti esclusi di proposito

`Ctrl+C` e `Ctrl+D` non sono nel layout. `Ctrl+D` esce da Claude Code, e un
tasto fisico grande e comodo che chiude la sessione per sbaglio non e' una buona
idea. `Esc` copre gia' il bisogno di interrompere.
