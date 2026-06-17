# Bitwarden Setup: macOS Safari + Linux Chrome

Session-specific workflow from 2026-06-17. User runs macOS 12.7.6 with
Chrome on a separate Linux machine. Both machines need unified password
management.

## Account Creation
- https://vault.bitwarden.com (or .eu for UK/EU data residency)
- **Important: do NOT let Chrome fill/save the master password.** Create it yourself using a long passphrase (4+ random words). Chrome saving the master password creates a circular dependency and a single point of failure.
- Write master password on paper — no recovery mechanism

## macOS Safari Extension

The Safari extension is **not** a standalone App Store download — it's bundled
with the Bitwarden desktop app:

1. Install **Bitwarden** from the Mac App Store (desktop app)
2. Open the app, log in with your master password
3. Safari → Settings → Extensions → find **Bitwarden** in the list → enable it
4. The Bitwarden icon appears in the Safari toolbar

If Bitwarden doesn't appear in the Extensions list, restart Safari and try again.

## Linux Chrome Extension
1. Open Chrome → Chrome Web Store
2. Search "Bitwarden"
3. "Add to Chrome"
4. Log in with master password

## Chrome Password Export (on Linux)
1. Chrome → `chrome://password-manager/settings`
2. Scroll to bottom → click **Export passwords**
3. Saves as CSV file

Note: the old path `chrome://settings/passwords` was removed in recent Chrome versions. If you don't see the Export button, try clicking the hamburger menu (top-left) → Settings first.

## Import to Bitwarden
1. https://vault.bitwarden.com → Log in
2. Tools → Import Data
3. Format: "Chrome (csv)"
4. Select the exported CSV → Import

## iCloud Keychain Bridge (Monterey — no native export)

Apple removed the bulk export button from Monterey. To migrate Safari passwords:

1. On macOS, install Apple's **iCloud Passwords** Chrome extension (Chrome Web
   Store, by Apple)
2. Sign in with your Apple ID — Safari passwords sync into Chrome
3. Export from Chrome (see above) → import to Bitwarden
4. Uninstall the iCloud Passwords extension

This is the only safe automated bulk path. Manual migration is fine for
users with < 20 passwords.

## Disable Native Auto-Fill

After Bitwarden is active on both machines, disable the built-in managers:

**Safari:**
- Safari → Settings → AutoFill → uncheck "Usernames and passwords"

**Chrome:**
1. Go to `chrome://password-manager/settings`
2. Turn off "Offer to save passwords and passkeys"
3. Turn off "Sign in automatically"

If you skip this, both Bitwarden and the browser will pop up simultaneously
on every login form.

## CLI Install (Linux)
```bash
curl -sSfLo bw.zip "https://vault.bitwarden.com/download/?app=cli&platform=linux"
unzip bw.zip
sudo mv bw /usr/local/bin/
bw --help
```

## CLI Usage
```bash
bw login                    # First-time login (email + password)
export BW_SESSION=$(bw unlock --raw)  # Unlock, get session token
bw get password example.com  # Get password for a service
bw generate -uln 30         # Generate random 30-char password
bw export --format json     # Export full vault to JSON
```

## Cost
- Free tier: unlimited passwords, 2 devices, 1 user
- Premium ($10/yr): TOTP authenticator, file attachments, vault health reports
