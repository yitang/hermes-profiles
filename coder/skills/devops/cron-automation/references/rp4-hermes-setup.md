# Hermes on Raspberry Pi 4 (aarch64 Debian Bookworm)

## System

- **Board:** Raspberry Pi 4 (1.8-4GB RAM)
- **OS:** Debian 12 Bookworm (aarch64)
- **Python:** 3.11.2 (system default)
- **Storage:** 29GB SD card (or external USB SSD/HDD)

## Installation

Hermes is not available on PyPI for direct `pip install` on ARM via `uv` (uv
doesn't bundle ARM Python binaries on all platforms). Install via pip in a
standard venv:

```bash
python3 -m venv ~/hermes-venv
~/hermes-venv/bin/pip install hermes-agent
```

The full install takes ~2-3 minutes on a Pi 4 due to cryptography compilation.

## Profile Creation

```bash
~/hermes-venv/bin/hermes profile create monitor
```

This creates `~/.hermes/profiles/monitor/` and a CLI wrapper at
`~/.local/bin/monitor`. Add to PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

Fix the wrapper (it calls `hermes` which isn't in PATH):

```bash
sed -i 's|exec hermes|exec /home/pi/hermes-venv/bin/hermes|' ~/.local/bin/monitor
```

## Setting Up a Default Profile (for `hermes chat`)

The `default` profile is special — it lives at `~/.hermes/` not
`~/.hermes/profiles/default/`. Create a minimal config:

```bash
cp ~/.hermes/profiles/monitor/config.yaml ~/.hermes/config.yaml
```

Copy the API key to the default profile's `.env`:

```bash
grep DEEPSEEK_API_KEY ~/.hermes/profiles/monitor/.env >> ~/.hermes/.env
```

Create a `hermes` CLI wrapper (optional):

```bash
cat > ~/.local/bin/hermes << 'EOF'
#!/bin/sh
exec /home/pi/hermes-venv/bin/hermes "$@"
EOF
chmod +x ~/.local/bin/hermes
```

## Skills Discovery

By default, local skills placed in `~/.hermes/profiles/<name>/skills/` are NOT
automatically discovered. Hermes only loads skills from hub sources and from
`external_dirs` in config.yaml.

Add to `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
  - ~/.hermes/profiles/<name>/skills
```

Replace `<name>` with your profile name. This makes all SKILL.md files in that
directory visible to Hermes.

## Colors / Terminal Detection

When running `hermes chat` via SSH on a Pi 4, colours may render oddly even
with `TERM=xterm-256color`. The `rich` library's `Console().color_system`
returns `None` on some ARM Linux configurations, meaning it emits no colour
codes at all.

**Fix:** Force colour output:

```bash
export RICH_FORCE_COLORS=true
hermes chat
```

Or permanently in `.bashrc`:

```bash
echo 'export RICH_FORCE_COLORS=true' >> ~/.bashrc
```

## Tapo python-kasa on ARM

python-kasa's AES transport **does not work** on Raspberry Pi 4 (aarch64, Debian
Bookworm, Python 3.11) with Tapo P110 plugs. The same library version (0.10.2)
works on macOS but fails with `LOGIN_ERROR(-1501)` on ARM. See
`references/tapo-p110-integration.md` for details.

Workaround: run Tapo polling on a different machine (e.g., a Mac that's always
on).

## File Locations (RP4 conventions)

| Item | Path |
|------|------|
| Hermes venv | `/home/pi/hermes-venv/` |
| Hermes config | `~/.hermes/config.yaml` |
| Profile configs | `~/.hermes/profiles/<name>/config.yaml` |
| Profile skills | `~/.hermes/profiles/<name>/skills/` |
| Profile .env | `~/.hermes/profiles/<name>/.env` |
| CLI wrappers | `~/.local/bin/` |
