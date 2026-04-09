"""
ophix_conf.models
~~~~~~~~~~~~~~~~~
Domain models for the Ophix Configuration server.

ConfigFormat
    A registered configuration format (yaml, json, xml, ini, toml, env, raw).
    Drives validation on ingestion and CodeMirror syntax highlighting in the
    admin editor.  New formats are added by appending rows to this table via
    a data migration in a new package version.

Configuration
    A named configuration snippet stored verbatim as text.
    The format determines how it is validated on write and what
    Content-Type header is returned on read.

ClientConfiguration
    Join table linking a Client to a Configuration with per-link
    permission flags inherited from ClientArtifactBase.
"""

from django.db import models
from ophix.core.models import ClientArtifactBase


class ConfigFormat(models.Model):
    """
    A supported configuration format.

    Fields
    ------
    name
        Short identifier used in the API and .env files (e.g. ``yaml``).
    mime_type
        MIME type returned in the Content-Type header when serving this format.
    description
        Human-readable description shown in the admin.
    validator_class
        Dotted Python path to a validator class implementing
        ``ophix_conf.validators.base.BaseValidator``.
        Null means no validation is performed (raw format).
    codemirror_mode
        CodeMirror mode name (e.g. ``yaml``, ``javascript``, ``xml``).
        Null means the plain text editor is used.
    codemirror_mode_file
        Relative path to the CodeMirror mode JS file under the
        ``ophix_conf/codemirror/`` static directory.
        Null means no mode file is loaded.
    enabled
        If False, this format cannot be used for new configurations.
        Existing configurations are unaffected.
    """

    name = models.CharField(max_length=50, unique=True)
    mime_type = models.CharField(max_length=100, default="text/plain")
    description = models.TextField(blank=True, null=True)
    validator_class = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Dotted path to validator class. Leave blank for no validation.",
    )
    codemirror_mode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="CodeMirror mode name (e.g. 'yaml', 'javascript', 'xml').",
    )
    codemirror_mode_file = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Relative path to the CodeMirror mode JS file under ophix_conf/codemirror/.",
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Configuration Format"
        verbose_name_plural = "Configuration Formats"

    def __str__(self) -> str:
        return self.name

    def get_validator(self):
        """
        Instantiate and return the validator for this format, or None.
        """
        if not self.validator_class:
            return None
        from importlib import import_module
        module_path, class_name = self.validator_class.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, class_name)()


class Configuration(models.Model):
    """
    A named configuration snippet stored verbatim.

    Content is stored as raw text and returned to clients exactly as stored.
    The format field drives validation on ingestion and the Content-Type
    header on retrieval.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    format = models.ForeignKey(
        ConfigFormat,
        on_delete=models.PROTECT,
        related_name="configurations",
        help_text="Format of this configuration snippet.",
    )
    content = models.TextField(
        help_text="Configuration content stored verbatim.",
    )
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.format})"


class ClientConfiguration(ClientArtifactBase):
    """
    Join table linking a Client to a Configuration.

    Inherits enabled, can_update, can_delete, can_share from
    ClientArtifactBase.  The creating client receives all permissions;
    admin-created links default to read-only.
    """

    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="client_links",
    )

    class Meta:
        unique_together = ("client", "configuration")

    def __str__(self) -> str:
        return f"{self.client} → {self.configuration}"
