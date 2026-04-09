"""
ophix_conf.urls
~~~~~~~~~~~~~~~
URL patterns contributed by the ophix-conf plugin.
"""

from django.urls import path
from .views import ConfigurationDetailView

urlpatterns = [
    path(
        "api/configs/<str:name>/",
        ConfigurationDetailView.as_view(),
        name="configuration-detail",
    ),
]
