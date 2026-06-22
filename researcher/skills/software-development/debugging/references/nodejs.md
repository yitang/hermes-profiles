# Node.js Debugger — node inspect, CDP

## Quick Reference: `node inspect` REPL

Launch paused on first line:
```bash
node inspect path/to/script.js
node --inspect-brk $(which tsx) path/to/script.ts
```

At the `debug>` prompt:

| Command | Action |
|---------|--------|
| `c` / `cont` | continue |
| `n` / `next` | step over |
| `s` / `step` | step into |
| `o` / `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | set breakpoint |
| `sb(42)` | break at line 42 current file |
| `sb('functionName')` | break on function call |
| `cb('file.js', 42)` | clear breakpoint |
| `bt` | backtrace |
| `list(5)` | show 5 lines of source |
| `watch('expr')` | watch expression |
| `repl` | JS REPL in current scope (Ctrl+C to exit) |
| `exec expr` | evaluate expression once |
| `restart` | restart script |
| `kill` | kill the script |
| `.exit` | quit debugger |

## Attaching to a Running Process

```bash
kill -SIGUSR1 <pid>                     # enable inspector on running process
node inspect -p <pid>                   # attach by PID
node inspect ws://127.0.0.1:9229/<uuid> # attach by WS URL
```

Start with inspector from the beginning:
```bash
node --inspect script.js                # listen on 9229, keep running
node --inspect-brk script.js            # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

## Programmatic CDP (chrome-remote-interface)

For scripting breakpoints and state inspection:

```bash
npm i -g chrome-remote-interface
node --inspect-brk=9229 target.js &
```

Driver script (`/tmp/cdp-debug.js`):
```javascript
const CDP = require('chrome-remote-interface');
(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId, ownProperties: true,
        });
        for (const p of result) console.log(`  ${scope.type}.${p.name} =`, p.value?.value);
      }
    }
    await Debugger.resume();
  });
  await Runtime.enable();
  await Debugger.enable();
  await Debugger.setBreakpointByUrl({ urlRegex: '.*app\\.tsx$', lineNumber: 119, columnNumber: 0 });
  await Runtime.runIfWaitingForDebugger();
})();
```

## Heap Snapshots & CPU Profiles

Swap Debugger for Profiler:
```javascript
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
```

Heap snapshot:
```javascript
const chunks = [];
client.HeapProfiler.enable();
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

## Debugging Hermes ui-tui

```bash
# Debugging an Ink component
cd hermes-agent/ui-tui
npm run build
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
# debug> sb('dist/app.js', 220); cont; repl

# Debugging running hermes --tui
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)
kill -SIGUSR1 "$TUI_PID"
node inspect -p "$TUI_PID"
```

## Node-Specific Pitfalls

1. **Wrong line numbers in TS source** — breakpoints hit emitted JS, not `.ts`. Break in `dist/*.js` or use CDP with sourcemaps
2. **`--inspect` vs `--inspect-brk`** — without `-brk`, execution races past first breakpoint
3. **Port collisions** — default 9229; use `--inspect=0` (random port) and read URL from `/json/list`
4. **Child processes** — `--inspect` on parent doesn't inspect children; use `NODE_OPTIONS='--inspect-brk'` per child
5. **`Ctrl+C` from debugger leaves target paused** — `cont` first or `kill` explicitly
6. **Security** — always bind to `127.0.0.1`
