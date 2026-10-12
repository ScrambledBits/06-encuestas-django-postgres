from django.db import models


class Pregunta(models.Model):
    texto = models.CharField(max_length=200)
    publicada_en = models.DateTimeField("fecha de publicación", auto_now_add=True)

    class Meta:
        ordering = ["-publicada_en"]
        verbose_name_plural = "preguntas"

    def __str__(self):
        return self.texto

    def total_votos(self):
        return sum(opcion.votos for opcion in self.opciones.all())


class Opcion(models.Model):
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.CASCADE, related_name="opciones"
    )
    texto = models.CharField(max_length=200)
    votos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"

    def __str__(self):
        return self.texto
