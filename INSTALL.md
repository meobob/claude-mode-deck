# INSTALL.md — procedura di installazione

Documento operativo, pensato per essere eseguito da **Claude Code** nel
terminale, con l'utente presente. Sistema di riferimento: **Linux Mint**
(base Ubuntu), sessione X11.

## Regole per chi esegue

1. **Un passo alla volta.** Alla fine di ogni fase c'è un `check.sh`: lancialo
   e mostra l'esito prima di andare avanti. Se una fase fallisce, fermati e
   riporta l'errore — non tentare percorsi alternativi di iniziativa.
2. **Mostra sempre i comandi con `sudo` prima di eseguirli.** La password la
   digita l'utente. Non usare `--dangerously-skip-permissions` per questa
   sessione: si tocca `apt`, `/etc/apt/sources.list.d/` e `/etc/udev/rules.d/`.
3. **I passi marcati `[UTENTE]` non sono automatizzabili.** Chiedi e aspetta.
4. **Non inventare percorsi.** La cartella dei plugin di OpenDeck va scoperta
   (`check.sh` la cerca) o letta dal pulsante *Open config directory* nelle
   impostazioni di OpenDeck. Non assumerla.
5. Se qualcosa non torna e la documentazione non lo copre, **dillo** invece di
   improvvisare.

---

## Fase 0 — Fotografia iniziale

```bash
./scripts/check.sh
```

Serve `usbutils` per il rilevamento del dispositivo:

```bash
sudo apt-get install -y usbutils jq
```

**Criterio di successo:** in `lsusb` compare `0300:1002` (AKP03E) oppure
`0300:3002` (AKP03E rev. 2). Sono entrambi nella lista dei dispositivi
supportati dal plugin.

**Se non compare nulla:** fermati. È un problema fisico (cavo dati vs cavo di
sola ricarica, porta USB, hub). Non proseguire: tutto il resto è inutile finché
il kernel non vede il dispositivo.

---

## Fase 1 — Node.js 22

Serve al plugin indicatore, che usa la classe `WebSocket` globale (stabile da
Node 22). Se `check.sh` riporta già node ≥ 22 **installato in `/usr/bin`**,
salta questa fase.

> **Attenzione, specifico per Mint:** non usare lo script
> `https://deb.nodesource.com/setup_22.x`. Verifica il nome in codice della
> distro e Mint riporta il proprio (`wilma`, `xia`, …), non quello di Ubuntu.
> Il metodo manuale qui sotto usa il percorso `nodistro`, che non dipende dal
> nome in codice.

> **Attenzione, nvm:** se node arriva da nvm, vive in `~/.nvm` e OpenDeck
> lanciato dal menu grafico potrebbe non trovarlo nel PATH. Per questo scopo
> serve un node in `/usr/bin`.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" \
  | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo apt-get update
sudo apt-get install -y nodejs
node --version
```

**Se `dpkg` protesta** che sta sovrascrivendo file appartenenti a `libnode-dev`:

```bash
sudo apt remove --purge -y libnode-dev nodejs npm
sudo apt-get install -y nodejs
```

**Criterio di successo:** `node --version` ≥ v22, e `command -v node` risponde
`/usr/bin/node`.

---

## Fase 2 — OpenDeck

Serve la versione **2.5.0 o superiore**: è il minimo richiesto dal plugin AKP03.

**Non usare l'AppImage** — il progetto stesso sconsiglia le proprie release
AppImage perché tendono a dare problemi.

**Preferisci il `.deb` al Flatpak.** Col Flatpak il plugin indicatore gira nel
sandbox e deve leggere `~/.claude/cc-state/`: non è verificato se i permessi
di default lo consentano, e potrebbe servire un `flatpak override`. Col `.deb`
il problema non esiste.

`[UTENTE]` Scarica il `.deb` dalle release di
<https://github.com/nekename/OpenDeck>, poi:

```bash
sudo apt install ./OpenDeck_*.deb
opendeck --version 2>/dev/null || true
```

**Se `apt` segnala dipendenze non soddisfatte:** fermati e riporta l'errore
esatto. Su Mint 21 (base jammy) può essere una glibc troppo vecchia per la
build corrente, e in quel caso la strategia cambia.

`[UTENTE]` Avvia OpenDeck almeno una volta, così crea la sua cartella di
configurazione. Poi:

```bash
./scripts/check.sh
```

**Criterio di successo:** `check.sh` trova la cartella plugin.

---

## Fase 3 — Plugin AKP03

`[UTENTE]` Scarica l'archivio dalla release più recente (v0.8.1 al momento in
cui è scritto questo file) di <https://github.com/4ndv/opendeck-akp03>, poi in
OpenDeck: **Plugins → Install from file**.

Questo passaggio è nella GUI e non è automatizzabile.

### Regole udev

Sono separate da quelle installate con OpenDeck, che coprono i dispositivi
Elgato. Senza le regole Ajazz il deck resta invisibile a OpenDeck anche se
`lsusb` lo vede.

```bash
cd /tmp
wget https://raw.githubusercontent.com/4ndv/opendeck-akp03/main/40-opendeck-akp03.rules
head -5 40-opendeck-akp03.rules          # controlla che sia il file giusto, non una pagina HTML
sudo cp 40-opendeck-akp03.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

