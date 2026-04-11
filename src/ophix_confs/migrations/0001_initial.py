from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("ophix_core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfigFormat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("mime_type", models.CharField(default="text/plain", max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                ("validator_class", models.CharField(blank=True, help_text="Dotted path to validator class. Leave blank for no validation.", max_length=200, null=True)),
                ("codemirror_mode", models.CharField(blank=True, help_text="CodeMirror mode name (e.g. 'yaml', 'javascript', 'xml').", max_length=50, null=True)),
                ("codemirror_mode_file", models.CharField(blank=True, help_text="Relative path to the CodeMirror mode JS file under ophix_confs/codemirror/.", max_length=100, null=True)),
                ("enabled", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Configuration Format",
                "verbose_name_plural": "Configuration Formats",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Configuration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("content", models.TextField(help_text="Configuration content stored verbatim.")),
                ("enabled", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("format", models.ForeignKey(help_text="Format of this configuration snippet.", on_delete=django.db.models.deletion.PROTECT, related_name="configurations", to="ophix_confs.configformat")),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="ClientConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True, help_text="Client can read this artifact (can_read).")),
                ("can_update", models.BooleanField(default=False, help_text="Client may overwrite this artifact.")),
                ("can_delete", models.BooleanField(default=False, help_text="Client may delete this artifact.")),
                ("can_share", models.BooleanField(default=False, help_text="Reserved: future client-driven sharing. Currently unused.")),
                ("notes", models.TextField(blank=True, null=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="ophix_core.client")),
                ("configuration", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="client_links", to="ophix_confs.configuration")),
            ],
            options={
                "unique_together": {("client", "configuration")},
            },
        ),
    ]
