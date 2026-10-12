---
name: fs-uae-debugger
description: | 
  Drive the built-in console debugger of the Robbson's fs-uae-3 fork
  interactively: launch with a user-supplied config and save state, activate the
  debugger programmatically (SIGUSR1 / debugger_signal), run debugger commands,
  breakpoints and memory watchpoints, read and interpret the output, and re-run
  deterministically from the same point. Use when asked to debug, trace, inspect
  memory/registers, or reverse-engineer a program running under this FS-UAE build.
---

# Skill: run and drive the FS-UAE built-in debugger

You are controlling a *specific build*: the [Robbson/fs-uae](https://github.com/Robbson/fs-uae) fork, branch
`fs-uae-3` (default). It adds the `debugger_signal` option, which lets a controller put
the emulator into its built-in console debugger by sending `SIGUSR1`, with no
keyboard interaction. Use that instead of GUI hotkeys or synthetic X11 input.

## 0. Parameters the user must supply

Collect these before starting. Do not guess.

| Parameter | Meaning | Example |
|---|---|---|
| `FS_UAE_BIN` | optional override for the binary; defaults to `fs-uae` on the `PATH` | `/opt/FS-UAE/bin/fs-uae` |
| `CONFIG` | `.fs-uae` configuration file | `~/FS-UAE/Configurations/HotShot.fs-uae` |
| `SAVE_STATE` | save-state slot number, `1`–`9` | `2` |
| `EXTRA_ARGS` | optional extra options | `--automatic_input_grab=0` |

`SAVE_STATE` maps to the option `load_state` (`1`–`9`). Save states live under
`$HOME/FS-UAE/Save States/<configuration-name>/`. The emulated machine and
Kickstart come from `CONFIG`. The emulator binary is `fs-uae` on the `PATH`;
`FS_UAE_BIN` overrides this only when it is not on the `PATH`.

## 1. Prerequisites the agent must assume about the host

- POSIX host (Linux/macOS). `SIGUSR1` activation is not available on Windows.
- The binary was built from this fork and is available as `fs-uae` on the
  `PATH` (otherwise provide `FS_UAE_BIN`). Verify once: `fs-uae --help` prints
  `FS-UAE 3.x` (fork versions start at 3.3.0), and
  `strings -a "$(command -v fs-uae)" | grep debugger_signal` finds the option.
- A writable FS-UAE base dir (`$HOME/FS-UAE`) with the Kickstart ROM and the
  floppy/hard-disk images referenced by `CONFIG`, plus the chosen save state.

## 2. Launch

Always enable both options, and route the log to stdout so you can see the
safety marker and correlate activity:

    fs-uae \
      --console_debugger=1 \
      --debugger_signal=1 \
      --stdout \
      --load_state=<SAVE_STATE> \
      <EXTRA_ARGS> \
      <CONFIG>

- `console_debugger=1` is required — the debugger is only *available* when it is
  set (same rule as the F12+D hotkey).
- `debugger_signal=1` installs the `SIGUSR1` handler.
- `--load_state=N` boots directly at the captured point.
- Use `$FS_UAE_BIN` in place of `fs-uae` if the binary is not on the `PATH`.
- Recommended `EXTRA_ARGS`: `--automatic_input_grab=0` for unattended runs.

Launch it as a child process you control, with a pipe/PTY for **stdout** and a
pipe for **stdin**. Do not launch it through a shell wrapper if you need a clean
pid; if you must, find the emulator pid with `pgrep -f '<CONFIG basename>'`.

## 3. Activate the debugger (critical safety rule)

The `SIGUSR1` handler is installed early in startup. Sending `SIGUSR1` **before**
it is installed uses the default action and **kills the process**. So:

1. Wait until this line appears on stdout:

       debugger_signal: sending SIGUSR1 will activate the debugger (requires console_debugger)

   (Fallback if you cannot read stdout: sleep ~5 s after launch.)
2. Send the signal to the **fs-uae** pid:

       kill -USR1 <fs-uae-pid>

3. The debugger activates on the next emulated frame, prints register state,
   then prompts with `>`. If `console_debugger` were off, you would instead see
   `WARNING: Option "console_debugger" is not enabled` and no prompt.

Re-send `SIGUSR1` to re-enter the debugger after each `g` (resume).

## 4. The console protocol

- Everything the debugger prints goes to **stdout**; it never echoes your input.
- The prompt is a single `>` (no newline), explicitly flushed before it blocks
  on input. Treat the trailing `>` as the **synchronisation token**: after writing
  a command, read stdout until the buffer ends with `>`.
- Send one command per line, terminated by `\n`, to the child's **stdin**.
- An empty line is a no-op (it just re-prompts).
- `g` resumes emulation (leaves the debugger). `q` **quits the emulator**.
- Caveat: `>` can occur inside dumped ASCII memory or strings. If that matters,
  prefer structured commands (registers, single memory lines) and treat only a
  `>` at the very end of a read burst as the prompt, or place a marker command
  before/after an ambiguous dump.

Minimal reference driver (adapt to your language):

```python
import os, time, select, signal, subprocess

def launch(fs_uae, config, state, extra=()):
    p = subprocess.Popen(
        [fs_uae, "--console_debugger=1", "--debugger_signal=1", "--stdout",
         f"--load_state={state}", *extra, config],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p

def read_until(p, token=b">", timeout=15.0):
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([p.stdout], [], [], max(0, end - time.time()))
        if not r:
            break
        chunk = os.read(p.stdout.fileno(), 4096)
        if not chunk:
            break
        buf += chunk
        if buf.rstrip().endswith(token):
            break
    return buf

def cmd(p, line, **kw):
    p.stdin.write((line + "\n").encode()); p.stdin.flush()
    return read_until(p, **kw)

p = launch("fs-uae", "/path/Game.fs-uae", 2, ["--automatic_input_grab=0"])

# wait for the safety marker (or sleep), then activate
read_until(p, token=b"activate the debugger", timeout=30)   # consume boot log
os.kill(p.pid, signal.SIGUSR1)
print(read_until(p))                 # register dump + first prompt

print(cmd(p, "?"))                   # authoritative command list
print(cmd(p, "r"))                   # registers
print(cmd(p, "m 40000 8"))           # memory dump
print(cmd(p, "f 1234"))              # toggle breakpoint at $1234
print(cmd(p, "g"))                   # resume  (no trailing prompt now)
# ... process runs; re-enter with SIGUSR1 later ...
```

## 5. Command reference (run `?` at runtime for the authoritative list)

Prompt helpers / navigation
- `?` — print the help/command list. `?<value>` — hex/bin/dec converter and calculator (`$`/`0x`, `%`, `!`).
- `g [<address>]` — start execution (resume), optionally from `<address>`.
- `t [instructions]` — step N instructions (default 1). `z` — step one instruction, stepping over JSR/DBRA.
- `q` — quit the emulator (avoid unless ending the session).

Inspection
- `r` — dump CPU registers. `r <reg> <value>` — modify (Dx,Ax,USP,ISP,VBR,…,PC).
- `m <address> [<lines>]` — memory dump.
- `d <address> [<lines>]` — disassembly.
- `e` — dump custom registers (AGA: `ea` for colors). `c` — CIA/disk/custom state.
- `i [<addr>]` — interrupt/trap vectors. `dm` — address-space map.
- `H[H] <cnt>` — PC history (HH = full CPU info).
- `T` / `Tt` — exec tasks and PCs. `Td,Tl,Tr,Tp,Ts,TS,Ti,TO,TM` — devices/libs/resources/ports/semaphores/residents/interrupts/doslist/memorylist.

Breakpoints / control flow
- `f` — step forward until PC is in RAM (boot-block finder).
- `f <address>` — add/remove a breakpoint. `f <addr1> <addr2>` — break when `addr1 <= PC <= addr2`.
- `fl` — list breakpoints. `fd` — remove all breakpoints.
- `fi` — step until RTS/RTD/RTE; `fi <opcode>` — until opcode.
- `fp "<name>"/<addr>` — step until process is active.
- `fa <address> [<start>] [<end>]` — find effective address.
- `fs <lines> | <vpos> <hpos>` / `fc <CCKs>` — wait n scanlines / color clocks.
- `fS <val> <mask>` — break when `(SR & mask) = val`.
- `od` — toggle Copper vpos/hpos tracing. `ot` — Copper single step. `ob <addr>` — Copper breakpoint.
- `il [<mask>]` — exception breakpoint. `smc [0-1]` — self-modifying-code detector (1 = break). `wd [0-1]` — illegal-access logger (1 = break).
- `di <mode> [<track>]` — break on disk access (`R/W/RW/P`).

Memory watchpoints and patching (fork-enhanced)
- `w <num> <address> <length> <FLAGS> [<value>[.x]]` — add/remove watchpoint.
  - Access letters: `R` read, `W` write, `I` opcode, `F` freeze, `C` mustchange, `L` logonly, `N` nobreak (may be space-separated).
  - `logonly` (`L`) prints the hit and keeps running; `nobreak` (`N`) records but does not stop; `mustchange` (`C`) only fires when the value changes.
  - Numeric watch modes also accept access masks such as `CPUDW`, `CPUD`, `CPUI`, `BLT`, `COP`, `DSK`, `AUD0-3`, `BPL0-7`, `SPR0-7`, `DMA`, `ALL`, `NONE`.
- `W <address> <values…>` or `W <address> 'string'` — write to Amiga memory.
- `s "<string>"/<values> [<addr>] [<length>]` — search memory.
- `S <file> <addr> <n>` — save a block of emulated memory to a host file.
- `C <value>` / `Cl` / `D[idxzs …]` — value/trainer search helpers.
- `sp <addr> [<addr2>][<size>]` — sprite info. `o <0-2|addr> [<lines>]` — view as Copper instructions.
- `v <vpos> [<hpos>]`, `v [-1..-4]` — DMA data / visual DMA debugger. `vh [<ratio> <lines>]` — heat map.
- `M<a|b|s> <val>` — mask audio channels / bitplanes / sprites.

Output format: with `enhanced_memwatch_outputs = 1` (a fork option) hit
messages report the *watched* value, the Amiga frame counter as first column,
zero-padded fields; `debug_log = 1` additionally writes them to
`FS-UAE/Cache/Logs/fs-uae.log.txt`.

## 6. Core workflows

**A. Start paused at a save state, then explore**
1. Launch (section 2). 
2. Wait for the marker, `SIGUSR1`.
3. `r`, `dm`, `m`, `d` to orient.
4. Set breakpoints/watches.
5. `g` to run; on a hit you are back at the `>` prompt with the reason printed (`Breakpoint at XXXXXXXX`, or a `Memwatch …` line).

**B. Breakpoint on a routine and inspect it**
```
f 1234          ; toggle breakpoint at $001234
fl              ; confirm
g               ; run; execution stops at $001234
r               ; registers at hit
d PC 10         ; disassemble around PC
m <ptr> 4       ; inspect a pointer
g               ; continue
```

**C. Non-intrusive watch (no stop)**
```
w 1 000400 2 W L       ; log writes to $000400, keep running
w 2 000574 2 RW C      ; stop on change of the word at $000574
g
```

**D. Re-run from the same point deterministically**
Relaunch a fresh process with the same `--load_state=N`. Loading a save state
restores the machine; the run is repeatable. Within one process you can also
just `g` and later re-`SIGUSR1`. Do not use `q` mid-iteration unless you intend
to end the whole emulator; to stop a run, terminate the child process instead.

## 7. Interpreting output

- Register dump (`r`): D0–D7/A0–A7, PC, SR/CCR, stacks, then disassembly at PC.
- Memory dump (`m`): rows of hex words plus ASCII; addresses are 24/32-bit as
  configured by the model.
- Disassembly (`d`): address, opcode bytes, mnemonic.
- `Breakpoint at XXXXXXXX` — a breakpoint/watchpoint fired; the following `>`
  prompt means you can issue commands.
- `Memwatch n: …` — a watchpoint hit; columns are address, access width
  (B/W/L), access type, value, `PC=`, access class (e.g. `CPUDW`), and with the
  enhanced option a leading frame counter.
- `WARNING: Activated debugger` — the debugger was entered (emitted once per
  activation).

## 8. Failure modes and cautions

- **Signal too early ⇒ process killed.** Always wait for the marker first.
- **No prompt after activation.** `console_debugger=1` missing, or you signalled
  the wrong pid (e.g. a shell wrapper instead of fs-uae). Check the log.
- **Prompt lost in output.** When a dump/string may contain `>`, only treat a
  trailing `>` as the prompt.
- **Buffering.** The debugger flushes stdout before each prompt, so pipes work;
  if you see stalls with certain tools, use a PTY instead.
- **Save state must match the config** (same machine/model); a mismatched state
  will fail to load.
- **One debugger at a time.** All commands go through the single stdin console;
  serialise commands and always read to the prompt before sending the next.
- Windows builds have no `SIGUSR1` path; this skill targets POSIX hosts.
