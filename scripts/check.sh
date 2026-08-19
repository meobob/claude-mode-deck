#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# check.sh v2 — diagnostica in SOLA LETTURA per il setup Claude Code Mode.
#
# Non installa, non modifica, non chiede sudo. Rilanciabile quante volte vuoi.
# Uscita: 0 sempre. Il valore sta nell'output, non nel codice di ritorno.
#
# CORREZIONI rispetto alla v1, tutte da difetti trovati sul campo il 14/08/2026:
#  1. Falsi negativi sui plugin. La v1 usava `... | grep -q`, che esce appena
#     trova la corrispondenza: chiudendo la pipe in anticipo mandava SIGPIPE al
#     ciclo a monte, e con `pipefail` la pipeline usciva 141 -> [NO]. Era il
#     successo del grep a far fallire il test. Si manifesta solo con piu' di una
#     cartella candidata ed e' NON DETERMINISTICO (una corsa fra scrittore e
#     lettore): 4 [OK] e 6 [NO] su 10 esecuzioni identiche. Qui non ci sono piu'
#     pipe in quei controlli.
#  2. Doppia cartella "plugins". La v1 accettava qualsiasi directory chiamata
#     `plugins` sotto un percorso contenente "opendeck": pescava anche
#     `~/.local/share/opendeck/logs/plugins`, che contiene file `.log`. Ed era
#     proprio la seconda cartella a innescare il bug 1. Ora una cartella e'
#     valida solo se contiene almeno una sottocartella `*.sdPlugin`.
#  3. Node controllato solo via PATH. La v1 dava [OK] a un Node 22 in
#     `~/.local/bin` mentre `/usr/bin/node` era v18: OpenDeck, lanciato dalla
#     sessione grafica, avrebbe pescato il v18 e il plugin sarebbe morto sul
#     WebSocket. Ora si controlla ogni interprete candidato e si verifica la
#     presenza REALE della classe WebSocket, non il numero di versione.
#  4. NUOVO: rileva se OpenDeck e' in esecuzione da PRIMA che i plugin fossero
#     copiati. Chiudere la finestra non lo riavvia (resta nella tray) e la lista
#     dei plugin resta ferma all'avvio precedente.

set -uo pipefail

ok()   { printf '  \033[32m[OK]\033[0m   %s\n' "$*"; }
no()   { printf '  \033[31m[NO]\033[0m   %s\n' "$*"; }
warn() { printf '  \033[33m[?]\033[0m    %s\n' "$*"; }
info() { printf '         %s\n' "$*"; }
head_() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

# --------------------------------------------------------------- 1. sistema --
head_ "Sistema"
if [ -r /etc/os-release ]; then
	. /etc/os-release
	info "Distro: ${PRETTY_NAME:-sconosciuta}"
fi
[ -r /etc/upstream-release/lsb-release ] && \
	info "Base Ubuntu: $(grep DISTRIB_CODENAME /etc/upstream-release/lsb-release | cut -d= -f2)"
info "Sessione grafica: ${XDG_SESSION_TYPE:-sconosciuta}"
if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
	warn "Wayland: l'invio di tasti sintetici (azione Hotkey) potrebbe non funzionare."
fi

# ------------------------------------------------------------- 2. hardware --
head_ "Dispositivo AKP03E"
if command -v lsusb >/dev/null 2>&1; then
	FOUND=$(lsusb | grep -iE '0300:(1001|1002|1003|3002|3003)' || true)
	if [ -n "$FOUND" ]; then
		ok "Dispositivo rilevato:"
		printf '         %s\n' "$FOUND"
	else
		no "Nessun dispositivo Ajazz 0300:xxxx trovato in lsusb."
		info "Elenco completo per controllo manuale:"
		lsusb | sed 's/^/         /'
	fi
else
	warn "lsusb non disponibile (pacchetto usbutils)."
fi

head_ "Regole udev"
if ls /etc/udev/rules.d/ 2>/dev/null | grep -qi akp03; then
	ok "Regole akp03 presenti: $(ls /etc/udev/rules.d/ | grep -i akp03 | tr '\n' ' ')"
else
	no "Nessuna regola udev akp03 in /etc/udev/rules.d/"
fi
if ls /etc/udev/rules.d/ 2>/dev/null | grep -qi streamdeck; then
	info "Presenti anche regole streamdeck (Elgato): $(ls /etc/udev/rules.d/ | grep -i streamdeck | tr '\n' ' ')"
fi

