#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# prova-home-pulita.sh — verifica che gli script si comportino bene su una
# macchina che non e' questa.
#
# Non abbiamo un secondo deck, ma possiamo avere un HOME finto. Quello che si
# prova qui non e' "funziona altrove": e' che **ogni fallimento spiega cosa
# manca**. Un traceback Python grezzo e' un fallimento della prova.
#
# Non scrive niente nell'HOME vero: alla fine lo verifica.

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
FINTO=$(mktemp -d /tmp/prova-home-pulita.XXXXXX)
VERO="$HOME"

verde=$'\033[32m'; rosso=$'\033[31m'; fine=$'\033[0m'
PASSATE=0; FALLITE=0
ok()  { printf '  %s[OK]%s   %s\n' "$verde" "$fine" "$1"; PASSATE=$((PASSATE+1)); }
no()  { printf '  %s[NO]%s   %s\n' "$rosso" "$fine" "$1"; FALLITE=$((FALLITE+1)); }

# Stato dell'HOME vero, per accorgersi se qualcuno lo tocca.
IMPRONTA_PRIMA=$(find "$VERO/.claude" "$VERO/.config/opendeck" -maxdepth 2 \
	-newermt '-1 second' 2>/dev/null | wc -l)
SETTINGS_PRIMA=$(md5sum "$VERO/.claude/settings.json" 2>/dev/null | cut -d' ' -f1)

# Il messaggio deve CONTENERE la spiegazione, e non essere un traceback.
attende() {
	local nome="$1" atteso="$2"; shift 2
	local out rc
	out=$(HOME="$FINTO" "$@" 2>&1); rc=$?
	if grep -qi 'Traceback (most recent call last)' <<<"$out"; then
		no "$nome: traceback Python grezzo"
		sed 's/^/        /' <<<"$out" | tail -4
		return
	fi
	if grep -qi -- "$atteso" <<<"$out"; then
		ok "$nome"
	else
		no "$nome: non ho trovato \"$atteso\" nel messaggio"
		sed 's/^/        /' <<<"$out" | tail -6
	fi
}

printf '\nHOME finto: %s\n\n== Niente installato ==\n' "$FINTO"

attende "installa.sh dice che manca la cartella plugin di OpenDeck" \
	"Cartella plugin non trovata" "$REPO/scripts/installa.sh" --dry
attende "installa.sh dice che manca Claude Code" \
	"non esiste" "$REPO/scripts/installa.sh" --dry
attende "profili-da-zero dice che non trova i profili di OpenDeck" \
	"non trovo" "$REPO/scripts/profili-da-zero.py" --dry

printf '\n== OpenDeck avviato una volta, nessun deck collegato ==\n'
mkdir -p "$FINTO/.config/opendeck/profiles" "$FINTO/.claude"
attende "profili-da-zero dice che non c'e' nessun dispositivo" \
	"nessun dispositivo" "$REPO/scripts/profili-da-zero.py" --dry

printf '\n== Due deck collegati ==\n'
mkdir -p "$FINTO/.config/opendeck/profiles/xx-UNO" "$FINTO/.config/opendeck/profiles/yy-DUE"
attende "profili-da-zero chiede quale deck usare" \
	"OPENDECK_DEVICE" "$REPO/scripts/profili-da-zero.py" --dry

printf '\n== Deck con una forma diversa ==\n'
rm -rf "$FINTO/.config/opendeck/profiles/yy-DUE"
python3 - "$FINTO" <<'PY'
import json, os, sys
casa = sys.argv[1]
d = os.path.join(casa, ".config/opendeck/profiles/xx-UNO")
json.dump({"infobars": [], "keys": [None]*15, "sliders": [None]*2},
          open(os.path.join(d, "Default.json"), "w"))
PY
attende "profili-da-zero rifiuta un deck 15 tasti / 2 manopole" \
	"questo layout ne vuole 9 e 3" "$REPO/scripts/profili-da-zero.py" --dry

printf '\n== Deck della forma giusta, ID diverso da questa macchina ==\n'
python3 - "$FINTO" <<'PY'
import json, os, sys
casa = sys.argv[1]
d = os.path.join(casa, ".config/opendeck/profiles/xx-UNO")
json.dump({"infobars": [], "keys": [None]*9, "sliders": [None]*3},
          open(os.path.join(d, "Default.json"), "w"))
PY
attende "profili-da-zero accetta un ID di dispositivo qualsiasi" \
	"xx-UNO" "$REPO/scripts/profili-da-zero.py" --dry

printf '\n== L'"'"'HOME vero non e'"'"' stato toccato ==\n'
SETTINGS_DOPO=$(md5sum "$VERO/.claude/settings.json" 2>/dev/null | cut -d' ' -f1)
[ "$SETTINGS_PRIMA" = "$SETTINGS_DOPO" ] \
	&& ok "~/.claude/settings.json invariato" \
	|| no "~/.claude/settings.json e' cambiato!"
[ ! -d "$FINTO/.claude/hooks" ] \
	&& ok "nessun hook installato nell'HOME finto (erano tutte prove a vuoto)" \
	|| no "una prova a vuoto ha scritto qualcosa"

rm -rf "$FINTO"
printf '\n  %d superate, %d fallite\n\n' "$PASSATE" "$FALLITE"
[ "$FALLITE" -eq 0 ]
