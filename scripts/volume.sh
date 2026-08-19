#!/bin/bash
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Volume di sistema per la manopola centrale del deck.
#
#   volume.sh <scatti>   scatti e' il %d di Run Command: positivo in senso
#                        orario, negativo in senso antiorario. 5% a scatto.
#   volume.sh muto       commuta il muto.
#
# Serve uno script perche' Run Command esegue il comando direttamente, senza
# shell: niente $(( )) e niente printf nella casella della GUI. E perche'
# pactl distingue "+5%" (relativo) da "5%" (assoluto), quindi il segno va
# costruito, non concatenato.
set -u
PASSO=5

case "${1:-0}" in
  muto|mute)
    exec pactl set-sink-mute @DEFAULT_SINK@ toggle
    ;;
esac

scatti=${1:-0}
case "$scatti" in
  ''|*[!0-9-]*) echo "uso: $0 <scatti|muto>" >&2; exit 2 ;;
esac

delta=$(( scatti * PASSO ))
if [ "$delta" -ge 0 ]; then segno="+${delta}%"; else segno="${delta}%"; fi
pactl set-sink-volume @DEFAULT_SINK@ "$segno" || exit 1

# pactl non si ferma al 100%: oltre distorce, quindi tagliamo qui.
attuale=$(pactl get-sink-volume @DEFAULT_SINK@ | head -1 | grep -oE '[0-9]+%' | head -1 | tr -d '%')
if [ -n "$attuale" ] && [ "$attuale" -gt 100 ]; then
  pactl set-sink-volume @DEFAULT_SINK@ 100%
fi
