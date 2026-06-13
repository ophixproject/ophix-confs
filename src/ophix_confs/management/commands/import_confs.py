"""
ophix-manage import_confs
~~~~~~~~~~~~~~~~~~~~~~~~~
Import Configuration records from a JSON file produced by export_confs.

Idempotent: configurations are matched by name. Existing configurations are
updated only when a field value differs; identical records are skipped. The
content and format are always written on update.

If the file includes client_links and --include-client-links is passed, the
ClientConfiguration join records are also imported. Referenced clients and
hosts must already exist — run import_hosts and import_clients first.

Configuration formats (yaml, json, etc.) are installed by data migrations and
must be present on the target server before import. Run migrate if a format is
reported as missing.

If the file was exported with --passphrase, provide the same passphrase here.
The passphrase is validated before any database changes are made.

Examples
--------
Import from a file:
    ophix-manage import_confs --input-file confs.json

Import from an encrypted file:
    ophix-manage import_confs --input-file confs.json --passphrase "secret"

Import with client links:
    ophix-manage import_confs --input-file confs.json --include-client-links

Preview without writing:
    ophix-manage import_confs --input-file confs.json --dry-run
"""

import base64
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


class Command(BaseCommand):
    help = "Import Configuration records from a JSON file produced by export_confs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-file",
            required=True,
            metavar="FILE",
            help="Source file path (JSON produced by export_confs).",
        )
        passphrase_group = parser.add_mutually_exclusive_group()
        passphrase_group.add_argument(
            "--passphrase",
            nargs="?",
            const="",
            metavar="PASSPHRASE",
            default=None,
            help="Passphrase to decrypt content (required if file was exported with --passphrase). Omit the value to be prompted securely (input is hidden).",
        )
        passphrase_group.add_argument(
            "--passphrase-env",
            metavar="ENVVAR",
            default=None,
            help="Read the passphrase from the named environment variable (for automated use).",
        )
        parser.add_argument(
            "--include-client-links",
            action="store_true",
            help="Also import ClientConfiguration join records from the file (if present).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created or updated without making any changes.",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress per-record output. Summary line is always shown.",
        )
        parser.add_argument(
            "--name",
            metavar="NAME",
            action="append",
            dest="names",
            default=None,
            help="Only import configuration(s) with this name. Repeat to specify multiple names.",
        )

    def handle(self, *args, **options):
        from ophix_confs.models import Configuration, ClientConfiguration, ConfigFormat

        input_path   = Path(options["input_file"])
        passphrase     = options["passphrase"]
        passphrase_env = options["passphrase_env"]
        if passphrase_env:
            passphrase = os.environ.get(passphrase_env)
            if not passphrase:
                raise CommandError(
                    f"Environment variable '{passphrase_env}' is not set or empty."
                )
        elif passphrase == "":
            import getpass
            passphrase = getpass.getpass("Passphrase: ")
            if not passphrase:
                raise CommandError("Passphrase cannot be empty.")
        import_links = options["include_client_links"]
        dry_run      = options["dry_run"]
        quiet        = options["quiet"]
        names        = options["names"]

        if not input_path.exists():
            raise CommandError(f"Input file not found: {input_path}")

        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {input_path}: {exc}")

        if not isinstance(payload, dict) or "configurations" not in payload:
            raise CommandError("Unrecognised file format — expected export_confs output.")

        encrypted = payload.get("encrypted", False)

        # Validate passphrase and build Fernet instance before touching the DB.
        fernet = None
        if encrypted:
            if not passphrase:
                raise CommandError(
                    "This file contains encrypted content. Provide --passphrase to import."
                )
            try:
                from cryptography.fernet import Fernet, InvalidToken
                salt = base64.urlsafe_b64decode(payload["salt"])
                fernet = Fernet(_derive_key(passphrase, salt))
                # Validate key against the first content value we can find.
                for rec in payload["configurations"]:
                    if rec.get("content"):
                        fernet.decrypt(rec["content"].encode())
                        break
            except InvalidToken:
                raise CommandError("Incorrect passphrase — could not decrypt content.")
            except Exception as exc:
                raise CommandError(f"Failed to initialise decryption: {exc}")
        elif passphrase and not quiet:
            self.stderr.write(self.style.WARNING(
                "Warning: file is not encrypted but --passphrase was provided — ignoring."
            ))

        records = payload["configurations"]
        if not isinstance(records, list):
            raise CommandError("Expected 'configurations' to be a JSON array.")

        if names:
            names_set = set(names)
            records = [r for r in records if (r.get("name") or "").strip() in names_set]
            if not records:
                raise CommandError(
                    f"No records found matching --name filter: {', '.join(sorted(names_set))}"
                )

        # Pre-load all known formats to avoid per-record DB hits.
        formats = {f.name: f for f in ConfigFormat.objects.all()}

        created = updated = unchanged = skipped = 0
        links_created = links_updated = links_unchanged = links_skipped = 0

        for i, rec in enumerate(records, 1):
            name = (rec.get("name") or "").strip()
            if not name:
                self.stderr.write(f"  Record {i}: missing 'name' — skipped.")
                skipped += 1
                continue

            # Resolve format.
            format_name = (rec.get("format") or "").strip()
            fmt = formats.get(format_name)
            if not fmt:
                self.stderr.write(
                    f"  {name}: format '{format_name}' not found — skipped. "
                    "Run migrate to ensure all configuration formats are installed."
                )
                skipped += 1
                continue

            # Decrypt content if needed.
            raw_content = rec.get("content", "")
            if fernet and raw_content:
                try:
                    from cryptography.fernet import InvalidToken
                    raw_content = fernet.decrypt(raw_content.encode()).decode()
                except InvalidToken:
                    self.stderr.write(f"  {name}: content decryption failed — skipped.")
                    skipped += 1
                    continue

            fields = {
                "description": rec.get("description") or None,
                "format":      fmt,
                "content":     raw_content,
                "enabled":     bool(rec.get("enabled", True)),
            }

            # Create or update configuration.
            conf_obj = None
            try:
                conf_obj = Configuration.objects.get(name=name)
                changed = {}
                if conf_obj.description != fields["description"]:
                    changed["description"] = fields["description"]
                if conf_obj.format_id != fmt.pk:
                    changed["format"] = fmt
                if conf_obj.content != fields["content"]:
                    changed["content"] = fields["content"]
                if conf_obj.enabled != fields["enabled"]:
                    changed["enabled"] = fields["enabled"]

                if not changed:
                    unchanged += 1
                    if not quiet:
                        self.stdout.write(f"  {name}: unchanged.")
                else:
                    if not quiet:
                        label = ", ".join(
                            f if f != "format" else f"format ({format_name})"
                            for f in changed
                        )
                        self.stdout.write(f"  {name}: updating {label}.")
                    if not dry_run:
                        try:
                            for f, v in changed.items():
                                setattr(conf_obj, f, v)
                            conf_obj.full_clean()
                            conf_obj.save()
                        except Exception as exc:
                            self.stderr.write(f"  {name}: save failed — {exc}")
                            skipped += 1
                            continue
                    updated += 1

            except Configuration.DoesNotExist:
                if not quiet:
                    self.stdout.write(f"  {name}: creating.")
                if not dry_run:
                    try:
                        conf_obj = Configuration(name=name, **fields)
                        conf_obj.full_clean()
                        conf_obj.save()
                    except Exception as exc:
                        self.stderr.write(f"  {name}: save failed — {exc}")
                        skipped += 1
                        continue
                created += 1

            # Import client links if requested.
            if import_links and rec.get("client_links"):
                if dry_run or conf_obj is None:
                    links_created += len(rec["client_links"])
                    continue

                from ophix.core.models import Client, Host
                for link_rec in rec["client_links"]:
                    client_name = (link_rec.get("client") or "").strip()
                    host_name   = (link_rec.get("host") or "").strip()

                    if not client_name or not host_name:
                        self.stderr.write(
                            f"  {name} → link: missing client or host — skipped."
                        )
                        links_skipped += 1
                        continue

                    try:
                        host   = Host.objects.get(name=host_name)
                        client = Client.objects.get(name=client_name, host=host)
                    except Host.DoesNotExist:
                        self.stderr.write(
                            f"  {name} → {host_name}/{client_name}: "
                            f"host '{host_name}' not found — skipped."
                        )
                        links_skipped += 1
                        continue
                    except Client.DoesNotExist:
                        self.stderr.write(
                            f"  {name} → {host_name}/{client_name}: "
                            f"client not found — skipped."
                        )
                        links_skipped += 1
                        continue

                    link_fields = {
                        "enabled":    bool(link_rec.get("enabled", True)),
                        "can_update": bool(link_rec.get("can_update", False)),
                        "can_delete": bool(link_rec.get("can_delete", False)),
                        "can_share":  bool(link_rec.get("can_share", False)),
                        "notes":      link_rec.get("notes") or None,
                    }

                    try:
                        link = ClientConfiguration.objects.get(
                            client=client, configuration=conf_obj
                        )
                        link_changed = {
                            f: v for f, v in link_fields.items()
                            if getattr(link, f) != v
                        }
                        if not link_changed:
                            links_unchanged += 1
                        else:
                            if not quiet:
                                self.stdout.write(
                                    f"  {name} → {host_name}/{client_name}: "
                                    f"updating {', '.join(link_changed)}."
                                )
                            try:
                                for f, v in link_changed.items():
                                    setattr(link, f, v)
                                link.save()
                            except Exception as exc:
                                self.stderr.write(
                                    f"  {name} → {host_name}/{client_name}: "
                                    f"save failed — {exc}"
                                )
                                links_skipped += 1
                                continue
                            links_updated += 1

                    except ClientConfiguration.DoesNotExist:
                        if not quiet:
                            self.stdout.write(
                                f"  {name} → {host_name}/{client_name}: creating link."
                            )
                        try:
                            ClientConfiguration.objects.create(
                                client=client, configuration=conf_obj, **link_fields
                            )
                        except Exception as exc:
                            self.stderr.write(
                                f"  {name} → {host_name}/{client_name}: "
                                f"save failed — {exc}"
                            )
                            links_skipped += 1
                            continue
                        links_created += 1

        # Build summary.
        parts = []
        if created:
            parts.append(f"{created} created")
        if updated:
            parts.append(f"{updated} updated")
        if unchanged:
            parts.append(f"{unchanged} unchanged")
        if skipped:
            parts.append(f"{skipped} skipped")
        summary = ", ".join(parts) if parts else "nothing to do"

        if import_links:
            link_parts = []
            if links_created:
                link_parts.append(f"{links_created} created")
            if links_updated:
                link_parts.append(f"{links_updated} updated")
            if links_unchanged:
                link_parts.append(f"{links_unchanged} unchanged")
            if links_skipped:
                link_parts.append(f"{links_skipped} skipped")
            link_summary = ", ".join(link_parts) if link_parts else "none"
            summary += f" | links: {link_summary}"

        if dry_run:
            self.stdout.write(f"Dry run: {summary}.")
        else:
            self.stdout.write(self.style.SUCCESS(f"{summary.capitalize()}."))
