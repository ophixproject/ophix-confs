# Ophix Confs Release Notes

## Unreleased

- `export_confs` gains a `--stable` flag: omits the `meta` block and passes `sort_keys=True`,
  so re-exporting unchanged data produces byte-identical output. Written for
  `ophix-revisions`. Not yet compatible with `--passphrase`/`--passphrase-env` together —
  Fernet encryption's own random IV/timestamp means encrypted output can never be
  byte-identical across runs; combining `--stable` with a passphrase now raises a clear
  error instead of silently producing non-reproducible "stable" output.
- Fixed a latent nondeterminism bug in `--include-client-links`: the nested
  `client_links` join query had no explicit `.order_by()`, so row order (and therefore
  export order) wasn't guaranteed stable across runs even for unchanged data. Now ordered
  by `client__host__name, client__name`.
- `ophix_confs` gains `get_revisions_targets()`, declaring its own `confs` target for
  `ophix-revisions` (if installed) to discover at runtime — no separate registration
  needed anywhere else.

## 2026.06.09.01

- Fixed `export_clients --passphrase` shown in the restore workflow — client tokens are
  stored as SHA-256 hashes and `export_clients` does not accept or require a passphrase.
- Added "Scheduled backups" section to `configuration-backup.md` with recommended `.env` values.

## 2026.06.05.02

- `export_confs`: export file now includes a `meta` block with `created_at`, `server_name`, `server_version`, `hostname`, `domain`, `command`, `run_by`, `login_user`, and `ssh_origin`.
- `export_confs`, `import_confs`: `--passphrase` now accepts no value to prompt securely (export confirms twice); `--passphrase-env ENVVAR` reads the passphrase from an environment variable for automated use. Both options are mutually exclusive.

## 2026.05.30.01

- Added `export_confs` management command — exports Configuration records to
  JSON. Content can be encrypted with `--passphrase`. Use `--include-client-links`
  to also export ClientConfiguration join records.
- Added `import_confs` management command — imports from an `export_confs` file.
  Idempotent (matched by name); formats resolved by name (must exist via migrate).
  `--include-client-links` imports join records; referenced clients and hosts
  must already exist. Supports `--dry-run` and `--quiet`.
- Added inline documentation page "Configuration Backup and Migration".

## 2026.05.26.01

- Added `OPHIX_RELEASE_NOTES.md` for release notes delivery.
