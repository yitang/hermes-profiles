---
name: secret-management-setup
description: >-
  Use when the user wants to set up a cross-platform password manager (Bitwarden,
  KeePassXC, 1Password) across macOS Safari and Linux Chrome, migrate passwords
  between managers (Chrome export, iCloud Keychain import), or back up GPG/SSH
  keys. Handles the full lifecycle: choosing a provider, account creation,
  browser extension install, password export/import, CLI setup, and GPG key
  backup as secure notes. Also covers pitfalls like dual-vault divergence and
  GPG key loss.
---

# Secret Management Setup

## Overview

Helps users set up unified secret management across macOS Safari and Linux
Chrome. The core pattern: one vault accessible from both platforms, with a
proper backup strategy for cryptographic keys that cannot be recovered if lost.

## Choosing a Provider

| Provider | macOS | Linux | Cost | Best For |
|----------|-------|-------|------|----------|
| Bitwarden | Safari ext, Desktop | Chrome ext, CLI | Free / $10/yr Premium | Cross-platform, open source |
| KeePassXC | Safari ext | Chrome ext, native | Free | Offline-first, no cloud |
| 1Password | Native app | Chrome ext | ~$3/mo sub | Polished UX |

**Recommended default:** Bitwarden — works identically on both platforms,
open source, CLI for Linux power users, free tier handles everything most
people need.

## Bitwarden Setup

### 1. Account
- Sign up at https://vault.bitwarden.com (or .eu for UK/EU data residency — functionally identical)
- **Master password: create it yourself, do NOT let Chrome/iCloud Keychain save or fill it.** If Chrome manages it, anyone with access to Chrome can open the vault, and you'd be locked out if Chrome's password DB corrupts. Use a long passphrase (4+ random words with hyphens).
- Write the master password **on paper**, store physically — Bitwarden cannot reset it

### 2. Browser Extensions
- **macOS Safari:** Install the **Bitwarden desktop app** from Mac App Store first.
  The Safari extension is bundled with the app — open the app, log in, then go to
  Safari → Settings → Extensions → enable Bitwarden. It is NOT a standalone
  App Store extension.
- **Linux Chrome:** Chrome Web Store → search "Bitwarden" → Add to Chrome
- Log in to the extension on both machines — vault syncs automatically

### 3. Migrate from Chrome Passwords
1. On the machine with Chrome passwords: open `chrome://password-manager/passwords`
   (the new UI; the old `chrome://settings/passwords` no longer exists).
   Click the hamburger menu (top-left) → Settings, then scroll to the bottom
   for **Export passwords** — saves as CSV. If the button isn't visible, look
   for a three-dot menu next to "Search passwords" on the Passwords page.
2. Bitwarden web vault → Tools → Import Data → choose "Chrome (CSV)" format →
   upload the file

### 4. Migrate from iCloud Keychain (macOS Monterey and earlier)
Apple provides no native bulk export from iCloud Keychain on Monterey. The only
safe automated path:
1. On macOS, install Apple's official **iCloud Passwords** Chrome extension
   (Chrome Web Store)
2. It syncs Safari/iCloud passwords into Chrome on the Mac
3. Export from Chrome to CSV (step 3 above) → import to Bitwarden
4. Uninstall the iCloud Passwords extension

Alternatively: let Bitwarden capture passwords naturally as you log in to sites,
or manually copy the 10–20 most important ones from System Settings → Passwords.

### 5. Disable Native Auto-Fill (both browsers)
Once Bitwarden is active, disable **both** browsers' built-in managers to avoid
conflicting fill popups:

- **Safari:** Safari → Settings → AutoFill → turn off "Usernames and passwords"
- **Chrome:** `chrome://password-manager/settings` → turn off **"Offer to save
  passwords and passkeys"** AND **"Sign in automatically"**

### 6. CLI (Linux optional)
```
curl -sSfLo bw.zip "https://vault.bitwarden.com/download/?app=cli&platform=linux"
unzip bw.zip && sudo mv bw /usr/local/bin/
```

## GPG Key Backup

GPG private keys are unrecoverable if lost — encrypted files become permanently
inaccessible. Store them in **at least two** of:

1. **Bitwarden secure note** — export key as `.asc`, attach to vault entry
   (convenient online backup, not sole source of truth)
2. **Encrypted USB drive** — offline cold storage
3. **Paper backup** — print key fingerprint + revocation cert, store physically

**Do not rely on only one copy.** The user has lost GPG keys before.

## Pitfalls

- **Dual vault divergence** — using iCloud Keychain on macOS and Chrome on Linux
  creates two separate vaults that drift apart. Pick one manager and use it
  everywhere.
- **Master password loss** — Bitwarden/KeePassXC have no password reset.
  Write it down physically before clicking Create.
- **Master password not saved in browser** — never let Chrome/Safari fill or
  save the master password. Creates a circular dependency: if Chrome's DB
  corrupts or someone accesses your Chrome profile, the vault is either locked
  out or exposed.
- **Conflicting auto-fill popups** — after enabling Bitwarden, you must disable
  the browser's native password manager too, or both will offer to fill/save
  passwords on the same page. Disable Chrome's built-in manager at
  `chrome://password-manager/settings`.
- **GPG key loss** — unlike passwords, GPG keys cannot be rotated. Files
  encrypted to a lost key are permanently inaccessible. Always have cold storage.

## See Also

- `references/bitwarden-macos-linux.md` — full step-by-step from this session
- `references/gpg-key-backup.md` — GPG export and backup commands
