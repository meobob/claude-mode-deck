#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# install-activity.sh — installa l'hook cc-activity e lo registra.
#
# Gemello di install-hook.sh, e con lo stesso meccanismo: toglie ogni handler
# che punta a cc-activity e poi lo riaggiunge, quindi e' idempotente. Gli
# handler di cc-mode NON vengono mai toccati: il filtro guarda solo
# "cc-activity". C'e' anche un controllo esplicito che li conta prima e dopo e
# si ferma se il numero cambia.
#
# Registrazione SINCRONA di proposito, ed e' una scelta, non una svista:
# `PermissionRequest` arriva 100 ms dopo il `PreToolUse` dello stesso
# strumento (misurato il 19/08/2026). In modo asincrono i due hook potrebbero
# finire in ordine invertito, e il tasto resterebbe su "lavora" mentre Claude
# aspetta una risposta — cioe' proprio lo stato che l'indicatore esiste per
# mostrare. Costa ~60 ms per evento.
#
# Uso:  ./scripts/install-activity.sh            installa
#       ./scripts/install-activity.sh --dry      mostra e basta
#       ./scripts/install-activity.sh --rimuovi  disinstalla

set -euo pipefail

MODO="installa"
case "${1:-}" in
	--dry) MODO="dry" ;;
	--rimuovi) MODO="rimuovi" ;;
	"") ;;
	*) echo "opzione sconosciuta: $1"; exit 2 ;;
esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/../hook/cc-activity.mjs"
DEST_DIR="$HOME/.claude/hooks"
DEST="$DEST_DIR/cc-activity.mjs"
SETTINGS="$HOME/.claude/settings.json"
CMD='node ~/.claude/hooks/cc-activity.mjs'

# Solo gli eventi che la mappa usa davvero. SubagentStop non c'e': l'hook lo
# ignorerebbe comunque, e registrarlo vorrebbe dire avviare node per niente.
SEMPLICI="SessionStart UserPromptSubmit PermissionRequest Notification Stop SessionEnd"
CON_MATCHER="PreToolUse PostToolUse"

die() { printf '\033[31mERRORE:\033[0m %s\n' "$*" >&2; exit 1; }
say() { printf '  %s\n' "$*"; }

command -v jq >/dev/null 2>&1 || die "jq non installato."
command -v node >/dev/null 2>&1 || die "node non installato."
[ -f "$SETTINGS" ] || die "$SETTINGS non esiste."
jq -e . "$SETTINGS" >/dev/null 2>&1 || die "$SETTINGS non e' JSON valido."
CURRENT=$(cat "$SETTINGS")

FILTRO='
	def strip_act:
		map(.hooks |= map(select((.command // "") | test("cc-activity") | not)))
		| map(select((.hooks | length) > 0));
'

if [ "$MODO" = "rimuovi" ]; then
	MERGED=$(printf '%s' "$CURRENT" | jq "$FILTRO"'
		.hooks //= {}
		| .hooks |= with_entries(.value |= strip_act)
		| .hooks |= with_entries(select((.value | length) > 0))
	')
else
	[ -f "$SRC" ] || die "sorgente non trovato: $SRC"
	MERGED=$(printf '%s' "$CURRENT" | jq \
		--arg cmd "$CMD" --arg semplici "$SEMPLICI" --arg conmatcher "$CON_MATCHER" \
		"$FILTRO"'
		def handler: { type: "command", command: $cmd, timeout: 5 };
		.hooks //= {}
		| reduce ($semplici | split(" "))[] as $e (.;
			.hooks[$e] = (((.hooks[$e] // []) | strip_act) + [{ hooks: [handler] }]))
		| reduce ($conmatcher | split(" "))[] as $e (.;
			.hooks[$e] = (((.hooks[$e] // []) | strip_act) + [{ matcher: "*", hooks: [handler] }]))
	')
fi

printf '%s' "$MERGED" | jq -e . >/dev/null 2>&1 \
	|| die "Il merge ha prodotto JSON non valido. Nulla e' stato scritto."

PRIMA=$(printf '%s' "$CURRENT" | jq '[.. | objects | select(.command? // "" | test("cc-mode"))] | length')
DOPO=$(printf '%s' "$MERGED" | jq '[.. | objects | select(.command? // "" | test("cc-mode"))] | length')
[ "$PRIMA" = "$DOPO" ] || die "gli handler di cc-mode passerebbero da $PRIMA a $DOPO. Interrotto."
say "handler di cc-mode intatti: $PRIMA."

if [ "$MODO" = "dry" ]; then
	say "[dry] hooks risultanti:"
	printf '%s' "$MERGED" | jq '.hooks | to_entries | map({evento: .key, handler: [.value[].hooks[].command]})' | sed 's/^/    /'
	exit 0
fi

BACKUP="$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"
cp "$SETTINGS" "$BACKUP"
say "Backup: $BACKUP"

if [ "$MODO" = "rimuovi" ]; then
	printf '%s\n' "$MERGED" | jq . > "$SETTINGS"
	rm -f "$DEST"
	say "Hook di attivita' rimosso."
	exit 0
fi

mkdir -p "$DEST_DIR"
cp "$SRC" "$DEST"
say "Hook copiato in $DEST"
printf '%s\n' "$MERGED" | jq . > "$SETTINGS"
say "Registrato su: $SEMPLICI $CON_MATCHER"

TEST=$(mktemp)
echo '{"hook_event_name":"PermissionRequest","session_id":"prova"}' \
	| CC_ACTIVITY_STATE_FILE="$TEST" node "$DEST"
if jq -e '.state == "wait"' "$TEST" >/dev/null 2>&1; then
	say "Prova a vuoto superata: $(cat "$TEST")"
else
	printf '\033[33mATTENZIONE:\033[0m la prova a vuoto non ha dato il risultato atteso.\n'
fi
rm -f "$TEST"

printf '\nFatto.\n'
