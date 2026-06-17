# Hermes on Raspberry Pi 4 — Setup Guide

Captured from a real setup session (June 2026). RP4 runs Debian 12 Bookworm,
1.8GB RAM, aarch64, Python 3.11.2.

## Setup steps

```bash
# System deps
sudo apt-get install -y python3-venv python3-pip

# Create venv and install Hermes
python3 -m venv ~/hermes-venv
~/hermes-venv/bin/pip install --upgrade pip
~/hermes-venv/bin/pip install hermes-agent

# Create a profile
~/hermes-venv/bin/hermes profile create monitor

# The installer creates a wrapper at ~/.local/bin/<profile-name>
# Fix the wrapper to use full path to the Hermes binary:
sed -i 's|exec hermes|exec /home/pi/hermes-venv/bin/hermes|' ~/.local/bin/monitor

# Create a general 'hermes' wrapper
cat > ~/.local/bin/hermes << 'EOF'
#!/bin/sh
export TERM=xterm-256color
exec /home/pi/hermes-venv/bin/hermes "$@"
EOF
chmod +x ~/.local/bin/hermes

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Config

Copy the config from an existing profile (e.g. the Mac's coder profile).
Strip any local-model providers (e.g. qwen-36-35b pointing to a local server
that may be off). Keep only the cloud API providers:

```yaml
model:
  default: deepseek-v4-flash
  provider: custom:deepseek-v4-flash
providers:
  deepseek-v4-flash: deepseek-v4-flash
  deepseek-v4-pro: deepseek-v4-pro
fallback_providers:
- custom: deepseek-v4-flash
custom_providers:
- base_url: https://api.deepseek.com
  name: deepseek-v4-flash
  model: deepseek-v4-flash
- base_url: https://api.deepseek.com
  name: deepseek-v4-pro
  model: deepseek-v4-pro
```

## API key

Add `DEEPSEEK_API_KEY=sk-...` to `~/.hermes/.env` (for the default profile)
or to `~/.hermes/profiles/<name>/.env` (for a named profile).

## Skills

Local skills are NOT auto-discovered. You must add them to config.yaml:

```yaml
skills:
  external_dirs:
  - ~/.hermes/profiles/default/skills
```

To copy skills from another machine: `scp -r <source>/skills/* <rpi>:~/.hermes/profiles/default/skills/`

The `hermes skills install` command does **not** support local file paths.
Only HTTP URLs are accepted as identifiers.

## Color fix over SSH

The default Hermes skin uses 24-bit truecolor escape codes that render
incorrectly over many SSH connections. **Add this to config.yaml as a
permanent fix:**

```yaml
skin: daylight
```

If the skin switch alone doesn't work, also set:
```bash
export RICH_FORCE_COLORS=true
```

See the "Hermes colors broken over SSH" quirk in the parent skill for
details and alternative fixes.

## Cron jobs (now working)

The gateway runs successfully on RP4 with `hermes gateway run --force`.
Cron jobs can be created with:

```bash
# v0.16 syntax: schedule is positional, NOT --schedule flag
hermes cron create --name "my-job" --script ~/scripts/poll.py --no-agent "*/15 * * * *"
```

Key gotcha: `--schedule` is NOT a valid flag in v0.16. The schedule
expression is a positional argument at the end.

To make cron persistent across SSH disconnects, run the gateway in a
`tmux` or `screen` session rather than relying on launchd (which isn't
set up on the RP4).

## Known limitations

- **python-kasa Tapo auth fails** — the AES transport cannot authenticate
  with Tapo P110 plugs from RP4. Root cause unknown; workaround is to run
  Tapo cron on a different machine.
- **No local LLM** — the RP4 has no GPU and only 1.8GB RAM. All inference
  goes through the cloud API.
- **launchd not available** — use `tmux` + `hermes gateway run --force`
  for persistent gateway sessions instead of a systemd service.
