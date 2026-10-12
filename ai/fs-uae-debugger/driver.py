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
