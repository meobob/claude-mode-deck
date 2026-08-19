#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# installa.sh — installa la parte PORTABILE: i due hook e il plugin OpenDeck.
#
# Questo e' il livello 1 del progetto, quello che si puo' promettere: Node,
# nessuna assunzione sull'hardware, funziona su qualunque deck che OpenDeck
# gestisca. Il layout dei tasti e' il livello 2 e sta in `profili-genera.py`,
# che ha assunzioni sue e le verifica per conto proprio.
#
# Controlla TUTTI i prerequisiti prima di toccare qualsiasi cosa, e se qualcuno
# manca li elenca tutti insieme invece di fermarsi al primo: chi installa
# preferisce sapere subito quante cose gli mancano.
#
# Uso:  ./scripts/installa.sh          installa
#       ./scripts/installa.sh --dry    dice cosa farebbe, senza scrivere

set -euo pipefail

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1
[ -n "${1:-}" ] && [ "$DRY" -eq 0 ] && { echo "opzione sconosciuta: $1"; exit 2; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
PLUGIN_SRC="$REPO/io.github.meobob.ccmode.sdPlugin"
CONF="${OPENDECK_CONFIG:-$HOME/.config/opendeck}"
PLUGINS_DIR="$CONF/plugins"

rosso=$'\033[31m'; giallo=$'\033[33m'; verde=$'\033[32m'; fine=$'\033[0m'
say()  { printf '  %s\n' "$*"; }
ok()   { printf '  %s[OK]%s   %s\n' "$verde" "$fine" "$*"; }
warn() { printf '  %s[?]%s    %s\n' "$giallo" "$fine" "$*"; }

PROBLEMI=()
manca() { PROBLEMI+=("$1"); }

printf '\n== Prerequisiti ==\n'

# --- Node con la classe WebSocket ------------------------------------------
# Il criterio NON e' la versione ma la presenza di `WebSocket` globale: il
# plugin parla con OpenDeck via WebSocket e senza quella classe non parte.
# Conta il node che usa OpenDeck, non quello del tuo PATH: OpenDeck viene
# lanciato dalla sessione grafica e di norma risolve /usr/bin/node.
NODE=""
for CAND in /usr/bin/node "$(command -v node 2>/dev/null || true)"; do
	[ -n "$CAND" ] && [ -x "$CAND" ] || continue
	if [ "$("$CAND" -e 'console.log(typeof WebSocket)' 2>/dev/null)" = "function" ]; then
		NODE="$CAND"; break
	fi
done
if [ -n "$NODE" ]; then
	ok "Node con WebSocket: $NODE ($("$NODE" --version))"
	[ "$NODE" != "/usr/bin/node" ] && warn "Non e' /usr/bin/node. OpenDeck, lanciato dal menu grafico, potrebbe risolverne un altro."
else
	manca "Nessun Node con la classe WebSocket globale (serve la 22 o superiore).
       Verifica con:  node -e 'console.log(typeof WebSocket)'   -> deve dire 'function'"
fi

# --- jq, per registrare gli hook in settings.json --------------------------
if command -v jq >/dev/null 2>&1; then
	ok "jq presente"
else
	manca "jq non installato: serve a registrare gli hook in ~/.claude/settings.json.
       Su Debian/Ubuntu:  sudo apt install jq"
fi

# --- cartella plugin di OpenDeck -------------------------------------------
if [ -d "$PLUGINS_DIR" ]; then
	ok "Cartella plugin di OpenDeck: $PLUGINS_DIR"
else
	manca "Cartella plugin non trovata: $PLUGINS_DIR
       Avvia OpenDeck almeno una volta perche' la crei, oppure indica dov'e':
       OPENDECK_CONFIG=/percorso/della/config $0"
fi

# --- OpenDeck deve essere fermo --------------------------------------------
# Copiare il plugin a OpenDeck vivo lascerebbe in esecuzione la versione
# vecchia: la nuova viene letta solo all'avvio.
if pgrep -x opendeck >/dev/null 2>&1; then
	manca "OpenDeck e' in esecuzione: la copia del plugin non avrebbe effetto
       fino al riavvio, e l'elenco dei plugin viene letto all'avvio.
       Esci con Quit dalla tray (chiudere la finestra NON basta), poi rilancia."
else
	ok "OpenDeck non e' in esecuzione"
fi

# --- ~/.claude, cioe' Claude Code installato -------------------------------
if [ -d "$HOME/.claude" ]; then
	ok "Cartella di Claude Code presente"
else
	manca "$HOME/.claude non esiste: Claude Code non e' mai stato avviato su questo utente."
fi

# --- opzionali: si avvisa, non si blocca -----------------------------------
PY="${CC_MODE_PYTHON:-/usr/bin/python3}"
if [ -x "$PY" ] && "$PY" -c 'from Xlib import display, X, XK; from Xlib.ext import xtest' 2>/dev/null; then
	ok "python3-xlib con XTEST: il tasto potra' anche CAMBIARE la modalita'"
else
	warn "python3-xlib assente o senza XTEST (cercato in $PY)."
	warn "  Gli indicatori funzionano lo stesso; premere il tasto della modalita'"
	warn "  non la cambiera'. Su Debian/Ubuntu:  sudo apt install python3-xlib"
fi
if [ -n "${WAYLAND_DISPLAY:-}" ]; then
	warn "Sessione Wayland: XTEST non e' mai stato provato qui. Gli indicatori"
	warn "  funzionano, l'invio di tasti probabilmente no."
fi

# --- verdetto ---------------------------------------------------------------
# In prova a vuoto i problemi si elencano ma si mostra comunque il piano: chi
# guarda vuole sapere sia cosa manca sia cosa succederebbe.
if [ "${#PROBLEMI[@]}" -gt 0 ]; then
	printf '\n%s%s%s %d prerequisito/i manca:\n\n' "$rosso" \
		"$([ "$DRY" -eq 1 ] && echo 'In questo stato l'"'"'installazione si fermerebbe.' || echo 'Non posso installare.')" \
		"$fine" "${#PROBLEMI[@]}"
	for p in "${PROBLEMI[@]}"; do printf '  - %s\n\n' "$p"; done
	[ "$DRY" -eq 0 ] && exit 1
fi

printf '\n== Installazione ==\n'
if [ "$DRY" -eq 1 ]; then
	say "[dry] copierei $PLUGIN_SRC -> $PLUGINS_DIR/"
	say "[dry] poi:  $HERE/install-hook.sh      (hook della modalita')"
	say "[dry] poi:  $HERE/install-activity.sh  (hook dell'attivita')"
	printf '\nProva a vuoto: non ho scritto niente.\n'
	exit 0
fi

DEST="$PLUGINS_DIR/$(basename "$PLUGIN_SRC")"
if [ -d "$DEST" ]; then
	BK="$DEST.bak.$(date +%Y%m%d%H%M%S)"
	cp -r "$DEST" "$BK"
	say "Backup del plugin precedente: $BK"
fi
mkdir -p "$PLUGINS_DIR"
cp -r "$PLUGIN_SRC" "$PLUGINS_DIR/"
rm -f "$DEST/plugin.log"   # il log della macchina di chi ha sviluppato, non serve a nessuno
ok "Plugin copiato in $DEST"

"$HERE/install-hook.sh"
"$HERE/install-activity.sh"

printf '\n%sFatto.%s\n' "$verde" "$fine"
cat <<'FINE'

Ora:
  1. avvia OpenDeck
  2. trascina su un tasto le azioni "Permission mode" e "Activity",
     categoria "Claude Code"
  3. premi ogni tasto una volta: finche' non lo fai resta "?", ed e' un
     limite noto, non un guasto

Questo era il livello 1: gli indicatori, la parte portabile.
Per il layout completo dei tasti e delle manopole c'e' il livello 2, che ha
assunzioni sue e le verifica per conto proprio:

  ./scripts/profili-installa.sh --dry

FINE
