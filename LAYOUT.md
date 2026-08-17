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

OpenDeck sa passare a un profilo quando la finestra di una certa applicazione
diventa attiva. Vale la pena configurarlo sul tuo terminale: il deck mostra i
tasti di Claude Code solo quando serve, e torna a `Default` quando sei altrove.
Non risolve il vincolo del focus — i tasti vanno comunque alla finestra attiva —
ma almeno smetti di vedere comandi inutili quando sei nel browser.

---

## Pagina 1 — guida (profilo `Claude/1-guida`)

Tasti 1-6, cioe' le due righe con schermo.

| # | Tasto | Azione OpenDeck | Cosa fa | Icona |
|---|---|---|---|---|
| 1 | Voce | Hotkey `Space` | Dettatura. Richiede `/voice tap` attivo | `keys/1-guida/1-voce.png` |
| 2 | Modo | Hotkey `Shift+Tab` | Cicla le modalita' permessi | `2-modo.png` |
| 3 | Stop | Hotkey `Esc` | Interrompe Claude a meta' turno | `3-stop.png` |
| 4 | Rewind | Multi-azione: `Esc`, pausa ~120 ms, `Esc` | Menu rewind (a input vuoto) | `4-rewind.png` |
| 5 | Task | Hotkey `Ctrl+T` | Mostra o nasconde la checklist | `5-task.png` |
| 6 | Stato | Azione *Permission mode* | Mostra la modalita' **e la cicla** se premuto | — |

**Il tasto 2 e il tasto 6 fanno la stessa cosa.** Dal 15 agosto 2026 premere
l'indicatore cicla le modalita' come `Shift+Tab`, quindi il tasto 2 e'
ridondante e il suo slot e' libero. Non e' stato ancora riassegnato: il profilo
non e' stato toccato.

Perche' non si e' invece messo tutto sul tasto 6 impilando due azioni: si e'
provato, e non funziona. Vedi "Multi Action" piu' avanti.

## Pagina 2 — contesto (profilo `Claude/2-contesto`)

| # | Tasto | Azione OpenDeck | Cosa fa |
|---|---|---|---|
| 1 | Storico | Hotkey `Ctrl+O` | Apre il transcript viewer |
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
| 1 | Modello | Hotkey `Alt+P` | Cambia modello senza perdere il prompt |
| 2 | Thinking | Hotkey `Alt+T` | Extended thinking on/off |
| 3 | Fast | Testo `/fast` + Invio | Fast mode on/off |
| 4 | Sfondo | Hotkey `Ctrl+B` | Manda in background il comando in corso |
| 5 | Ferma | Multi-azione: `Ctrl+X` `Ctrl+K`, pausa, di nuovo | Ferma i subagent in background |
| 6 | Config | Testo `/config` + Invio | Impostazioni |

## Manopole

| # | Rotazione | Pressione |
|---|---|---|
| 1 | Freccia su / freccia giu' | `Ctrl+O` (apri il transcript da scorrere) |
| 2 | Volume di sistema | Muto |
| 3 | Zoom del terminale (`Ctrl+Shift++` / `Ctrl+-`) | Zoom originale (`Ctrl+0`) |

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
   la codifica giusta. Nessun rimedio necessario. (`Alt+O` non esiste piu': il
   tasto Fast manda `/fast` + Invio.)
2. **`Ctrl+X Ctrl+K` trasmette, ma il tasto e' incompleto.** I due byte
   arrivano a 2 ms l'uno dall'altro, pero' l'accordo c'e' **una volta sola**,
   mentre per confermare va ripetuto entro 3 secondi. Il tasto fa al massimo
   meta' del lavoro. Da correggere o da togliere.
3. **`Esc Esc` arriva senza pausa: 0,0 ms fra i due.** Il profilo ha un singolo
   `Simulate Input` con `[Key(Escape, Click), Key(Escape, Click)]`, non la
   multi-azione con pausa che questo documento prescriveva. Due Esc nello stesso
   millisecondo hanno buone probabilita' di essere letti come uno solo.

Vincolo confermato per tutti: **il terminale deve avere il focus**. Il deck
manda tasti alla finestra attiva, non a Claude Code in quanto tale.

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
Serve per dare una pausa ai due `Esc` del Rewind. Il riferimento e'
`docs/esempio-multiaction.json`, e `tools/genera-multiaction.py` mostra come e'
stato costruito.

---

## Due tasti esclusi di proposito

`Ctrl+C` e `Ctrl+D` non sono nel layout. `Ctrl+D` esce da Claude Code, e un
tasto fisico grande e comodo che chiude la sessione per sbaglio non e' una buona
idea. `Esc` copre gia' il bisogno di interrompere.
