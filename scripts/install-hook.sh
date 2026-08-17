#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# install-hook.sh — installa l'hook cc-mode e lo registra in ~/.claude/settings.json
#
# Idempotente: rilanciabile quante volte vuoi, non duplica nulla.
# Non richiede sudo. Fa un backup di settings.json prima di toccarlo.
#
# Uso:  ./scripts/install-hook.sh          installa
#       ./scripts/install-hook.sh --dry    mostra cosa farebbe, senza scrivere

set -euo pipefail

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/../hook/cc-mode.mjs"
DEST_DIR="$HOME/.claude/hooks"
DEST="$DEST_DIR/cc-mode.mjs"
SETTINGS="$HOME/.claude/settings.json"

die() { printf '\033[31mERRORE:\033[0m %s\n' "$*" >&2; exit 1; }
say() { printf '  %s\n' "$*"; }

# ------------------------------------------------------------ prerequisiti --
command -v jq >/dev/null 2>&1 || die "jq non installato. Installa con: sudo apt install jq"
command -v node >/dev/null 2>&1 || die "node non installato."

NODE_MAJOR=$(node --version | sed 's/^v//' | cut -d. -f1)
[ "$NODE_MAJOR" -ge 22 ] || die "node $(node --version): serve la 22 o superiore."

[ -f "$SRC" ] || die "Sorgente hook non trovato: $SRC"

# --------------------------------------------------------- copia dell'hook --
if [ "$DRY" -eq 1 ]; then
	say "[dry] copierei $SRC -> $DEST"
else
	mkdir -p "$DEST_DIR"
	cp "$SRC" "$DEST"
	say "Hook copiato in $DEST"
fi

# ------------------------------------------------------- merge in settings --
# Se settings.json non esiste, partiamo da un oggetto vuoto.
if [ -f "$SETTINGS" ]; then
	jq -e . "$SETTINGS" >/dev/null 2>&1 \
		|| die "$SETTINGS non e' JSON valido. Sistemalo a mano prima di rilanciare."
	CURRENT=$(cat "$SETTINGS")
else
	CURRENT='{}'
	say "$SETTINGS non esiste: lo creo."
fi

CMD='node ~/.claude/hooks/cc-mode.mjs'

MERGED=$(printf '%s' "$CURRENT" | jq --arg cmd "$CMD" '
	# Toglie ogni handler che punta a cc-mode, poi scarta i gruppi rimasti vuoti.
	# Cosi il rilancio non duplica e un eventuale vecchio comando sparisce.
	def strip_cc:
		map(.hooks |= map(select((.command // "") | test("cc-mode") | not)))
		| map(select((.hooks | length) > 0));

	def handler($async; $timeout):
		{ type: "command", command: $cmd, timeout: $timeout }
		+ (if $async then { async: true } else {} end);

	.hooks //= {}
	| .hooks.UserPromptSubmit =
		(((.hooks.UserPromptSubmit // []) | strip_cc)
		 + [{ hooks: [handler(true; 10)] }])
	| .hooks.PreToolUse =
		(((.hooks.PreToolUse // []) | strip_cc)
		 + [{ matcher: "*", hooks: [handler(true; 10)] }])
	| .hooks.SessionEnd =
		(((.hooks.SessionEnd // []) | strip_cc)
		 + [{ hooks: [handler(false; 5)] }])
')

printf '%s' "$MERGED" | jq -e . >/dev/null 2>&1 || die "Il merge ha prodotto JSON non valido. Nulla e' stato scritto."

if [ "$DRY" -eq 1 ]; then
	say "[dry] settings.json risultante:"
	printf '%s\n' "$MERGED" | jq . | sed 's/^/    /'
	exit 0
fi

if [ -f "$SETTINGS" ]; then
	BACKUP="$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"
	cp "$SETTINGS" "$BACKUP"
	say "Backup: $BACKUP"
fi

mkdir -p "$(dirname "$SETTINGS")"
printf '%s\n' "$MERGED" | jq . > "$SETTINGS"
say "Hook registrato su UserPromptSubmit, PreToolUse, SessionEnd."

# ------------------------------------------------------------------ prova --
TESTFILE=$(mktemp)
echo '{"hook_event_name":"PreToolUse","permission_mode":"plan","session_id":"test"}' \
	| CC_MODE_STATE_FILE="$TESTFILE" node "$DEST"
if jq -e '.mode == "plan"' "$TESTFILE" >/dev/null 2>&1; then
	say "Prova a vuoto superata: l'hook scrive correttamente."
else
	printf '\033[33mATTENZIONE:\033[0m la prova a vuoto non ha prodotto il risultato atteso.\n'
	printf '  Contenuto: %s\n' "$(cat "$TESTFILE")"
fi
rm -f "$TESTFILE"

printf '\nFatto. In Claude Code, /hooks deve ora elencare i tre hook.\n'
