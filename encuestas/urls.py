from django.urls import path

from . import views

app_name = "encuestas"

urlpatterns = [
    path("", views.indice, name="indice"),
    path("<int:pregunta_id>/", views.detalle, name="detalle"),
    path("<int:pregunta_id>/votar/", views.votar, name="votar"),
    path("<int:pregunta_id>/resultados/", views.resultados, name="resultados"),
]
