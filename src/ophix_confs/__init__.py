plugin_category = "module"
plugin_sort = 110


def install_configure(conf, command):
    """configure_install hook: contribute this domain's backup target."""
    existing = conf.get("backup", "targets_extra", fallback="")
    conf.set("backup", "targets_extra", ",".join(filter(None, [existing, "confs"])))

