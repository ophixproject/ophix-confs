"""
State-only migration — records the verbose_name/help_text/Meta changes made
in the i18n sweep (gettext_lazy wrapping) that shipped in 2026.10.05.04
without an accompanying migration. None of these operations change any
database column type, null-ness, or default — they only affect Django's
migration state (and therefore makemigrations' ability to detect "no
changes"). Safe to apply on any existing database.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ophix_confs", "0002_initial_formats"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configformat",
            name="name",
            field=models.CharField(max_length=50, unique=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="configformat",
            name="mime_type",
            field=models.CharField(default="text/plain", max_length=100, verbose_name="MIME type"),
        ),
        migrations.AlterField(
            model_name="configformat",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="configformat",
            name="validator_class",
            field=models.CharField(
                blank=True,
                help_text="Dotted path to validator class. Leave blank for no validation.",
                max_length=200,
                null=True,
                verbose_name="validator class",
            ),
        ),
        migrations.AlterField(
            model_name="configformat",
            name="codemirror_mode",
            field=models.CharField(
                blank=True,
                help_text="CodeMirror mode name (e.g. 'yaml', 'javascript', 'xml').",
                max_length=50,
                null=True,
                verbose_name="CodeMirror mode",
            ),
        ),
        migrations.AlterField(
            model_name="configformat",
            name="codemirror_mode_file",
            field=models.CharField(
                blank=True,
                help_text="Relative path to the CodeMirror mode JS file under ophix_confs/codemirror/.",
                max_length=100,
                null=True,
                verbose_name="CodeMirror mode file",
            ),
        ),
        migrations.AlterField(
            model_name="configformat",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="name",
            field=models.CharField(max_length=100, unique=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="format",
            field=models.ForeignKey(
                help_text="Format of this configuration snippet.",
                on_delete=models.deletion.PROTECT,
                related_name="configurations",
                to="ophix_confs.configformat",
                verbose_name="format",
            ),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="content",
            field=models.TextField(
                help_text="Configuration content stored verbatim.",
                verbose_name="content",
            ),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="enabled",
            field=models.BooleanField(default=True, verbose_name="enabled"),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="updated at"),
        ),
        migrations.AlterModelOptions(
            name="configuration",
            options={
                "ordering": ("name",),
                "verbose_name": "Configuration",
                "verbose_name_plural": "Configurations",
            },
        ),
        migrations.AlterField(
            model_name="clientconfiguration",
            name="configuration",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="client_links",
                to="ophix_confs.configuration",
                verbose_name="configuration",
            ),
        ),
        migrations.AlterModelOptions(
            name="clientconfiguration",
            options={
                "verbose_name": "Client Configuration",
                "verbose_name_plural": "Client Configurations",
            },
        ),
    ]