# ----------------------------------------------------------------- 3. node --
# Il criterio vero non e' "node >= 22 nel PATH": e' che l'interprete usato da
# OpenDeck esponga la classe WebSocket. La versione e' un indizio, questa e' la
# prova. Ogni candidato viene controllato separatamente.
head_ "Node.js"

check_node() {
	local path="$1" label="$2" ver ws
	[ -x "$path" ] || return 1
	ver=$("$path" --version 2>/dev/null)
	ws=$("$path" -e 'process.stdout.write(typeof WebSocket === "function" ? "si" : "no")' 2>/dev/null)
	if [ "$ws" = "si" ]; then
		ok "$label: $path $ver — WebSocket disponibile"
	else
		no "$label: $path $ver — WebSocket ASSENTE (serve Node 22+)"
	fi
	return 0
}

# /usr/bin/node e' quello che conta: e' l'interprete che di norma risolve
# un'applicazione lanciata dal menu grafico.
if ! check_node /usr/bin/node "di sistema"; then
	no "/usr/bin/node non esiste."
	info "OpenDeck lanciato dal menu grafico potrebbe non trovare alcun node."
fi

PATH_NODE=$(command -v node 2>/dev/null || true)
if [ -n "$PATH_NODE" ] && [ "$PATH_NODE" != "/usr/bin/node" ]; then
	check_node "$PATH_NODE" "nel PATH della shell" || true
	warn "Nel PATH vince $PATH_NODE, non /usr/bin/node."
	info "Shell e menu grafico possono risolvere due interpreti diversi:"
	info "quello che conta per OpenDeck e' /usr/bin/node."
fi

# ------------------------------------------------------- 3bis. invio tasti --
# Premere l'indicatore cicla la permission mode, e per farlo il plugin manda
# Shift+Tab con `sendkeys.py`, che usa python3-xlib e l'estensione XTEST.
# Se manca, il tasto continua a MOSTRARE la modalita' ma non la cambia piu':
# un guasto silenzioso, che si vede solo qui o in plugin.log.
head_ "Invio tasti (sendkeys.py)"
PY="${CC_MODE_PYTHON:-/usr/bin/python3}"
if [ -x "$PY" ]; then
	ok "Interprete: $PY $("$PY" --version 2>&1 | tr -d '\n')"
	if "$PY" -c 'from Xlib import display, X, XK; from Xlib.ext import xtest' 2>/dev/null; then
		ok "python3-xlib con estensione XTEST disponibile."
	else
		no "python3-xlib assente o senza XTEST: il tasto non potra' cambiare modalita'."
		info "Pacchetto: python3-xlib"
	fi
else
	no "$PY non esiste: il plugin non potra' lanciare sendkeys.py."
	info "Se il tuo python3 sta altrove, imposta CC_MODE_PYTHON."
fi

# --------------------------------------------------------------- 4. opendeck --
head_ "OpenDeck"
# NON si lancia `opendeck --version`: quel flag non esiste e OpenDeck lo
# ignora, quindi il comando AVVIA l'applicazione e non torna mai. Misurato il
# 17/08/2026, a OpenDeck fermo: check.sh appeso a tempo indefinito, OpenDeck
# partito di nascosto — la sua riga di comando diceva letteralmente
# `opendeck --version` — e con lui il plugin indicatore. Con OpenDeck gia'
# acceso non si vedeva, ed e' per questo che e' rimasto nascosto finora.
# La versione si legge dal pacchetto, che non esegue niente.
if command -v opendeck >/dev/null 2>&1; then
	ok "Eseguibile: $(command -v opendeck)"
	VER=$(dpkg-query -W -f='${Version}' opendeck 2>/dev/null || true)
	if [ -n "$VER" ]; then
		info "Versione: $VER  (serve >= 2.5.0)"
	else
		info "Versione non leggibile da dpkg (installazione non .deb?)."
	fi
elif dpkg -l 2>/dev/null | grep -q '^ii.*opendeck'; then
	ok "Pacchetto .deb installato:"
	dpkg -l | grep -i opendeck | sed 's/^/         /'
elif flatpak list 2>/dev/null | grep -qi opendeck; then
	warn "Installato come Flatpak."
	info "Il plugin indicatore gira nel sandbox e deve leggere ~/.claude/cc-state/:"
	info "potrebbe servire un 'flatpak override' per l'accesso al filesystem."
else
	no "OpenDeck non trovato (ne' nativo ne' Flatpak)."
fi

