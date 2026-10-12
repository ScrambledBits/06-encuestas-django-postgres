from django.contrib import admin

from .models import Opcion, Pregunta


class OpcionEnLinea(admin.TabularInline):
    model = Opcion
    extra = 2


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ["texto", "publicada_en"]
    search_fields = ["texto"]
    inlines = [OpcionEnLinea]
