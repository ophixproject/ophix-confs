plugin_category = "module"
plugin_sort = 110


def install_configure(conf, command):
    """configure_install hook: contribute this domain's backup target."""
    existing = conf.get("backup", "targets_extra", fallback="")
    conf.set("backup", "targets_extra", ",".join(filter(None, [existing, "confs"])))


def get_doc_tokens():
    """
    Optional hook discovered by ophix-docs (if installed), for {{ token }}
    substitution in shared markdown like the Client Quickstart doc.
    """
    return {
        "client_package": "ophix-conf-client",
        "client_command": "conf-client",
        "client_venv": ".conf-env",
        "client_env": ".conf.env",
        "client_env_prefix": "CONFSERVER",
        "artifact_name": "Configuration",
        "artifact_name_lower": "configuration",
    }


def get_revisions_targets():
    """
    Optional hook discovered by ophix-revisions (if installed). `encrypted` is the default
    classification only — an operator can still force this target into
    REVISION_TARGETS_ENCRYPTED, which export_confs's own --stable guard
    then rejects until Phase B (deterministic encryption) lands, since it's
    only ever run unencrypted for now.
    """
    return [
        {
            "name": "confs",
            "app_label": "ophix_confs",
            # Precise model match — export_confs only exports Configuration
            # rows. ConfigFormat is a lookup table referenced by FK, not
            # itself exported; ClientConfiguration join records need
            # --include-client-links, which the revisions worker never passes.
            "models": ["ophix_confs.configuration"],
            "export_command": "export_confs",
            "encrypted": False,
            "stable": True,
        },
    ]

