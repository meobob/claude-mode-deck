# Claude Code Mode — permission-mode indicator for Ajazz AKP03E / OpenDeck

One key on your stream deck shows which Claude Code **permission mode** is
active, by colour and by shape. Pressing it sends `Shift+Tab` to the focused
window, so the same key both shows the mode and changes it.

**What it does not do — read this before installing:**

- **Not real time.** Hooks fire on events, not on Shift+Tab: change mode and do
  nothing, and the key stays stale until your next prompt or tool call.
- **One session at a time.** Single state file — with two Claude Code sessions
  open, the last one to write wins.
- **Keystrokes go to the focused window**, not to Claude Code as such. Browser
  focused, browser gets the `Shift+Tab`.

**Requirements:** Linux on **X11** · **OpenDeck ≥ 2.5.0** with the
`opendeck-akp03` plugin · **Node.js ≥ 22**, natively installed (not Flatpak) ·
`python3-xlib` for the press-to-cycle half.

**Verified on:** Linux Mint 22.3 (noble), X11 · Ajazz AKP03E rev. 2
(`0300:3002`) · OpenDeck 2.14.0 · AKP03 plugin 0.10.1 · Node 22.23.2 from
NodeSource. Never tried on Windows, never tried on Wayland.

---

## How it works

Two pieces:

1. **`hook/cc-mode.mjs`** — a Claude Code hook. It receives the event JSON,
   extracts `permission_mode` and writes it to `~/.claude/cc-mode.json`.
2. **`io.github.meobob.ccmode.sdPlugin/`** — an OpenDeck plugin. It re-reads
   that file every 500 ms and updates the key's image and title. Pressing the
   key sends `Shift+Tab` to the focused window via `sendkeys.py`.

```
Claude Code --(hook)--> ~/.claude/cc-mode.json --(polling)--> OpenDeck plugin --> key
     ^                                                                            |
     +---------------- Shift+Tab via sendkeys.py (XTEST) <--------- key press -----+
```

### Status

Installed and verified on **14 August 2026** on the hardware listed above. The
full chain was demonstrated on the physical deck: Shift+Tab → message → hook →
`cc-mode.json` → plugin polling → `setImage` → the key changes colour. `auto`
shows amber AUTO, `default` shows red MANUAL. The hook is no longer "tested with
fake input only": it runs against real Claude Code and writes `mode`, `reason`,
`ts`, `session_id`, `cwd`.

On **15 August 2026** the key started changing the mode as well as showing it.
Measured: the press produces `^[[Z`, byte-identical to what a *Simulate Input*
key produces, and the `auto → default → auto` cycle was followed by the key in
both directions. On the same day, all 17 keys of the layout were verified to
send exactly the expected bytes, captured one by one — the tool is
`tools/cattura-tasti.py`.

**A note on `setState`:** the API has a `setState` event that would be the
natural way to drive a multi-state indicator, but the example in the OpenAction
documentation is plainly wrong (it reports `event: "logMessage"` and has no
`context` field). Rather than build on that, this plugin uses `setImage`, which
is specified unambiguously and worked on the first try.

---

## Installation

> If you are having Claude Code install this for you, don't follow this section:
> use `docs/PROMPT.md` and `INSTALL.md`. What follows is the manual summary.

### 1. The hook

```bash
mkdir -p ~/.claude/hooks
cp hook/cc-mode.mjs ~/.claude/hooks/
```

Then merge the contents of `settings-snippet.json` into
`~/.claude/settings.json`. If the file already has a `"hooks"` key, merge the
contents instead of overwriting it. `scripts/install-hook.sh` does all of this
for you, with a backup, and is idempotent.

Check it with fake input:

```bash
echo '{"hook_event_name":"PreToolUse","permission_mode":"plan"}' \
  | node ~/.claude/hooks/cc-mode.mjs
cat ~/.claude/cc-mode.json
```

Then open Claude Code and confirm with `/hooks` that the three hooks are
registered.

