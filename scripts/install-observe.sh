#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# install-observe.sh — installa l'hook TEMPORANEO di osservazione cc-observe.
#
# Serve alla Fase 0 dell'indicatore di attivita': scoprire quali eventi
# arrivano davvero su questa installazione. Va tolto quando il dato e' stato
# raccolto:  ./scripts/install-observe.sh --rimuovi
#
# Idempotente, come install-hook.sh, e con lo stesso meccanismo: toglie ogni
# handler che punta a cc-observe e poi lo riaggiunge. Gli handler di cc-mode
# non vengono mai toccati — il filtro guarda solo "cc-observe".
#
# Registrazione SINCRONA di proposito. L'osservatore serve a stabilire
# l'ORDINE degli eventi: in modo asincrono due hook possono girare
# sovrapposti e il log mentirebbe sull'ordine. Costa ~60 ms per evento.
#
# Uso:  ./scripts/install-observe.sh          installa
#       ./scripts/install-observe.sh --dry    mostra e basta
#       ./scripts/install-observe.sh --rimuovi   disinstalla

set -euo pipefail

MODO="installa"
case "${1:-}" in
	--dry) MODO="dry" ;;
	--rimuovi) MODO="rimuovi" ;;
	"") ;;
	*) echo "opzione sconosciuta: $1"; exit 2 ;;
esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/../hook/cc-observe.mjs"
DEST_DIR="$HOME/.claude/hooks"
DEST="$DEST_DIR/cc-observe.mjs"
SETTINGS="$HOME/.claude/settings.json"
CMD='node ~/.claude/hooks/cc-observe.mjs'

# Documentati, NON verificati su questa installazione: scoprire quali di
# questi arrivino davvero e' esattamente il lavoro della Fase 0.
SEMPLICI="SessionStart UserPromptSubmit PermissionRequest Notification Stop SubagentStop SessionEnd"
CON_MATCHER="PreToolUse PostToolUse"

die() { printf '\033[31mERRORE:\033[0m %s\n' "$*" >&2; exit 1; }
say() { printf '  %s\n' "$*"; }

command -v jq >/dev/null 2>&1 || die "jq non installato."
command -v node >/dev/null 2>&1 || die "node non installato."
[ -f "$SETTINGS" ] || die "$SETTINGS non esiste: installa prima cc-mode."
jq -e . "$SETTINGS" >/dev/null 2>&1 || die "$SETTINGS non e' JSON valido."
CURRENT=$(cat "$SETTINGS")

FILTRO='
	def strip_obs:
		map(.hooks |= map(select((.command // "") | test("cc-observe") | not)))
		| map(select((.hooks | length) > 0));
'

if [ "$MODO" = "rimuovi" ]; then
	MERGED=$(printf '%s' "$CURRENT" | jq "$FILTRO"'
		.hooks //= {}
		| .hooks |= with_entries(.value |= strip_obs)
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
			.hooks[$e] = (((.hooks[$e] // []) | strip_obs) + [{ hooks: [handler] }]))
		| reduce ($conmatcher | split(" "))[] as $e (.;
			.hooks[$e] = (((.hooks[$e] // []) | strip_obs) + [{ matcher: "*", hooks: [handler] }]))
	')
fi

printf '%s' "$MERGED" | jq -e . >/dev/null 2>&1 \
	|| die "Il merge ha prodotto JSON non valido. Nulla e' stato scritto."

# Rete di sicurezza: cc-mode deve sopravvivere in ogni caso.
PRIMA=$(printf '%s' "$CURRENT" | jq '[.. | objects | select(.command? // "" | test("cc-mode"))] | length')
DOPO=$(printf '%s' "$MERGED" | jq '[.. | objects | select(.command? // "" | test("cc-mode"))] | length')
[ "$PRIMA" = "$DOPO" ] || die "gli handler di cc-mode passerebbero da $PRIMA a $DOPO. Interrotto."
say "handler di cc-mode intatti: $PRIMA prima, $DOPO dopo."

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
	say "Osservatore rimosso da settings.json e da $DEST."
	say "Il log resta dov'e': ~/.claude/cc-observe.log"
	exit 0
fi

mkdir -p "$DEST_DIR"
cp "$SRC" "$DEST"
say "Hook copiato in $DEST"
printf '%s\n' "$MERGED" | jq . > "$SETTINGS"
say "Registrato su: $SEMPLICI $CON_MATCHER"

# ------------------------------------------------------------------ prova --
TESTLOG=$(mktemp)
echo '{"hook_event_name":"PreToolUse","permission_mode":"auto","session_id":"prova"}' \
	| CC_OBSERVE_LOG="$TESTLOG" node "$DEST"
if grep -q 'PreToolUse' "$TESTLOG"; then
	say "Prova a vuoto superata: $(cat "$TESTLOG")"
else
	printf '\033[33mATTENZIONE:\033[0m la prova a vuoto non ha scritto niente.\n'
fi
rm -f "$TESTLOG"

printf '\nFatto. Il log si accumula in ~/.claude/cc-observe.log\n'
printf 'Per togliere tutto:  %s --rimuovi\n' "$0"
