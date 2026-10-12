# FS-UAE — `fs-uae-3` fork

This repository is a fork of [FS-UAE](http://fs-uae.net/), based on the
`fs-uae-3` branch (FS-UAE 3.2.35) — the last stable, released version of the
emulator. The fork keeps the 3.x version scheme; its releases start at 3.3.0.

## Why this fork?

FS-UAE 3.2.35 is the last version that was actually stabilized and released.
The later FS-UAE 4 and 5 branches (`fs-uae-4` and `main`) contain a large
WinUAE sync and a restructured code base, but they were never stabilized or
released and development has stalled. Instead of building on those unreleased
branches, this fork stays on the well-tested 3.2.35 emulator core and adds
narrowly scoped, useful improvements on top of it. The changes so far are
focused on the built-in debugger's memory watchpoint feature.

If you are interested in an application which makes use of those watchpoint
improvements, check out the [Debug Shell](https://github.com/Robbson/fs-uae-debug-shell).

## New features

### Memory watch logging modes

Like in _WinUAE_ a watchpoint can now report without stopping the emulator:

* `L` (`logonly`) — print the hit and keep running.
* `N` (`nobreak`) — record the hit but do not enter the debugger.

Flags may be combined (`RWL`, `W C L`, …) and word aliases (`logonly`,
`nobreak`, `mustchange`, `freeze`) are accepted. See the debugger help
(`w`) for the full syntax.

### Output formats

The hit message has two flavours:

* **Original** (default) — the same format as upstream fs-uae-3 / recent
  WinUAE: the raw CPU access (access address, access width and the full
  32-bit value).
* **Enhanced** (`enhanced_memwatch_outputs = 1`) — reports the **watched**
  value (correct watch address, width and value) instead of the raw CPU
  access, adds an **Amiga frame counter** (`vsync_counter`, the emulated
  chipset frame, not the host render counter) as the first column, and
  **zero-pads** all the fields to a fixed width

### Configuration options

* `debug_log = 1` — also write memory watch messages to the standard log file
  (`FS-UAE/Cache/Logs/fs-uae.log.txt`).
* `enhanced_memwatch_outputs = 1` — use the enhanced output format (watched
  value, Amiga frame counter and zero-padded values).

These two settings are independent: one controls *where* the output goes, the
other controls *how* it looks. The debugger console output is always shown.

Original format:

```
Memwatch 1: break at 00000574.L  W  000300AB  PC=00001234 CPUDW (000)
```

Enhanced format:

```
00000025 Memwatch 01: 00000574.W  W  000000AB PC=00001234 CPUDW (000)
```

### Programmatic debugger activation

The (console) debugger is normally entered with the <kbd>Mod</kbd>+<kbd>D</kbd>
/ <kbd>F12</kbd>+<kbd>D</kbd> hot key. A wrapper or launcher can now start it
without synthesising a key press: enable `debugger_signal = 1` (together with
`console_debugger = 1`) and send `SIGUSR1` to the FS-UAE process, for example
`kill -USR1 <pid>`. FS-UAE enters the debugger on the next emulated frame and
prints `WARNING: Activated debugger`, which can be used to confirm success. This
is POSIX only (Linux/macOS), not available on Windows.

## Bug fixes

* **`mustchange` (`C`) never worked.** The size-masked old memory value was
  compared against the unmasked new value, so any byte/word write — including
  writes of the same value — was reported as changed. The new value is now
  masked to the access size before the comparison.
* **Adjacent watchpoints blocked each other.** Once a watchpoint fired, a
  further access in the same instruction could overwrite the pending hit, so
  the lower-address watchpoint never triggered. A guard now preserves the first
  pending hit (matching newer WinUAE), and redefining a watchpoint no longer
  leaves a stale `mustchange`/`nobreak`/`reportonly` flag behind.
* **Trailing tokens were not parsed.** The `w` parser stopped after a single trailing
  token, so flags placed after one another (for example `w 1 574 2 W C L`) were
  dropped and the watchpoint always paused the emulator. The parser now consumes
  multiple trailing flag tokens.

## Documentation

The original FS-UAE documentation is available in the [README](README).
