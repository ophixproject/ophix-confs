"""
Data migration — populate the initial set of ConfigFormat rows.

These are the formats shipped with ophix-conf out of the box.
New formats are added in subsequent migrations as new package versions
are released, alongside the corresponding validator and CodeMirror
mode files.
"""

from django.db import migrations


INITIAL_FORMATS = [
    {
        "name": "json",
        "mime_type": "application/json",
        "description": "JavaScript Object Notation",
        "validator_class": "ophix_confs.validators.JsonValidator",
        "codemirror_mode": "javascript",
        "codemirror_mode_file": "mode/javascript.min.js",
        "enabled": True,
    },
    {
        "name": "yaml",
        "mime_type": "application/x-yaml",
        "description": "YAML Ain't Markup Language",
        "validator_class": "ophix_confs.validators.YamlValidator",
        "codemirror_mode": "yaml",
        "codemirror_mode_file": "mode/yaml.min.js",
        "enabled": True,
    },
    {
        "name": "xml",
        "mime_type": "application/xml",
        "description": "Extensible Markup Language",
        "validator_class": "ophix_confs.validators.XmlValidator",
        "codemirror_mode": "xml",
        "codemirror_mode_file": "mode/xml.min.js",
        "enabled": True,
    },
    {
        "name": "ini",
        "mime_type": "text/plain",
        "description": "INI configuration file (requires section headers)",
        "validator_class": "ophix_confs.validators.IniValidator",
        "codemirror_mode": "properties",
        "codemirror_mode_file": "mode/properties.min.js",
        "enabled": True,
    },
    {
        "name": "toml",
        "mime_type": "application/toml",
        "description": "Tom's Obvious Minimal Language",
        "validator_class": "ophix_confs.validators.TomlValidator",
        "codemirror_mode": "toml",
        "codemirror_mode_file": "mode/toml.min.js",
        "enabled": True,
    },
    {
        "name": "env",
        "mime_type": "text/plain",
        "description": "Environment variable file (.env / dotenv format)",
        "validator_class": "ophix_confs.validators.EnvValidator",
        "codemirror_mode": "properties",
        "codemirror_mode_file": "mode/properties.min.js",
        "enabled": True,
    },
    {
        "name": "raw",
        "mime_type": "text/plain",
        "description": "Raw text — no validation, no syntax highlighting",
        "validator_class": None,
        "codemirror_mode": None,
        "codemirror_mode_file": None,
        "enabled": True,
    },
]


def create_formats(apps, schema_editor):
    ConfigFormat = apps.get_model("ophix_confs", "ConfigFormat")
    for fmt in INITIAL_FORMATS:
        ConfigFormat.objects.get_or_create(name=fmt["name"], defaults=fmt)


def delete_formats(apps, schema_editor):
    ConfigFormat = apps.get_model("ophix_confs", "ConfigFormat")
    ConfigFormat.objects.filter(
        name__in=[f["name"] for f in INITIAL_FORMATS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ophix_confs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_formats, reverse_code=delete_formats),
    ]
