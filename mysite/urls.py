from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("Plataforma_logistica/", include("Plataforma_logistica.urls")),
    path("admin/", admin.site.urls),
]