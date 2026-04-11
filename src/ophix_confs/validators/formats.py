"""
ophix_confs.validators.formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Concrete validators for each supported configuration format.

All validators use only Python standard library modules for parsing
so there are no additional dependencies beyond what ships with Python.

JsonValidator       json
YamlValidator       yaml (requires PyYAML, listed as a dependency)
XmlValidator        xml.etree.ElementTree
IniValidator        configparser
TomlValidator       tomllib (Python 3.11+) / tomli (fallback)
EnvValidator        stub — treated as raw, validates key=value lines
RawValidator        no-op — accepts any content
"""

from django.core.exceptions import ValidationError
from .base import BaseValidator


class JsonValidator(BaseValidator):
    """Validates JSON content using the standard library json module."""

    def validate(self, content: str) -> None:
        import json
        try:
            json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSON: {exc}") from exc


class YamlValidator(BaseValidator):
    """Validates YAML content using PyYAML (safe_load)."""

    def validate(self, content: str) -> None:
        try:
            import yaml
        except ImportError as exc:
            raise ValidationError(
                "PyYAML is required for YAML validation. "
                "Install it with: pip install pyyaml"
            ) from exc
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise ValidationError(f"Invalid YAML: {exc}") from exc


class XmlValidator(BaseValidator):
    """Validates XML content using the standard library xml.etree.ElementTree."""

    def validate(self, content: str) -> None:
        import xml.etree.ElementTree as ET
        try:
            ET.fromstring(content)
        except ET.ParseError as exc:
            raise ValidationError(f"Invalid XML: {exc}") from exc


class IniValidator(BaseValidator):
    """
    Validates INI content using the standard library configparser.

    configparser requires at least one section header — bare key=value
    files without a section header will fail.  If you need to support
    headerless INI files, use the EnvValidator or RawValidator instead.
    """

    def validate(self, content: str) -> None:
        import configparser
        import io
        parser = configparser.ConfigParser()
        try:
            parser.read_file(io.StringIO(content))
        except configparser.Error as exc:
            raise ValidationError(f"Invalid INI: {exc}") from exc


class TomlValidator(BaseValidator):
    """
    Validates TOML content.

    Uses tomllib (Python 3.11+ standard library) with tomli as a
    fallback for older Python versions.
    """

    def validate(self, content: str) -> None:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError as exc:
                raise ValidationError(
                    "TOML validation requires Python 3.11+ or the tomli package. "
                    "Install it with: pip install tomli"
                ) from exc
        try:
            tomllib.loads(content)
        except tomllib.TOMLDecodeError as exc:
            raise ValidationError(f"Invalid TOML: {exc}") from exc


class EnvValidator(BaseValidator):
    """
    Stub validator for .env / dotenv format.

    Currently performs minimal validation — checks that non-comment,
    non-blank lines follow the KEY=value convention.  This is intentionally
    permissive since .env files have no strict specification.

    Extend this class in a future version to add stricter validation
    if required.
    """

    def validate(self, content: str) -> None:
        errors = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            # Skip blank lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            # Allow export KEY=value syntax
            if stripped.startswith("export "):
                stripped = stripped[7:].strip()
            # Must contain = with a non-empty key
            if "=" not in stripped:
                errors.append(f"Line {lineno}: missing '=' in '{line.rstrip()}'")
                continue
            key, _, _ = stripped.partition("=")
            if not key.strip():
                errors.append(f"Line {lineno}: empty key in '{line.rstrip()}'")

        if errors:
            raise ValidationError(
                "Invalid .env format:\n" + "\n".join(errors)
            )


class RawValidator(BaseValidator):
    """
    No-op validator — accepts any content without validation.
    Used for the 'raw' format and as a safe fallback.
    """

    def validate(self, content: str) -> None:
        pass  # All content is valid for raw format
