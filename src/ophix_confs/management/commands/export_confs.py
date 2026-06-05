"""
ophix-manage export_confs
~~~~~~~~~~~~~~~~~~~~~~~~~
Export Configuration records to a JSON file for backup or server migration.

Configuration content is plain text and exported without encryption by default.
If any configurations contain sensitive values, use --passphrase to encrypt the
content field with a PBKDF2-derived Fernet key; the same passphrase is required
by import_confs on the receiving server.

Use --include-client-links to also export the ClientConfiguration join table
(which clients have access to which configurations and with what permissions).
On import, referenced clients and hosts must already exist — run import_hosts
and import_clients first when doing a full server restore.

Examples
--------
Export all configurations:
    ophix-manage export_confs --output-file confs.json

Export with encrypted content:
    ophix-manage export_confs --output-file confs.json --passphrase "secret"

Export with client links included:
    ophix-manage export_confs --output-file confs.json --include-client-links

Preview without writing:
    ophix-manage export_confs --output-file confs.json --dry-run
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


def _serialize(configuration, fernet=None, include_links=False):
    content = configuration.content
    if fernet:
        content = fernet.encrypt(content.encode()).decode()

    record = {
        "name":        configuration.name,
        "description": configuration.description,
        "format":      configuration.format.name,
        "content":     content,
        "enabled":     configuration.enabled,
    }

    if include_links:
        links = []
        for link in configuration.client_links.select_related("client__host").all():
            links.append({
                "client":     link.client.name,
                "host":       link.client.host.name,
                "enabled":    link.enabled,
                "can_update": link.can_update,
                "can_delete": link.can_delete,
                "can_share":  link.can_share,
                "notes":      link.notes,
            })
        record["client_links"] = links

    return record


class Command(BaseCommand):
    help = "Export Configuration records to a JSON file for backup or server migration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-file",
            required=True,
            metavar="FILE",
            help="Destination file path.",
        )
        passphrase_group = parser.add_mutually_exclusive_group()
        passphrase_group.add_argument(
            "--passphrase",
            nargs="?",
            const="",
            metavar="PASSPHRASE",
            default=None,
            help="Encrypt configuration content using a passphrase-derived Fernet key. Omit the value to be prompted securely (input is hidden).",
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
            help="Also export ClientConfiguration join records (client access permissions).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many configurations would be exported without writing anything.",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress all output.",
        )

    def handle(self, *args, **options):
        from ophix_confs.models import Configuration

        output_path   = Path(options["output_file"])
        passphrase    = options["passphrase"]
        passphrase_env = options["passphrase_env"]
        if passphrase_env:
            passphrase = os.environ.get(passphrase_env)
            if not passphrase:
                raise CommandError(
                    f"Environment variable '{passphrase_env}' is not set or empty."
                )
        elif passphrase == "":
            import getpass
            while True:
                passphrase = getpass.getpass("Passphrase: ")
                if not passphrase:
                    raise CommandError("Passphrase cannot be empty.")
                confirm = getpass.getpass("Confirm passphrase: ")
                if passphrase == confirm:
                    break
                self.stderr.write("Passphrases do not match — try again.")
        include_links = options["include_client_links"]
        dry_run       = options["dry_run"]
        quiet         = options["quiet"]

        configurations = list(
            Configuration.objects.select_related("format").order_by("name")
        )
        count = len(configurations)

        if dry_run:
            self.stdout.write(
                f"Dry run: {count} configuration(s) would be exported to {output_path}."
            )
            return

        if count == 0:
            if not quiet:
                self.stdout.write("No configurations found — nothing to export.")
            return

        if not output_path.parent.exists():
            raise CommandError(f"Output directory does not exist: {output_path.parent}")

        fernet = None
        salt_b64 = None
        if passphrase:
            from cryptography.fernet import Fernet
            salt = os.urandom(16)
            salt_b64 = base64.urlsafe_b64encode(salt).decode()
            fernet = Fernet(_derive_key(passphrase, salt))

        payload = {
            "version":              1,
            "encrypted":            fernet is not None,
            "salt":                 salt_b64,
            "include_client_links": include_links,
            "configurations":       [
                _serialize(c, fernet, include_links) for c in configurations
            ],
        }

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        if not quiet:
            enc_note  = " (content encrypted)" if fernet else ""
            link_note = ", with client links" if include_links else ""
            self.stdout.write(self.style.SUCCESS(
                f"Exported {count} configuration(s) to {output_path}{enc_note}{link_note}."
            ))
