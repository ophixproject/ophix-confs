from django.apps import AppConfig


class OphixConfsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ophix_confs"
    verbose_name = "Configurations"
    is_ophix_domain = True

    def ready(self):
        from ophix.core.admin import ClientAdmin
        from .admin import ClientConfigurationInlineForClient, linked_configurations
        ClientAdmin.register_inline(ClientConfigurationInlineForClient)
        ClientAdmin.register_column(linked_configurations)
