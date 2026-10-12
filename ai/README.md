# AI debugger integration

This directory ships an AI *skill* that lets an assistant drive the built-in
console debugger of this [FS-UAE fork](https://github.com/Robbson/fs-uae)
programmatically — launching the emulator at a given save state, entering the
debugger over a signal, running debugger commands, breakpoints and memory
watchpoints, reading the results, and re-running from the same point.

It relies on the `debugger_signal` option added by this fork (see
[`docs/options/debugger_signal.md`](../docs/options/debugger_signal.md)), which
enters the debugger in response to `SIGUSR1` instead of a keyboard hotkey.

## Contents

| Path | Purpose |
|---|---|
| `fs-uae-debugger/SKILL.md` | The skill itself: parameters, launch, activation, console protocol, full command reference, workflows, and failure modes. |
| `fs-uae-debugger/driver.py` | A minimal reference driver implementing the protocol in Python. |

## Prerequisites

- `fs-uae` built from this fork and available on your `PATH` (otherwise set
  `FS_UAE_BIN` to its location), with `debugger_signal` present. Verify with
  `strings -a "$(command -v fs-uae)" | grep debugger_signal`.
- A POSIX host (Linux or macOS). The `SIGUSR1` trigger does not exist on
  Windows.
- The FS-UAE base directory (`$HOME/FS-UAE`) populated with the Kickstart ROM
  and the disk images referenced by your configuration, plus the save state you
  want to start from.
- Python 3 only if you intend to run `driver.py`.

## Installing the skill

The skill is a single folder named after the skill (`fs-uae-debugger/`)
containing `SKILL.md` with `name`/`description` front matter. Copy that folder
into whatever skills directory your assistant uses.

### Kilo (this project's agent tooling)

Copy the folder into a skills directory so it becomes available to the agent:

    # project-scoped
    mkdir -p .kilo/skills
    cp -r ai/fs-uae-debugger .kilo/skills/

    # or user-scoped
    mkdir -p ~/.config/kilo/skills
    cp -r ai/fs-uae-debugger ~/.config/kilo/skills/

`.kilo/skill/` (singular) also works. Alternatively, add this directory to
`skills.paths` in `kilo.json` if your setup expects skills to live elsewhere.

### Claude Code

    mkdir -p ~/.claude/skills
    cp -r ai/fs-uae-debugger ~/.claude/skills/

### Other skill-aware tools

Follow that tool's convention: the file must be named `SKILL.md` and keep the
`name` and `description` front matter. The folder name (`fs-uae-debugger`)
becomes the skill id.

### Plain LLMs without a skills mechanism

Paste the body of `fs-uae-debugger/SKILL.md` into the system prompt or custom
instructions, then give the assistant the parameters below. No installation step
is needed.

## Parameters to give the assistant

The skill expects these to be provided; do not hardcode them into the skill.

| Parameter | Meaning | Example |
|---|---|---|
| `FS_UAE_BIN` | Optional override for the binary; defaults to `fs-uae` on the `PATH` | `/opt/FS-UAE/bin/fs-uae` |
| `CONFIG` | `.fs-uae` configuration file | `~/FS-UAE/Configurations/HotShot.fs-uae` |
| `SAVE_STATE` | Save-state slot, `1`–`9` | `2` |
| `EXTRA_ARGS` | Optional extra options | `--automatic_input_grab=0` |

`fs-uae` is expected to be on the `PATH`; `FS_UAE_BIN` is only needed when it is
not. Save states live under `$HOME/FS-UAE/Save States/<configuration-name>/`.

## Quick start (manual)

    fs-uae --console_debugger=1 --debugger_signal=1 --stdout \
      --load_state=2 ~/FS-UAE/Configurations/HotShot.fs-uae

If `fs-uae` is not on your `PATH`, substitute its full path (or `$FS_UAE_BIN`).

Wait for the safety marker on stdout before signalling:

    debugger_signal: sending SIGUSR1 will activate the debugger (requires console_debugger)

Then activate and use the console:

    kill -USR1 <fs-uae-pid>     # enter the debugger
    # at the ">" prompt, type debugger commands
    ?                           # list all available commands
    r                           # dump registers
    f 1234                      # toggle breakpoint at $001234
    g                           # resume emulation; re-enter later with SIGUSR1

Sending `SIGUSR1` before the marker appears kills the process, because the
handler is not installed yet. `console_debugger=1` is required for the debugger
to be enterable at all.

## Quick start (driver)

Edit the `launch(...)` arguments at the bottom of
`fs-uae-debugger/driver.py` to your configuration and save state. The first
argument is the emulator binary and defaults to `fs-uae` from the `PATH`; change
it to a full path (or `$FS_UAE_BIN`) only if the binary is not on the `PATH`.
Then:

    python3 ai/fs-uae-debugger/driver.py

## Customising

- Prefer building the workflow around the parameters table above rather than
  editing `SKILL.md`, so the skill stays reusable across machines.
- To retarget a different fork or a stock FS-UAE build, review section 1 of
  `SKILL.md` — the signal-based activation is specific to this fork.

## Related documentation

- [`docs/debugging.md`](../docs/debugging.md) — programmatic activation overview.
- [`docs/options/debugger_signal.md`](../docs/options/debugger_signal.md) — the option.
- [`docs/options/console_debugger.md`](../docs/options/console_debugger.md) — required gate.
- [`docs/keyboard-shortcuts.md`](../docs/keyboard-shortcuts.md) — the equivalent hotkey.

## License

Part of FS-UAE; see the top-level `COPYING` file.