On **Windows** the command `node ~/.claude/hooks/cc-mode.mjs` still works:
Claude Code hands the command to Git Bash when it is installed, and `~` expands
to your home directory. If you prefer an absolute path, use forward slashes
(`C:/Users/yourname/...`), never backslashes — Git Bash eats them as escape
characters.

### 2. The plugin

Open OpenDeck's settings → **Open config directory** → the `plugins` folder, and
copy the whole `io.github.meobob.ccmode.sdPlugin` directory into it (the
directory name must stay exactly that). Restart OpenDeck.

You will find the action under the **Claude Code** category, named
*Permission mode*. Drag it onto a key.

---

## Reading the colours

| Mode | Colour | Shape | Title | Meaning |
|---|---|---|---|---|
| `default` (Manual) | red | octagon | MANUAL | every action goes through you |
| `plan` | blue | three lines | PLAN | planning, not executing |
| `acceptEdits` | green | check mark | EDITS | file edits go through on their own |
| `auto` | amber | ›› | AUTO | broad automatic approval |
| `dontAsk` | dark amber | ››› | NO ASK | same, without asking |
| `bypassPermissions` | magenta | hazard triangle | BYPASS | no brakes |
| unknown / session closed | grey | ? | ? | we don't know |

Two deliberate choices, which you can of course change:

- **`bypassPermissions` is not green.** It is the most dangerous state, and it
  must not wear the colour the brain reads as "all good".
- **Unknown is grey, never green.** If the plugin doesn't know what state you
  are in, it says so. An indicator that lies reassuringly is worse than no
  indicator at all.

Every state differs in colour **and** in shape, so it stays readable under harsh
desk light, or if colour alone isn't enough for you.

To change the colours: edit `make_icons.py`, run it, restart OpenDeck.

---

## Real limitations, worth keeping in mind

**1. It is not instant.** *Confirmed in the field.* Hooks fire on events, not
when you press Shift+Tab. If you change mode and then do nothing, the key stays
behind until the next prompt you send or the next tool call. In practice: change
mode, send the message, the key updates. Measured on 15 August 2026: message
sent at 20:03:37, key redrawn at 20:03:38.090. There is no way to do better with
the tools documented today.

**2. One session at a time.** There is a single state file: with two Claude Code
sessions open, the last one to write wins. If you routinely work across parallel
sessions, this indicator will lie to you.

**3. Pressing the key cycles the mode, but the key lies to you for a few
seconds.** *Fixed on 15 August 2026: it used to be read-only.* The press sends
`Shift+Tab` to the focused window and really does change the mode — but because
of limitation 1 the key's face cannot update immediately. In the meantime it
shows a dot next to the title, meaning "request sent, not yet confirmed", which
clears itself after 6 seconds.

The dot is not decoration. Without it you press, nothing visible happens, and
the natural reaction is to press a second time and cycle two modes. The *next*
mode is deliberately not shown in advance: the cycle order depends on your
configuration, and guessing it would mean writing something false on the key.

The usual constraint applies: keystrokes go to the window that has **focus**,
not to Claude Code as such. If focus is on the browser, the browser receives the
`Shift+Tab`. To go back to a read-only indicator, set `CC_MODE_CYCLE=0` — no
code changes needed.

**3b. Stacking two actions on the key does not achieve the same thing.**
*Measured, not deduced.* OpenDeck has a `Multi Action` container, and you can
put both a `Simulate Input` and the indicator inside it: the sequence does run,
but **the container keeps the key's face** and the indicator stops drawing.
Tried in all three variants — indicator first, indicator second, indicator alone
— with the same outcome. That is why the plugin sends the keystroke itself: one
action stays on the key and `setImage` keeps control. The profile from that
experiment is in `docs/esempio-multiaction.json`, and
`tools/genera-multiaction.py` shows how it was built. That JSON is a verbatim
dump from 15 August 2026, so it still carries the plugin's old `com.pcmod.*`
ids: it was left untouched on purpose, because its value is in being exactly
what OpenDeck wrote.

