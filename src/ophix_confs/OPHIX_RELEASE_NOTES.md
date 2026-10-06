# Ophix Confs Release Notes

## Unreleased

- Added `get_doc_tokens()` hook, discovered by `ophix-docs` (if installed) for
  `{{ token }}` substitution in shared markdown. Contributes `client_package`
  (`ophix-conf-client`) and `client_command` (`conf-client`) so the generic
  Client Quickstart doc in `ophix-server-base` can render this domain's correct
  example instead of staying generic.

## 2026.10.05.04

- Fixed the `Tier 2 usage` example in the `configurations` inline doc: `from ophix_conf_client
  import get_config` was never a valid import — the pip package `ophix-conf-client` strips its
  `ophix-` prefix for the actual Python module name (`conf_client`). Found while sweeping git
  history for a public-release pass. `conf_client`'s own `__init__.py` docstring documents the
  correct top-level form; now reads `from conf_client import get_config`.

## 2026.10.05.03

- `TomlValidator` (`validators/formats.py`) falls back to the `tomli` package on Python
  versions older than 3.11, where the `tomllib` standard-library module doesn't exist yet.
  That fallback was never actually usable, though — this package's own floor is Python
  3.10, but `tomli` was never declared as a dependency, so a real 3.10 install had nothing
  to fall back to; TOML-format configurations would raise "TOML validation requires Python
  3.11+ or the tomli package" with no way to resolve it short of a manual `pip install
  tomli`. Added `tomli>=2.0; python_version < '3.11'` to `dependencies` so it's installed
  automatically wherever it's actually needed, and skipped entirely on 3.11+ where the
  standard-library module already covers it.

## 2026.10.05.02

- Added the `Programming Language :: Python :: 3.14` classifier, after real verification
  (not a rubber-stamp add): a fresh Python 3.14 venv, a live `migrate` through this
  package's full migration history, real HTTP requests against every registered admin
  page (changelist with disabled-row styling, add-form, change-form), a real
  `export_confs`/`import_confs` round trip (both with and without `--stable`), and all six
  format validators (JSON/YAML/XML/INI/TOML/.env) exercised directly, including their
  error-message paths. All passed.
- Found and fixed a real (non-3.14-specific) portability bug along the way: `_build_meta()`
  in `export_confs.py` had the identical `import pwd` issue as `ophix-creds`'s
  `export_creds.py` (see that package's release notes) — an unconditional top-level import
  inside a function whose own surrounding `try/except` was meant to tolerate exactly this
  failure mode. Moved the import inside the `try`.

## 2026.10.05.01

- i18n regression sweep, ahead of this domain's own public-release pass:
  - `models.py` — every field across `ConfigFormat`/`Configuration`/`ClientConfiguration` now has
    a translated `verbose_name`, not just `help_text` on some of them; added missing
    `Meta.verbose_name`/`verbose_name_plural` to `Configuration` and `ClientConfiguration`.
  - `views.py` — wrapped the two fleet-API error strings in `ConfigurationDetailView`
    ("Configuration already exists" / "Conflict" and "Configuration deletion is disabled on this
    server."), matching the corrected convention from the taskserver wave's own i18n pass (every
    known Tier 1 client branches purely on HTTP status code, never parses this text).
  - `validators/formats.py` — wrapped every `ValidationError` message across all six format
    validators (JSON/YAML/XML/INI/TOML/.env). Also fixed a real latent bug found while doing
    this: `EnvValidator.validate()` used a bare `key, _, _ = stripped.partition("=")` throwaway
    assignment that would have silently shadowed the newly-added `gettext_lazy as _` import for
    the rest of the function — renamed to `_sep`/`_val`.

## 2026.08.30.01

- Disabled-client/disabled-configuration styling in the "Authorised
  Configurations" (Client admin) and "Authorised Clients" (Configuration
  admin) linked-artifact columns changed from an italic red-tinted mix
  (`color-mix(..., var(--admin-interface-delete-button-background-color) ...)`)
  to the theme's dedicated disabled colour at a heavier weight, italic kept
  (`var(--admin-interface-disabled-color); font-weight: 600; font-style:
  italic`), matching the same treatment applied fleet-wide to changelist
  disabled rows.

## 2026.08.04.01

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
