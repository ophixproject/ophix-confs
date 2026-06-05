# Ophix Confs Release Notes

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
