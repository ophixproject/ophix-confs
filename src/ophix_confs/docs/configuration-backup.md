---
title: Configuration Backup and Migration
slug: configuration-backup
order: 110
section: Configurations
---

Configuration records can be exported to a JSON file and imported on another server. This supports server migration, disaster recovery, and environment cloning.

Configuration content is plain text and is not encrypted by default. If your configurations contain sensitive values, use `--passphrase` to encrypt the content field in the export file.

---

## Restore dependency order

Configuration imports reference clients by name. The full restore sequence for a configuration server is:

```
import_hosts  →  import_clients  →  import_confs
```

Run `import_hosts` and `import_clients` (from `ophix-server-base`) before importing configurations with client links. See [Server Backup and Migration](server-backup) for the base-layer commands.

If you are only restoring configuration content (no client links), `import_confs` can run independently.

---

## Exporting configurations

**Export all configurations:**

```bash
ophix-manage export_confs --output-file confs.json
```

**Export with encrypted content:**

```bash
ophix-manage export_confs --output-file confs.json --passphrase 'your-passphrase'
```

**Also export client access links:**

```bash
ophix-manage export_confs --output-file confs.json --include-client-links
```

**Preview without writing:**

```bash
ophix-manage export_confs --output-file confs.json --dry-run
```

> **Note:** Always use single quotes around passphrases in bash. Double-quoted strings allow bash to interpret `!` as a history event, which corrupts a passphrase containing an exclamation mark.

| Flag | Description |
| --- | --- |
| `--output-file FILE` | _(required)_ Destination path |
| `--passphrase PASSPHRASE` | Encrypt configuration content using a PBKDF2-derived Fernet key |
| `--include-client-links` | Also export `ClientConfiguration` join records (client access and permission flags) |
| `--dry-run` | Show how many configurations would be exported without writing |
| `--quiet` | Suppress all output |

### What is exported

Each configuration record includes:

- `name` — the unique configuration identifier
- `description` — optional description text
- `format` — the format name (e.g. `yaml`, `json`, `env`)
- `content` — the configuration text (encrypted if `--passphrase` was used)
- `enabled` — whether the configuration is active

With `--include-client-links`, each record also includes its `ClientConfiguration` join records, capturing which clients have access and with what permission flags (`enabled`, `can_update`, `can_delete`, `can_share`, `notes`).

---

## Importing configurations

**Import from a file:**

```bash
ophix-manage import_confs --input-file confs.json
```

**Import from an encrypted file:**

```bash
ophix-manage import_confs --input-file confs.json --passphrase 'your-passphrase'
```

**Also import client links:**

```bash
ophix-manage import_confs --input-file confs.json --include-client-links
```

**Preview without writing:**

```bash
ophix-manage import_confs --input-file confs.json --dry-run
```

The passphrase (if provided) is validated against the first record in the file before any database changes are made.

Configurations are matched by name. Existing records are updated only when a field value differs; identical records are skipped. The import is idempotent — safe to re-run.

For client links, referenced hosts and clients must already exist on the target server. Missing hosts or clients are reported per-record and skipped; the configuration itself is still imported.

| Flag | Description |
| --- | --- |
| `--input-file FILE` | _(required)_ Source path (JSON produced by `export_confs`) |
| `--passphrase PASSPHRASE` | Decrypt content (required if file was exported with `--passphrase`) |
| `--include-client-links` | Also import `ClientConfiguration` join records from the file |
| `--dry-run` | Show what would be created or updated without making any changes |
| `--quiet` | Suppress per-record output; summary line always shown |

### Configuration formats

Formats (`yaml`, `json`, `xml`, `ini`, `toml`, `env`, `raw`) are installed by data migrations. If a format referenced in the import file is not present on the target server, that configuration is skipped with an error. Run `ophix-manage migrate` to ensure all formats are installed before importing.

---

## Full configuration server restore workflow

```bash
# 1. Export from the source server
ophix-manage export_hosts --output-file hosts.json
ophix-manage export_clients --output-file clients.json
ophix-manage export_confs --output-file confs.json --include-client-links

# 2. Transfer all three files to the target server

# 3. Import on the target server in dependency order
ophix-manage import_hosts --input-file hosts.json
ophix-manage import_clients --input-file clients.json
ophix-manage import_confs --input-file confs.json --include-client-links
```

Fleet clients can reconnect and retrieve configurations immediately after the restore without re-registering or re-linking.

---

## Scheduled backups

`ophix-manage create_backup_script` generates `ophix-backup.sh` — a cron-ready wrapper that reads `BACKUP_TARGETS` and `BACKUP_TARGETS_ENCRYPTED` from `.env` and runs the corresponding export commands.

Add to `.env` to include configurations in the scheduled backup. If configurations contain sensitive values:

```ini
BACKUP_TARGETS_ENCRYPTED=confs
```

Otherwise, add `confs` to `BACKUP_TARGETS` instead and the script will export without passphrase.