**4. A freshly created key stays `?` until you press it once.** `willAppear`
does not arrive when you drag the action onto a key for the first time. Pressing
it fixes it, and after an OpenDeck restart the key paints itself. It happens
once per key; you won't meet it in daily use.

**5. Closing the OpenDeck window does not restart it.** It stays in the tray,
and launching it again brings back the old instance with the plugin list it read
at its previous start — a plugin copied in later is not seen. You need *Quit*
from the tray. `scripts/check.sh` detects this and says so.

**6. If you delete and re-add the action** after editing the manifest, do it
from scratch: OpenDeck persists an independent copy per instance.

---

## Environment variables

| Variable | Default | Effect |
|---|---|---|
| `CC_MODE_STATE_FILE` | `~/.claude/cc-mode.json` | path of the state file (set it on **both** hook and plugin) |
| `CC_MODE_POLL_MS` | `500` | how often the plugin re-reads the file |
| `CC_MODE_STALE_MS` | `0` (off) | after how many ms without updates to show "unknown" |
| `CC_MODE_CYCLE` | on | `0` makes the key read-only again: show, don't touch |
| `CC_MODE_CYCLE_KEYS` | `shift+Tab` | the combination sent on press |
| `CC_MODE_PYTHON` | `/usr/bin/python3` | interpreter that runs `sendkeys.py` |
| `CC_MODE_PENDING_MS` | `6000` | how long the pending dot stays |
| `CC_MODE_PENDING_MARK` | `·` | the mark used for pending |
| `OPENDECK_DEVICE` | auto-detected | deck id, for the scripts under `scripts/` and `tools/` |

About `CC_MODE_STALE_MS`: careful, "old" does not mean "wrong". If you haven't
used Claude Code for an hour, the mode is still whatever it was. Turn it on only
if you prefer a cautious grey over correct but stale data.

---

## Layout

`LAYOUT.md` documents the 17-key layout this deck is set up with, and — for each
key — whether the keystroke it sends was verified or only assumed. It is in
Italian, as is the rest of the documentation under `docs/`.

---

## Structure

```
claude-mode-deck/
├── README.md                       # this file
├── INSTALL.md                      # step-by-step procedure, with the [UTENTE] stops
├── LAYOUT.md                       # what goes on each key, and what was verified
├── LICENSE                         # GPL-3.0
├── make_icons.py                   # regenerates the plugin's state icons
├── make_key_icons.py               # regenerates the key icons
├── settings-snippet.json           # to merge into ~/.claude/settings.json
├── docs/
│   ├── PROMPT.md                   # opening prompt to hand to Claude Code
│   ├── CONTEXT.md                  # how the project grew, and why
│   └── esempio-multiaction.json    # a Multi Action as OpenDeck writes it
├── tools/
│   ├── cattura-tasti.py            # logs the bytes arriving from the deck, timestamped
│   └── genera-multiaction.py       # how a multi-action profile is built
├── keys/                           # key icons, one folder per page
├── scripts/
│   ├── check.sh                    # read-only diagnostics
│   ├── install-hook.sh             # installs the hook, idempotent
│   ├── profili-genera.py           # how the profiles in use were produced
│   └── profili-installa.sh         # installs them: backup, OpenDeck stopped, verify
├── hook/
│   └── cc-mode.mjs
└── io.github.meobob.ccmode.sdPlugin/
    ├── manifest.json
    ├── plugin.mjs
    ├── sendkeys.py                 # sends a key combination via XTEST
    ├── icon.png
    └── states/*.png
```

Most of the documentation is in Italian; this README is not. `scripts/check.sh`
is the fastest way to find out what state your machine is in — it is read-only
and never asks for `sudo`.

---

## License

GPL-3.0 — see `LICENSE`.

This plugin does not incorporate code from either [OpenDeck][od] or the
[AKP03 plugin][akp]: it is a separate process that talks to OpenDeck over a
documented WebSocket protocol. Both of those projects are GPL-3.0 as well, which
is where this project's choice comes from — not from an obligation to inherit
it.

[od]: https://github.com/nekename/OpenDeck
[akp]: https://github.com/4ndv/opendeck-akp03
