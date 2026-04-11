"""
ophix_confs.views
~~~~~~~~~~~~~~~~
API views for the Configuration domain plugin.

GET    /api/configs/<n>/  — fetch config, returns content with correct Content-Type
POST   /api/configs/<n>/  — create new config (validates format on ingestion)
PUT    /api/configs/<n>/  — update config (validates format on ingestion)
DELETE /api/configs/<n>/  — delete config (requires can_delete + ENABLE_ARTIFACT_DELETE)
"""

import logging

from django.conf import settings
from django.http import Http404, HttpResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ophix.core.auth import ClientTokenAuthentication
from ophix.core.audit import record_access
from ophix.core.utils import assert_artifact_access, err_response

from .models import Configuration, ClientConfiguration, ConfigFormat
from .serializers import ConfigurationSerializer

logger = logging.getLogger(__name__)


class ConfigurationDetailView(APIView):
    """
    CRUD endpoint for a single named Configuration.

    GET returns the raw content with the format's Content-Type header
    rather than a JSON envelope, so clients can use the content directly
    without parsing a wrapper.  The format metadata is available in
    response headers:

        X-Ophix-Config-Format: yaml
        X-Ophix-Config-Updated: 2026-03-23T12:00:00Z
        Content-Type: application/x-yaml
    """

    authentication_classes = [ClientTokenAuthentication]

    # ------------------------------------------------------------------
    # GET — fetch
    # ------------------------------------------------------------------

    def get(self, request, name: str):
        client = request.user

        try:
            config = Configuration.objects.select_related("format").get(name=name)
        except Configuration.DoesNotExist:
            raise Http404

        access = assert_artifact_access(
            client, config, ClientConfiguration, "configuration"
        )

        record_access(access, "GET")
        # Return raw content with format-appropriate Content-Type
        response = HttpResponse(
            config.content,
            content_type=config.format.mime_type,
        )
        response["X-Ophix-Config-Format"] = config.format.name
        response["X-Ophix-Config-Updated"] = config.updated_at.isoformat()
        return response

    # ------------------------------------------------------------------
    # POST — create
    # ------------------------------------------------------------------

    def post(self, request, name: str):
        client = request.user

        if Configuration.objects.filter(name=name).exists():
            return Response(
                {"error": err_response("Configuration already exists", "Conflict")},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ConfigurationSerializer(data={**request.data, "name": name})
        serializer.is_valid(raise_exception=True)

        config = Configuration.objects.create(
            name=name,
            format=serializer.validated_data["format"],
            content=serializer.validated_data["content"],
            description=serializer.validated_data.get("description", ""),
        )

        # Creator gets full permissions
        access = ClientConfiguration.objects.create(
            client=client,
            configuration=config,
            enabled=True,
            can_update=True,
            can_delete=True,
            can_share=False,
        )

        record_access(access, "POST")
        return Response({"status": "created"}, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # PUT — update
    # ------------------------------------------------------------------

    def put(self, request, name: str):
        client = request.user

        try:
            config = Configuration.objects.select_related("format").get(name=name)
        except Configuration.DoesNotExist:
            raise Http404

        assert_artifact_access(
            client, config, ClientConfiguration, "configuration",
            require_update=True,
        )

        serializer = ConfigurationSerializer(
            config,
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"status": "updated"}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete(self, request, name: str):
        client = request.user

        if not getattr(settings, "ENABLE_ARTIFACT_DELETE", False):
            return Response(
                {"error": err_response("Configuration deletion is disabled on this server.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            config = Configuration.objects.get(name=name)
        except Configuration.DoesNotExist:
            raise Http404

        assert_artifact_access(
            client, config, ClientConfiguration, "configuration",
            require_delete=True,
        )

        config.delete()
        return Response({"status": "deleted"}, status=status.HTTP_200_OK)
