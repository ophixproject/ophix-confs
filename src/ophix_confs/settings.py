"""
ophix_confs.settings
~~~~~~~~~~~~~~~~~~~
Default settings contributed by the ophix-conf plugin.
Loaded non-destructively by ophix.settings.plugins.
"""

from ophix.settings.utils import get_bool_env

SHOW_CONFIG_FORMATS_MODEL = get_bool_env("SHOW_CONFIG_FORMATS_MODEL", default=False)
