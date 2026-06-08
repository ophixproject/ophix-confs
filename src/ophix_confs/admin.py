"""
ophix_confs.admin
~~~~~~~~~~~~~~~~
Admin registrations for ConfigFormat, Configuration and ClientConfiguration.
"""

from django.contrib import admin
from django.conf import settings
from django import forms
from django.db import models
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from ophix.core.admin import CleanSaveMessageMixin
from .models import ConfigFormat, Configuration, ClientConfiguration


# ============================================================
# Client ↔ Configuration inlines
# ============================================================

class ClientConfigurationInlineForClient(admin.TabularInline):
    """
    Inline shown on Client admin: manage which configurations are attached to this client.
    Registered into ClientAdmin via AppConfig.ready().
    """
    model = ClientConfiguration
    extra = 0
    autocomplete_fields = ('configuration',)
    fields = ('configuration', 'enabled', 'notes')
    classes = ('collapse',)
    verbose_name = _("Configuration")
    verbose_name_plural = _("Configurations")
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 2, 'cols': 120})
        }
    }


class ClientConfigurationInlineForConfiguration(admin.TabularInline):
    """
    Inline shown on Configuration admin: manage which clients use this configuration.
    """
    model = ClientConfiguration
    extra = 0
    autocomplete_fields = ('client',)
    fields = ('client', 'enabled', 'notes')
    classes = ('collapse',)
    verbose_name = _("Client")
    verbose_name_plural = _("Clients")
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 2, 'cols': 120})
        }
    }


# ============================================================
# ClientAdmin column — contributed via register_column()
# ============================================================

def linked_configurations(self, obj):
    links = ClientConfiguration.objects.filter(client=obj).select_related('configuration')
    if not links:
        return "—"

    items = []
    for cc in links:
        label = cc.configuration.name
        if cc.enabled and cc.configuration.enabled:
            items.append(f"• {label}")
        else:
            items.append(
                format_html(
                    "• <span style='color: color-mix(in srgb, var(--admin-interface-delete-button-background-color) 60%, currentColor 40%); font-style: italic;'>{}</span>",
                    label,
                )
            )

    return format_html(
        "<div style='display: flex; flex-wrap: wrap; gap: 0.5em; white-space: normal;'>{}</div>",
        mark_safe(" ".join(items)),
    )

linked_configurations.short_description = _("Authorised Configurations")


# ============================================================
# ConfigFormatAdmin
# ============================================================

class ConfigFormatAdmin(CleanSaveMessageMixin, admin.ModelAdmin):
    list_display = (
        "name", "mime_type", "codemirror_mode",
        "validator_class", "enabled",
    )
    list_editable = ("enabled",)
    list_filter = ("enabled",)
    search_fields = ("name", "mime_type")
    ordering = ("name",)
    actions = None

    def get_readonly_fields(self, request, obj=None):
        # Prevent renaming existing formats — code references formats by name.
        if obj:
            return ("name",)
        return ()


if getattr(settings, "SHOW_CONFIG_FORMATS_MODEL", False):
    admin.site.register(ConfigFormat, ConfigFormatAdmin)


# ============================================================
# ConfigurationAdmin
# ============================================================

@admin.register(Configuration)
class ConfigurationAdmin(CleanSaveMessageMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'format',
        'description',
        'enabled',
        'linked_clients',
    )
    list_editable = ('enabled',)
    list_filter = ('enabled', 'format')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('updated_at',)
    inlines = [ClientConfigurationInlineForConfiguration]
    actions = None

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'content':
            try:
                from ophix_codemirror.widgets import DynamicCodeMirrorWidget
                kwargs['widget'] = DynamicCodeMirrorWidget()
            except ImportError:
                pass
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Annotate each format <option> with its codemirror_mode as a
        data-codemirror-mode attribute so DynamicCodeMirrorWidget can switch
        modes when the format dropdown changes.
        """
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "format":
            class AnnotatedSelect(forms.Select):
                def create_option(self, name, value, label, selected, index, **kwargs):
                    option = super().create_option(
                        name, value, label, selected, index, **kwargs,
                    )
                    if value:
                        try:
                            pk = value.value if hasattr(value, 'value') else value
                            fmt = ConfigFormat.objects.get(pk=pk)
                            if fmt.codemirror_mode:
                                option["attrs"]["data-codemirror-mode"] = fmt.codemirror_mode
                        except (ConfigFormat.DoesNotExist, ValueError):
                            pass
                    return option

            formfield.widget = AnnotatedSelect(
                choices=formfield.widget.choices,
                attrs=formfield.widget.attrs,
            )
            formfield.widget.choices = formfield.choices

        return formfield

    def linked_clients(self, obj):
        links = obj.client_links.select_related('client')
        if not links:
            return "—"

        items = []
        for cc in links:
            label = cc.client.name
            if cc.enabled and cc.client.enabled:
                items.append(f"• {label}")
            else:
                items.append(
                    format_html(
                        "• <span style='color: color-mix(in srgb, var(--admin-interface-delete-button-background-color) 60%, currentColor 40%); font-style: italic;'>{}</span>",
                        label,
                    )
                )

        return format_html(
            "<div style='display: flex; flex-wrap: wrap; gap: 0.5em; white-space: normal;'>{}</div>",
            mark_safe(" ".join(items)),
        )

    linked_clients.short_description = _("Authorised Clients")


# ============================================================
# ClientConfigurationAdmin (audit / debug only)
# ============================================================

if getattr(settings, "SHOW_CLIENT_ARTIFACT_MODEL", False):

    @admin.register(ClientConfiguration)
    class ClientConfigurationAdmin(CleanSaveMessageMixin, admin.ModelAdmin):
        """
        Exists primarily for auditing and debugging.
        Day-to-day management should be done via inlines.
        """
        list_display = (
            'client',
            'configuration',
            'enabled',
            'short_notes',
        )
        list_editable = ('enabled',)
        list_filter = ('enabled', 'client__host', 'client', 'configuration')
        search_fields = ('client__name', 'configuration__name', 'notes')
        actions = None
        verbose_name = _("Client-Configuration Link")
        verbose_name_plural = _("Client-Configuration Links")

        def short_notes(self, obj):
            return (obj.notes[:50] + '…') if obj.notes and len(obj.notes) > 50 else obj.notes
        short_notes.short_description = _('Notes')
