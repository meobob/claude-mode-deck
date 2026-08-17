#!/usr/bin/env python3
# Copyright (C) 2026 meobob
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cattura i byte che arrivano dal deck e li registra con l'orario.

Sola lettura: non tocca niente, non scrive fuori dal proprio log.
Uscita: Ctrl+C.
"""
import os
import sys
import termios
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keytest.log")


def caret(b):
    """Notazione ^X, come 'cat -v'."""
    if b == 0x7F:
        return "^?"
    if b < 0x20:
        return "^" + chr(b + 0x40)
    if b < 0x7F:
        return chr(b)
    return "\\x%02x" % b


def main():
    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        sys.exit("Errore: va lanciato in un terminale vero, non in una pipe.")

    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    # iflag: niente XON/XOFF (altrimenti Ctrl+S congela) e niente CR->NL
    new[0] &= ~(termios.IXON | termios.ICRNL)
    # lflag: niente riga bufferizzata, niente eco, niente IEXTEN
    # (IEXTEN si mangerebbe Ctrl+O). ISIG resta acceso: Ctrl+C esce.
    new[3] &= ~(termios.ICANON | termios.ECHO | termios.IEXTEN)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, new)

    log = open(LOG, "w", buffering=1)
    log.write("# cattura tasti deck - avviata %s\n"
              % time.strftime("%Y-%m-%d %H:%M:%S"))

    print("\r\n  Cattura attiva. Questa finestra deve avere il FOCUS.")
    print("  Premi i tasti del deck. Ctrl+C per finire.\r")
    print("  " + "-" * 56 + "\r\n")

    last = None
    try:
        while True:
            data = os.read(fd, 64)
            if not data:
                break
            now = time.time()
            # piu' di mezzo secondo di silenzio = pressione nuova
            if last is not None and now - last > 0.5:
                sys.stdout.write("\r\n")
                log.write("---\n")
            last = now
            stamp = time.strftime("%H:%M:%S", time.localtime(now))
            stamp += ".%03d" % int((now % 1) * 1000)
            for b in data:
                r = caret(b)
                sys.stdout.write(r)
                log.write("%s  0x%02x  %s\n" % (stamp, b, r))
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old)
        log.write("# fine %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log.close()
        print("\r\n\r\n  Fine. Log in:\r\n  %s\r" % LOG)


if __name__ == "__main__":
    main()
