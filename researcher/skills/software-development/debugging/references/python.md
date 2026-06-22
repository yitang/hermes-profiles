# Python Debugger — pdb, debugpy, remote-pdb

## Quick Reference: pdb Commands

Inside any `(Pdb)` prompt:

| Command | Action |
|---------|--------|
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from function |
| `c` | continue |
| `unt N` | continue until line N |
| `l` / `ll` | list source around current / full function |
| `w` | where (stack trace) |
| `u` / `d` | move up/down in stack |
| `a` | print function args |
| `p expr` / `pp expr` | print / pretty-print |
| `display expr` | auto-print on every stop |
| `b file:line` | set breakpoint |
| `b func` | break on function entry |
| `b file:line, cond` | conditional breakpoint |
| `cl N` | clear breakpoint N |
| `tbreak file:line` | one-shot breakpoint |
| `!stmt` | execute arbitrary Python (assignments too) |
| `interact` | drop into full Python REPL (Ctrl+D to exit) |
| `q` | quit |

## Recipe: Local breakpoint

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # drops into pdb here
    return result + y
```

## Recipe: Launch under pdb

```bash
python -m pdb path/to/script.py arg1 arg2
```

## Recipe: Debug a pytest test

```bash
scripts/run_tests.sh tests/test_file.py::test_name --pdb -p no:xdist
source .venv/bin/activate
python -m pytest tests/foo_test.py::test_bar --pdb
```

## Recipe: Post-mortem

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

```bash
python -m pdb -c continue script.py   # crashes into pdb
```

## Recipe: Remote debug with debugpy

```bash
pip install debugpy
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
```

Attach from VS Code (launch.json):
```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false
}
```

## Recipe: remote-pdb (simpler than debugpy for terminal agents)

```bash
pip install remote-pdb
```

In code:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```

Connect from terminal:
```bash
nc 127.0.0.1 4444
# (Pdb) prompt appears
```

## Python-Specific Pitfalls

1. **pdb under pytest-xdist silently hangs** — always use `-p no:xdist`
2. **`breakpoint()` in CI hangs** — never commit; pre-commit grep: `rg -n 'breakpoint\\(\\)' --type py`
3. **`PYTHONBREAKPOINT=0` disables breakpoint** — check env if not hitting
4. **Attach to PID fails on hardened kernels** — `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope`
5. **pdb doesn't follow forks** — each child needs its own breakpoint
6. **asyncio** — `await` inside pdb works in 3.13+; use `interact` or `asyncio.run_coroutine_threadsafe` on older versions
7. **Threads** — pdb debugs only the current thread; use debugpy for multi-threaded code
