# GPG Key Backup Strategy

**Premise:** GPG private keys are irrecoverable. If lost, files encrypted to
that key are permanently inaccessible. This user has lost GPG keys before and
had files become undecryptable.

## Backup Checklist

Store your private key in at least **two** of these:

### 1. Bitwarden Secure Note (convenient online backup)

```bash
# Export your private key (ASCII-armored)
gpg --export-secret-keys --armor <KEY-ID> > my-private-key.asc

# Also export the revocation certificate
gpg --gen-revoke --armor <KEY-ID> > revoke.asc
```

Upload `my-private-key.asc` and `revoke.asc` as attachments to a Bitwarden
secure note entry titled "GPG Key Backup".

### 2. Encrypted USB Drive (cold storage)

- Copy `.asc` files to a USB drive
- Encrypt the USB with LUKS (Linux) or FileVault/APFS encrypted volume (macOS)
- Store the USB in a safe place (ideally off-site from the primary machine)

### 3. Paper Backup (physical)

Print the key fingerprint and the revocation cert. Store with important
documents. Only useful for proving key compromise + revoking, not for
recovering the actual key.

## What to Export

For each GPG key pair:

```bash
# Public key (safe to share) — export this for .gitconfig signing too
gpg --export --armor <KEY-ID> > public-key.asc

# Private key (keep secret!) — this is what you need for recovery
gpg --export-secret-keys --armor <KEY-ID> > private-key.asc

# Revocation certificate (proves you asked for this key to be revoked)
gpg --gen-revoke --armor <KEY-ID> > revoke.asc
```

## Testing Your Backup

```bash
# On a fresh machine or temp directory:
gpg --import private-key.asc
echo "test" | gpg --encrypt --recipient <KEY-ID> > /tmp/test.gpg
gpg --decrypt /tmp/test.gpg
# Should output: test
```

If decryption works, the backup is valid.

## Notes

- Bitwarden stores attached files encrypted at rest — acceptable as one layer
  of the backup strategy, but not the sole source of truth
- Key rotation is not a substitute for backup — rotated keys still can't
  decrypt files encrypted with the old key
- Export to paper via `paperkey` utility:
  ```bash
  gpg --export-secret-keys <KEY-ID> | paperkey --output key.txt
  # Prints the key data compactly for paper storage
  ```