# Una directory `plugins` e' quella vera solo se contiene almeno una
# sottocartella *.sdPlugin. La cartella dei log contiene file .log e nella v1
# passava il filtro, innescando anche il bug dei falsi negativi.
head_ "Cartella plugin di OpenDeck"
PLUGINS_DIR=""
INSTALLED=""
while IFS= read -r d; do
	[ -z "$d" ] && continue
	for entry in "$d"/*.sdPlugin; do
		if [ -d "$entry" ]; then PLUGINS_DIR="$d"; break; fi
	done
	[ -n "$PLUGINS_DIR" ] && break
done < <(find "$HOME/.config" "$HOME/.local/share" "$HOME/.var/app" \
	-maxdepth 6 -type d -iname plugins -ipath '*opendeck*' 2>/dev/null || true)

if [ -n "$PLUGINS_DIR" ]; then
	ok "Cartella plugin: $PLUGINS_DIR"
	for entry in "$PLUGINS_DIR"/*.sdPlugin; do
		[ -d "$entry" ] || continue
		INSTALLED="$INSTALLED$(basename "$entry")"$'\n'
	done
	printf '%s' "$INSTALLED" | sed 's/^/           /'
else
	no "Non trovata alcuna cartella contenente plugin *.sdPlugin."
	info "Se OpenDeck non e' mai stato avviato e' normale: avvialo una volta."
	info "Altrimenti usa 'Open config directory' nelle sue impostazioni."
fi

# I controlli sui singoli plugin lavorano su una variabile gia' in memoria:
# niente pipe, niente SIGPIPE, niente corsa. Era questo il bug della v1.
has_plugin() {
	case "$(printf '%s' "$INSTALLED" | tr 'A-Z' 'a-z')" in
		*"$1"*) return 0 ;;
		*) return 1 ;;
	esac
}

head_ "Plugin AKP03"
if has_plugin akp03; then
	ok "Plugin akp03 installato."
else
	no "Plugin akp03 non installato."
fi

head_ "Plugin indicatore (io.github.meobob.ccmode)"
if has_plugin io.github.meobob.ccmode; then
	ok "Plugin indicatore installato."
	SK="$PLUGINS_DIR/io.github.meobob.ccmode.sdPlugin/sendkeys.py"
	if [ -f "$SK" ]; then
		if DRY=$("${CC_MODE_PYTHON:-/usr/bin/python3}" "$SK" --dry-run "${CC_MODE_CYCLE_KEYS:-shift+Tab}" 2>&1); then
			ok "sendkeys.py risolve la combinazione: $DRY"
		else
			no "sendkeys.py non funziona: $DRY"
		fi
	else
		no "sendkeys.py assente accanto al plugin: premere il tasto non cambiera' modalita'."
	fi
	LOG="$PLUGINS_DIR/io.github.meobob.ccmode.sdPlugin/plugin.log"
	if [ -f "$LOG" ]; then
		info "Ultime righe di plugin.log:"
		tail -n 5 "$LOG" | sed 's/^/           /'
	else
		warn "plugin.log assente: il plugin non e' mai partito."
		info "Il log sta QUI, non in ~/.local/share/opendeck/logs/plugins/"
		info "(quel file esiste ma resta vuoto: il plugin non usa stdout)."
	fi
else
	no "Plugin indicatore non installato."
fi

# Chiudere la finestra non riavvia OpenDeck: resta nella tray e la lista dei
# plugin resta quella letta all'avvio. Un plugin copiato dopo non viene visto.
head_ "OpenDeck e' stato riavviato dopo l'ultima copia di plugin?"
OD_PID=""
# Attenzione: qui NON si azzera IFS. Serve la divisione in campi per separare
# pid/stat/comm; con `IFS=` l'intera riga finirebbe nella prima variabile.
while read -r pid stat _; do
	case "$stat" in Z*) continue ;; esac
	OD_PID="$pid"; break
done < <(ps -eo pid,stat,comm 2>/dev/null | awk '$3 == "opendeck" {print $1, $2, $3}')

if [ -z "$OD_PID" ]; then
	warn "OpenDeck non risulta in esecuzione."
elif [ -n "$PLUGINS_DIR" ]; then
	ETIME=$(ps -o etimes= -p "$OD_PID" 2>/dev/null | tr -d ' ')
	if [ -n "$ETIME" ]; then
		START=$(( $(date +%s) - ETIME ))
		NEWEST=0; NEWEST_NAME=""
		for entry in "$PLUGINS_DIR"/*.sdPlugin; do
			[ -d "$entry" ] || continue
			M=$(stat -c %Y "$entry" 2>/dev/null || echo 0)
			if [ "$M" -gt "$NEWEST" ]; then NEWEST=$M; NEWEST_NAME=$(basename "$entry"); fi
		done
		info "OpenDeck: PID $OD_PID, avviato alle $(date -d "@$START" '+%H:%M:%S' 2>/dev/null || echo "$START")"
		if [ "$NEWEST" -gt "$START" ]; then
			no "Il plugin piu' recente ($NEWEST_NAME) e' arrivato DOPO l'avvio di OpenDeck."
			info "Copiato alle $(date -d "@$NEWEST" '+%H:%M:%S' 2>/dev/null || echo "$NEWEST")."
			info "OpenDeck non puo' averlo visto. Serve un'uscita VERA dalla tray"
			info "(Quit): chiudere la finestra non basta, e rilanciarlo lascia uno"
			info "zombie e ripresenta la vecchia istanza. Alternativa: kill $OD_PID"
		else
			ok "Nessun plugin e' piu' recente dell'avvio: la lista e' aggiornata."
		fi
	fi
fi

# ------------------------------------------------------------ 5. hook + cc --
head_ "Claude Code — hook"
if [ -f "$HOME/.claude/hooks/cc-mode.mjs" ]; then
	ok "Hook presente in ~/.claude/hooks/cc-mode.mjs"
	[ -f "$HOME/.claude/hooks/cc-activity.mjs" ] \
		&& ok "Hook attivita' presente in ~/.claude/hooks/cc-activity.mjs" \
		|| warn "Hook attivita' assente: ./scripts/install-activity.sh"
else
	no "Hook assente in ~/.claude/hooks/cc-mode.mjs"
fi

SETTINGS="$HOME/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
	if command -v jq >/dev/null 2>&1; then
		if jq -e . "$SETTINGS" >/dev/null 2>&1; then
			ok "settings.json e' JSON valido."
			EVENTS=$(jq -r '[.hooks // {} | to_entries[]
				| select(.value | tostring | test("cc-mode"))
				| .key] | join(", ")' "$SETTINGS" 2>/dev/null)
			if [ -n "$EVENTS" ]; then
				ok "Hook cc-mode registrato su: $EVENTS"
			else
				no "Nessun hook cc-mode dentro settings.json"
			fi
		else
			no "settings.json NON e' JSON valido. Non toccarlo finche' non lo sistemi."
		fi
	else
		warn "jq non installato: non posso ispezionare settings.json."
	fi
else
	no "~/.claude/settings.json non esiste ancora."
fi

# Dal 19/08/2026 lo stato e' una CARTELLA per indicatore, con un file per
# sessione: prima era un file solo e con piu' sessioni vinceva l'ultima.
head_ "Stato degli indicatori"
for COPPIA in "mode:CC_MODE_STATE_DIR:modalita'" "activity:CC_ACTIVITY_STATE_DIR:attivita'"; do
	SUB=${COPPIA%%:*}; RESTO=${COPPIA#*:}; VAR=${RESTO%%:*}; ETICHETTA=${RESTO#*:}
	DIR=$(eval "echo \${$VAR:-\$HOME/.claude/cc-state/$SUB}")
	if [ ! -d "$DIR" ]; then
		no "Cartella assente: $DIR"
		info "Normale finche' l'hook della $ETICHETTA non e' partito almeno una volta."
		continue
	fi
	N=$(find "$DIR" -maxdepth 1 -name '*.json' | wc -l)
	if [ "$N" -eq 0 ]; then
		info "$ETICHETTA: nessuna sessione attiva (cartella vuota)."
		continue
	fi
	ok "$ETICHETTA: $N sessione/i in $DIR"
	for F in "$DIR"/*.json; do
		BASE=$(basename "$F" .json)
		if command -v jq >/dev/null 2>&1; then
			VAL=$(jq -r '.state // .mode // "?"' "$F" 2>/dev/null)
			TS=$(jq -r '.ts // 0' "$F" 2>/dev/null)
			if [ "$TS" -gt 0 ] 2>/dev/null; then
				AGE=$(( ($(date +%s%3N) - TS) / 1000 ))
				info "  ${BASE:0:8}  $VAL  (${AGE}s fa)"
			else
				info "  ${BASE:0:8}  $VAL"
			fi
		else
			info "  ${BASE:0:8}  $(cat "$F")"
		fi
	done
done

printf '\n'
