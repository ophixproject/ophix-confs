"""
ophix_conf.serializers
~~~~~~~~~~~~~~~~~~~~~~
"""

from rest_framework import serializers
from .models import Configuration, ConfigFormat


class ConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and writing Configuration instances.

    The format field accepts the format name (string) on write
    and returns the full format object on read.
    """

    format_name = serializers.SlugRelatedField(
        source="format",
        slug_field="name",
        queryset=ConfigFormat.objects.filter(enabled=True),
        write_only=False,
    )

    class Meta:
        model = Configuration
        fields = ["name", "description", "format_name", "content", "updated_at"]
        read_only_fields = ["name", "updated_at"]

    def validate(self, data):
        """Run format-specific content validation on write."""
        fmt = data.get("format") or (self.instance.format if self.instance else None)
        content = data.get("content") or (self.instance.content if self.instance else None)

        if fmt and content:
            validator = fmt.get_validator()
            if validator:
                # Raises ValidationError which DRF handles automatically
                validator.validate(content)

        return data
