---
name: debugging
description: "Language-aware debugging: pdb/breakpoint for Python, node inspect/CDP for Node.js. Covers local breakpoints, remote attach to running processes, Hermes-specific processes, and DAP protocol for CI/agent environments."
version: 1.0.0
author: Hermes Agent (consolidated from python-debugpy + node-inspect-debugger)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, pdb, debugpy, node-inspect, breakpoints, dap, python, nodejs, troubleshooting]
    related_skills: [systematic-debugging, test-driven-development]
---

# Debugging — Language-Aware Debugger Orchestration

When `print()` / `console.log()` isn't enough. This umbrella covers the shared patterns for debugging any language, with language-specific details in the reference files.

## Core Principle

**ALWAYS find root cause before attempting fixes.** Symptom fixes are failure. See the `systematic-debugging` skill for the investigation methodology.

## Tool Selection

| Situation | Tool | Reference |
|-----------|------|-----------|
| Python: local, quick | `breakpoint()` then `(Pdb)` REPL | `references/python.md` |
| Python: no source edits | `python -m pdb script.py` | `references/python.md` |
| Python: remote/headless | `debugpy` or `remote-pdb` | `references/python.md` |
| Node.js: quick | `node inspect` built-in REPL | `references/nodejs.md` |
| Node.js: scriptable | CDP via `chrome-remote-interface` | `references/nodejs.md` |
| Node.js: CPU profile/heap | Profiler via CDP | `references/nodejs.md` |

## Shared Workflow

### 1. Local breakpoint (language-independent pattern)

Add a breakpoint in the source code, run normally:

**Python:** `breakpoint()` — drops into pdb REPL at that line.
**Node.js:** `node inspect script.js` — built-in V8 inspector REPL.

Always remove breakpoints before committing:
```bash
rg -n 'breakpoint\\(\\)' --type py      # Python
rg -n 'debugger' --type ts --type js    # Node
```

### 2. Launch under debugger (no source edits)

```bash
# Python
python -m pdb path/to/script.py arg1 arg2

# Node.js
node inspect path/to/script.js
# or paused on first line:
node --inspect-brk path/to/script.js
```

### 3. Attach to a running process

For long-lived processes (servers, daemons, gateways):

**Python (debugpy):**
```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```
```bash
# Via CLI:
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
# Attach to PID:
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

**Node.js:**
```bash
# Start process with inspector
node --inspect-brk script.js       # paused on first line
# Or enable on running process
kill -SIGUSR1 <pid>
# Attach
node inspect -p <pid>
node inspect ws://127.0.0.1:9229/<uuid>
```

### 4. Debug tests

```bash
# Python (pytest)
scripts/run_tests.sh tests/test_file.py::test_name --pdb -p no:xdist
python -m pytest tests/foo_test.py::test_bar --pdb

# Node.js (vitest)
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/test_file.ts
# Then in another terminal: node inspect -p <pid>
```

**Always disable parallel execution for debugging** — xdist/vitest parallelism breaks breakpoint-driven debugging.

## Hermes-Specific Process Debugging

| Process | Language | Strategy |
|---------|----------|----------|
| Gateway (`gateway/run.py`) | Python | `remote-pdb` at handler, or `debugpy --wait-for-client` on restart |
| `tui_gateway` subprocess | Python | Source-edit with `debugpy.listen` or `remote-pdb` |
| `_SlashWorker` subprocess | Python | `remote-pdb` with `set_trace()` in exec path |
| ui-tui Ink components | TypeScript | `node --inspect-brk dist/entry.js` |
| Running `hermes --tui` | TS+Python | `kill -SIGUSR1 <node-pid>` for Node; debugpy/remote-pdb for Python |

## Common Pitfalls (Language-Agnostic)

1. **Breakpoints under parallel test runners silently fail** — disable xdist (pytest), use `--no-file-parallelism` (vitest)
2. **Attach vs launch** — `--inspect`/`debugpy.listen` runs code immediately; `--inspect-brk`/`wait_for_client` pauses on first line
3. **Port collisions** — default 9229 (Node) or 5678 (debugpy); check with `ss -tlnp` or `curl json/list`
4. **Subprocesses don't inherit debugger** — each process needs its own breakpoint/setup
5. **Background kills** — killing the debugger leaves the target paused; continue first or kill explicitly
6. **Security** — always bind to `127.0.0.1` unless in an isolated network
7. **Check env vars** — `PYTHONBREAKPOINT=0` disables Python breakpoints
