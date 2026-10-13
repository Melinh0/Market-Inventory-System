import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, JsonResponse
from django.urls import include, path, re_path


def spa(request, route=""):
    dist = Path(settings.FRONTEND_DIST).resolve()
    if route:
        candidate = (dist / route).resolve()
        if candidate.is_file() and candidate.is_relative_to(dist):
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            return FileResponse(open(candidate, "rb"), content_type=content_type)
    index = dist / "index.html"
    if index.is_file():
        return FileResponse(open(index, "rb"), content_type="text/html")
    return JsonResponse(
        {"detail": "Frontend não encontrado. Execute: npm run build em frontend/"},
        status=404,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("backend.inventory.urls")),
    re_path(r"^static/(?P<path>.*)$", spa, name="static-spa"),
    re_path(r"^(?P<route>[\w./-]*)$", spa, name="spa"),
]
