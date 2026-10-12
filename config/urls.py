from django.contrib import admin
from django.urls import include, path

from encuestas.views import health

urlpatterns = [
    path("", include("encuestas.urls")),
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
]
