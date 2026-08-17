#!/usr/bin/env bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
# Installa i profili corretti e le icone. DA LANCIARE A OPENDECK FERMO.
#
# Si ferma da solo se OpenDeck e' vivo: a processo acceso i profili stanno in
# memoria e vengono riscritti all'uscita, quindi installare mentre gira
# significa veder sparire tutto.
#
# Fa il backup prima di toccare qualsiasi cosa. Non cancella niente in
# ~/.config/opendeck: copia sopra, e le immagini si fondono con quelle
# esistenti (quella dell'indicatore resta dov'e').

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
CONF="$HOME/.config/opendeck"

# L'ID del deck e' il nome della cartella dentro profiles/: cambia da deck a
# deck, quindi si legge invece di scriverlo. OPENDECK_DEVICE lo forza, se
# ne hai collegato piu' di uno.
if [ -n "${OPENDECK_DEVICE:-}" ]; then
	DEVICE="$OPENDECK_DEVICE"
else
	mapfile -t DEVS < <(find "$CONF/profiles" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort)
	if [ "${#DEVS[@]}" -ne 1 ]; then
		echo "Trovati ${#DEVS[@]} dispositivi in $CONF/profiles: ${DEVS[*]:-nessuno}"
		echo "Scegli con  OPENDECK_DEVICE=<id> $0"
		exit 1
	fi
	DEVICE="${DEVS[0]}"
fi

PROF="$CONF/profiles/$DEVICE/Claude"
IMG="$CONF/images"
STAMP=$(date +%Y-%m-%d-%H%M)
BK="$REPO/backup/$STAMP-prima-delle-correzioni"

# ---------------------------------------------------------------- sicurezza --
if pgrep -x opendeck >/dev/null; then
	echo "OpenDeck e' in esecuzione. Esci con Quit dalla tray, poi rilancia questo script."
	exit 1
fi
echo "OpenDeck fermo."

for f in 1-guida 2-contesto 3-regolazioni; do
	[ -f "$HERE/nuovi-profili/$f.json" ] || { echo "manca $f.json in nuovi-profili/"; exit 1; }
	python3 -c "import json,sys; json.load(open('$HERE/nuovi-profili/$f.json'))" \
		|| { echo "$f.json non e' JSON valido"; exit 1; }
done
echo "I tre profili nuovi sono JSON valido."

# ------------------------------------------------------------------ backup --
mkdir -p "$BK/profili" "$BK/immagini"
cp "$PROF"/*.json "$BK/profili/"
cp "$CONF/profiles/$DEVICE.json" "$BK/profili/$DEVICE.indice.json"
[ -d "$IMG/$DEVICE" ] && cp -r "$IMG/$DEVICE" "$BK/immagini/"
echo "Backup in $BK"

# --------------------------------------------------------------- pulizia ----
# Cartelle immagini rimaste da 9-prova, il profilo dell'esperimento di ieri:
# il profilo non esiste piu', queste sono orfane.
if [ -d "$IMG/$DEVICE/Claude/9-prova" ]; then
	rm -rf "$IMG/$DEVICE/Claude/9-prova"
	echo "Rimosse le immagini orfane di 9-prova (erano gia' nel backup)."
fi

# ----------------------------------------------------------------- copia ----
cp "$HERE/nuovi-profili"/*.json "$PROF/"
cp -r "$HERE/nuove-immagini/$DEVICE" "$IMG/"
echo "Installati profili e icone."

# --------------------------------------------------------------- verifica ---
echo
echo "--- controllo ---"
for f in 1-guida 2-contesto 3-regolazioni; do
	a=$(md5sum < "$HERE/nuovi-profili/$f.json")
	b=$(md5sum < "$PROF/$f.json")
	[ "$a" = "$b" ] && echo "  $f: copiato" || echo "  $f: >>> DIVERSO <<<"
done
echo "  immagini installate: $(find "$IMG/$DEVICE" -name '0.png' | wc -l) file 0.png"
echo "  profilo attivo: $(cat "$CONF/profiles/$DEVICE.json" | tr -d '\n ')"
echo
echo "Ora rilancia OpenDeck."
