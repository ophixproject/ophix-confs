# Ophix Confs Release Notes

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
