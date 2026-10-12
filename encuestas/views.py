import socket

from django.db import connection
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Opcion, Pregunta


def indice(request):
    return render(
        request,
        "encuestas/indice.html",
        {"preguntas": Pregunta.objects.all(), "contenedor": socket.gethostname()},
    )


def detalle(request, pregunta_id):
    pregunta = get_object_or_404(Pregunta, pk=pregunta_id)
    return render(request, "encuestas/detalle.html", {"pregunta": pregunta})


def votar(request, pregunta_id):
    pregunta = get_object_or_404(Pregunta, pk=pregunta_id)
    try:
        opcion = pregunta.opciones.get(pk=request.POST["opcion"])
    except (KeyError, ValueError, Opcion.DoesNotExist):
        return render(
            request,
            "encuestas/detalle.html",
            {"pregunta": pregunta, "error": "Selecciona una opción."},
            status=400,
        )
    # F() hace el incremento en la base de datos y evita condiciones de carrera.
    Opcion.objects.filter(pk=opcion.pk).update(votos=F("votos") + 1)
    return redirect("encuestas:resultados", pregunta_id=pregunta.id)


def resultados(request, pregunta_id):
    pregunta = get_object_or_404(Pregunta, pk=pregunta_id)
    return render(request, "encuestas/resultados.html", {"pregunta": pregunta})


def health(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse(
            {"estado": "error", "base_de_datos": "sin conexion"}, status=503
        )
    return JsonResponse({"estado": "ok", "base_de_datos": connection.vendor})