Se il `wget` restituisce 404, `[UTENTE]` scarica il file dalla pagina del repo:
si chiama `40-opendeck-akp03.rules` ed è nella radice.

`[UTENTE]` Scollega e ricollega fisicamente il deck. Poi riavvia OpenDeck.

```bash
./scripts/check.sh
```

**Criterio di successo:** `[UTENTE]` conferma che in OpenDeck compare il
dispositivo e i tasti si illuminano. **Prova concreta:** assegna a un tasto
qualsiasi azione nativa e verifica che funzioni.

> **Fermati qui e chiedi conferma all'utente prima di proseguire.** Se il deck
> non funziona a questo punto, installare l'indicatore non ha senso: sarebbero
> due problemi mescolati invece di uno.

---

## Fase 4 — Hook di Claude Code

Questa fase è automatizzata e reversibile.

```bash
./scripts/install-hook.sh --dry     # mostra il settings.json risultante
./scripts/install-hook.sh           # esegue
```

Lo script copia l'hook in `~/.claude/hooks/`, ne registra tre
(`UserPromptSubmit`, `PreToolUse`, `SessionEnd`) dentro
`~/.claude/settings.json` facendo prima un backup, e fa una prova a vuoto. È
idempotente: rilanciarlo non duplica nulla. Se `settings.json` non è JSON
valido si rifiuta di scrivere.

`[UTENTE]` In Claude Code, digita `/hooks`: devono comparire i tre hook.

---

## Fase 5 — Plugin indicatore

**La via breve, dal 19/08/2026:** `./scripts/installa.sh` fa tutto — controlla
i prerequisiti, copia il plugin e registra i due hook — e se qualcosa manca si
ferma dicendo cosa e come rimediare. `--dry` mostra il piano senza scrivere.
Il resto di questa fase descrive gli stessi passi a mano.

La cartella plugin è quella che `check.sh` ha trovato. Sostituisci
`<PLUGINS_DIR>` con quel percorso:

```bash
cp -r io.github.meobob.ccmode.sdPlugin <PLUGINS_DIR>/
```

`[UTENTE]` Riavvia OpenDeck. Poi trascina su un tasto le azioni
**Permission mode** e **Activity**, nella categoria *Claude Code*.

**Criterio di successo:** il tasto mostra qualcosa. All'inizio sarà grigio con
un `?` — è corretto: significa che il file di stato non esiste ancora.

---

## Fase 6 — Verifica end-to-end

1. In Claude Code manda un messaggio qualsiasi. Il tasto deve diventare rosso
   con l'ottagono e la scritta MANUAL.
2. Premi Shift+Tab per cambiare modalità, poi **manda un altro messaggio**.
   Il tasto deve aggiornarsi.

Il secondo passo è il punto in cui si tocca con mano il limite noto:
**l'aggiornamento non è istantaneo**. Gli hook scattano sugli eventi, non
quando premi Shift+Tab. Se cambi modalità e non fai nulla, il tasto resta
indietro fino al prossimo prompt o alla prossima chiamata a tool. Non è un bug
da cercare: è come funziona.

Diagnostica:

```bash
./scripts/check.sh                                    # stato complessivo
cat ~/.claude/cc-state/mode/*.json                    # cosa ha scritto l'hook
cat ~/.claude/cc-state/activity/*.json                # idem, per l'attività
tail -20 <PLUGINS_DIR>/io.github.meobob.ccmode.sdPlugin/plugin.log   # cosa ha letto il plugin
```

Questi due file dicono da che parte sta il problema: se il JSON è aggiornato ma
il tasto no, è il plugin; se il JSON è fermo, è l'hook.

---

## Se qualcosa va storto

| Sintomo | Dove guardare |
|---|---|
| Il deck non compare in OpenDeck | regole udev, poi riavvio di OpenDeck dopo il ricollegamento |
| L'azione non è nella lista | il manifest non è stato letto: riavvia OpenDeck, controlla il nome della cartella `io.github.meobob.ccmode.sdPlugin` |
| Il tasto resta grigio col `?` | c'è qualcosa in `~/.claude/cc-state/mode/`? se no, l'hook non è mai partito → `/hooks` in Claude Code |
| Il tasto non si aggiorna mai | `plugin.log`: se è vuoto il plugin non è partito (node non trovato?), se dice "Modalità ->" il problema è a valle |
| Il tasto è indietro di un messaggio | non è un guasto, è il limite descritto sopra |

## Come disinstallare

```bash
# 1. togli le registrazioni: il backup più recente di settings.json è di prima
#    dell'ultima installazione
cp "$(ls -t ~/.claude/settings.json.bak.* | head -1)" ~/.claude/settings.json

# 2. togli hook, stato e plugin
rm -f  ~/.claude/hooks/cc-mode.mjs ~/.claude/hooks/cc-activity.mjs
rm -rf ~/.claude/cc-state
rm -rf <PLUGINS_DIR>/io.github.meobob.ccmode.sdPlugin
```

L'hook dell'attività ha anche un suo comando che toglie solo quello, senza
toccare il resto: `./scripts/install-activity.sh --rimuovi`.
