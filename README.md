# Encuestas (Django + PostgreSQL)

Aplicación web de **encuestas**: muestra preguntas, permite votar por una opción y ver los resultados. Incluye el **panel de administración** de Django para crear preguntas y opciones. Está basada en la aplicación de ejemplo del tutorial oficial de Django, adaptada al español y preparada para configurarse mediante variables de entorno.

> Proyecto con fines exclusivamente educativos. Cualquiera puede votar las veces que quiera.

---

## Nivel y objetivos de aprendizaje

**Nivel:** intermedio.

Django es un framework "con baterías incluidas", y eso trae tareas extra que **no** son simplemente "arrancar el servidor". Al dockerizarla vas a practicar:

- Separar las tareas de **tiempo de construcción** (recolectar archivos estáticos) de las de **tiempo de arranque** (aplicar migraciones).
- Escribir un **script de entrada** (*entrypoint*) que prepara el entorno y luego cede el control al proceso principal.
- Configurar una app con muchas variables de entorno: clave secreta, modo depuración, hosts permitidos, base de datos.
- Servir archivos estáticos en producción **sin** un servidor web adicional (WhiteNoise).
- Crear un **superusuario** de forma no interactiva.
- Cargar **datos iniciales** (*fixtures*).
- Entender por qué no se deben ejecutar tareas de un solo uso en cada réplica.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 o superior |
| Framework | Django 6.1 |
| Servidor WSGI | Gunicorn |
| Archivos estáticos | WhiteNoise |
| Configuración de BD | `dj-database-url` (convierte `DATABASE_URL` en la configuración de Django) |
| Driver PostgreSQL | psycopg 3 (`psycopg[binary]`) |
| Base de datos | PostgreSQL 16 o 17 (si no hay `DATABASE_URL`, usa SQLite) |

---

## Arquitectura

```
 Navegador ──HTTP──▶  web (Gunicorn + Django, puerto 8000)
                         │   /            → lista de preguntas
                         │   /<id>/       → formulario de votación
                         │   /admin/      → panel de administración
                         │   /static/...  → CSS servido por WhiteNoise
                         │
                         │  TCP 5432
                         ▼
                       db (PostgreSQL)
                         └─ tablas de Django + encuestas_pregunta + encuestas_opcion
```

### Ciclo de vida de una app Django en un contenedor

| Momento | Tarea | ¿Por qué ahí? |
|---|---|---|
| Construcción de la imagen | Recolectar archivos estáticos en `STATIC_ROOT` | No depende de la base de datos; el resultado es igual para todas las réplicas. |
| Arranque del contenedor (o tarea separada) | Aplicar migraciones | Necesita la base de datos disponible. |
| Una sola vez | Crear superusuario y cargar datos iniciales | Repetirlo en cada arranque puede fallar o **sobrescribir** datos. |
| Siempre | Arrancar Gunicorn | Es el proceso principal del contenedor. |

---

## Estructura del proyecto

```
06-encuestas-django-postgres/
├── manage.py                     # Utilidad de línea de comandos de Django
├── requirements.txt              # Dependencias con versiones fijas
├── config/                       # Proyecto Django (configuración global)
│   ├── settings.py               # Lee TODA la configuración variable del entorno
│   ├── urls.py                   # Rutas raíz: encuestas, /health/ y /admin/
│   ├── wsgi.py                   # Punto de entrada WSGI (lo usa Gunicorn)
│   └── asgi.py                   # Punto de entrada ASGI (no se usa aquí)
└── encuestas/                    # Aplicación Django
    ├── models.py                 # Modelos Pregunta y Opcion
    ├── views.py                  # Vistas: índice, detalle, votar, resultados, health
    ├── urls.py                   # Rutas de la app
    ├── admin.py                  # Registro en el panel de administración
    ├── migrations/0001_initial.py# Migración inicial (ya generada)
    ├── fixtures/encuestas_iniciales.json  # 2 preguntas de ejemplo
    ├── templates/encuestas/*.html# Plantillas
    └── static/encuestas/estilos.css
```

Detalles importantes:

- **`config/settings.py`**
  - `DEBUG` es **falso** por defecto. Con `DEBUG` falso, Django **no** sirve archivos estáticos por sí mismo y exige que el host de la petición esté en `ALLOWED_HOSTS` (si no, responde `400 Bad Request`).
  - `STATIC_ROOT` es la carpeta donde se reúnen todos los estáticos (incluidos los del panel de administración). WhiteNoise los sirve desde ahí con nombres que incluyen un *hash* para el caché del navegador. **Si no se recolectaron, las páginas fallan con error 500**, porque el almacenamiento de estáticos busca un manifiesto que no existe.
  - Sin `DATABASE_URL`, usa un archivo SQLite local. Muy útil para probar rápido, pero no es lo que queremos en Compose.
- **`encuestas/views.py`**: el voto se suma con una expresión `F()` para que la base de datos haga el incremento y no se pierdan votos simultáneos. `/health/` comprueba la conexión a la base.
- **`config/wsgi.py`**: contiene la variable `application`. Gunicorn necesita la ruta `módulo:variable` hacia ella.
- **Migraciones**: ya vienen generadas en el repositorio; en el contenedor solo hay que **aplicarlas**, no generarlas.
- **Fixture**: carga 2 preguntas con IDs fijos. Si la cargas en cada arranque, **reiniciará los votos** de esas preguntas.

---

## Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `DJANGO_SECRET_KEY` | valor inseguro de desarrollo | Clave criptográfica de Django. **Obligatorio** cambiarla fuera de tu máquina. |
| `DJANGO_DEBUG` | `False` | `True` activa el modo depuración (nunca en producción). |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts aceptados, separados por comas. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | (vacío) | Orígenes de confianza para formularios, p. ej. `http://localhost:8080`. Necesario si accedes a través de un proxy con otro puerto o dominio. |
| `DATABASE_URL` | SQLite local | `postgres://USUARIO:CLAVE@HOST:5432/BASE`. |
| `DJANGO_STATIC_ROOT` | `<proyecto>/staticfiles` | Carpeta destino de los estáticos recolectados. |
| `TZ` | `UTC` | Zona horaria de la app. |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | — | Las lee el comando de Django que crea superusuarios cuando se ejecuta en modo **no interactivo**. |

---

## Rutas

| Ruta | Descripción |
|---|---|
| `/` | Lista de preguntas (muestra también el nombre del contenedor). |
| `/<id>/` | Formulario para votar. |
| `/<id>/votar/` | Recibe el voto (`POST`, protegido con CSRF). |
| `/<id>/resultados/` | Resultados de la pregunta. |
| `/health/` | `200` con el motor de base de datos en uso; `503` si no hay conexión. |
| `/admin/` | Panel de administración (requiere superusuario). |

---

## Ejecución local sin Docker (referencia)

1. Crea un entorno virtual e instala `requirements.txt`.
2. Sin definir `DATABASE_URL` se usará SQLite. Activa `DJANGO_DEBUG` para desarrollo.
3. Usa `manage.py` para aplicar migraciones, cargar el fixture `encuestas_iniciales`, crear un superusuario y arrancar el servidor de desarrollo.

---

## Reto: dockerizar la aplicación

> Pistas, no soluciones.

### Parte 1: el `Dockerfile`

1. **Imagen base** oficial de Python, variante `slim`, versión explícita.
2. Variables de Python para contenedores (*bytecode* y salida sin *buffer*).
3. **Caché de capas:** dependencias primero, código después.
4. **Recolecta los estáticos durante la construcción.** Pista: el comando de `manage.py` que lo hace necesita poder importar la configuración, pero **no** necesita la base de datos. Revisa qué variables de entorno exige `settings.py` y cuáles tienen valor por defecto.
5. **Script de entrada** (`entrypoint.sh` o similar):
   - Debe **fallar** si algún paso falla (opciones de seguridad del *shell*).
   - Aplica las migraciones.
   - Termina usando `exec` con los argumentos recibidos, para que Gunicorn reemplace al *shell* y reciba las señales directamente. Investiga la combinación de `ENTRYPOINT` + `CMD`.
   - Recuerda darle **permiso de ejecución** y cuidado con los **finales de línea de Windows** (CRLF) si editas en ese sistema.
6. **Comando por defecto:** Gunicorn apuntando al objeto WSGI de `config`, escuchando en `0.0.0.0`.
7. **Usuario sin privilegios.** ¿Necesita ese usuario escribir en alguna carpeta? (si recolectas estáticos al construir, no).
8. **`.dockerignore`:** `.venv`, `db.sqlite3`, `staticfiles/`, `__pycache__`, `.git`, `.env`.

### Parte 2: el `docker-compose.yml`

1. Servicios **web** y **db** (PostgreSQL con versión explícita, volumen con nombre y healthcheck).
2. Define todas las variables de la tabla anterior. Los **secretos** (clave de Django, contraseñas) en un `.env` ignorado por git. Genera una clave secreta aleatoria larga.
3. Ajusta `DJANGO_ALLOWED_HOSTS` y, si publicas en un puerto distinto, `DJANGO_CSRF_TRUSTED_ORIGINS`. Prueba a votar desde el navegador: si falla con **403 CSRF**, revisa esta variable.
4. La web espera a que la base esté **sana**.
5. **Tareas de un solo uso:** crea el superusuario y carga el fixture **ejecutando comandos dentro del servicio** (o con un contenedor de un solo uso) en lugar de meterlos en el *entrypoint*. Investiga la diferencia entre ejecutar un comando en un contenedor en marcha y lanzar uno nuevo y efímero del mismo servicio.
6. (Avanzado) Mueve las migraciones a un **servicio separado** que corre una vez y termina, y haz que la web dependa de que ese servicio **haya terminado correctamente** (busca las condiciones disponibles en `depends_on`).

### Criterios de aceptación

- [ ] La lista de preguntas se ve **con estilos** (el CSS carga) y el panel `/admin/` también.
- [ ] Puedes votar desde el navegador y ver resultados.
- [ ] Puedes entrar a `/admin/` con tu superusuario y crear una pregunta nueva.
- [ ] Los datos persisten tras recrear los contenedores.
- [ ] Reiniciar el contenedor web **no** reinicia los votos.
- [ ] `DJANGO_DEBUG` está desactivado y no hay secretos escritos en el `docker-compose.yml` ni en el `Dockerfile`.
- [ ] `docker compose down` detiene la web rápidamente (Gunicorn recibe la señal).

### Retos extra

- Agrega **Nginx** delante como proxy inverso y sirve los estáticos desde Nginx en lugar de WhiteNoise (pista: volumen compartido).
- Escala la web a varias réplicas. ¿Qué pasaría si cada réplica aplicara migraciones al arrancar a la vez?
- Agrega un **healthcheck** al servicio web usando `/health/` sin instalar `curl` (pista: Python ya está en la imagen).
- Crea un `compose.override.yml` de desarrollo con `DJANGO_DEBUG=True`, *bind mount* del código y el servidor de desarrollo de Django.

---

## Errores comunes

| Síntoma | Causa probable |
|---|---|
| `400 Bad Request` en todas las páginas | El host no está en `DJANGO_ALLOWED_HOSTS`. |
| `500` y en logs `Missing staticfiles manifest entry` | No se recolectaron los estáticos o `STATIC_ROOT` no coincide. |
| Página sin estilos | Igual que el anterior, o el middleware de WhiteNoise no está activo. |
| `403 Forbidden (CSRF verification failed)` al votar | Accedes desde un origen no incluido en `DJANGO_CSRF_TRUSTED_ORIGINS`. |
| `relation "encuestas_pregunta" does not exist` | No se aplicaron las migraciones. |
| `exec ./entrypoint.sh: no such file or directory` (y el archivo sí existe) | Finales de línea CRLF o falta el permiso de ejecución. |
| Los votos vuelven a 0 tras reiniciar | Estás cargando el fixture en cada arranque. |

---

## Referencias

- Tutorial oficial de Django (app de encuestas): <https://docs.djangoproject.com/es/6.1/intro/tutorial01/>
- Lista de verificación de despliegue de Django: <https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/>
- Archivos estáticos en Django: <https://docs.djangoproject.com/en/6.1/howto/static-files/deployment/>
- WhiteNoise: <https://whitenoise.readthedocs.io/>
- `ENTRYPOINT` y `CMD`: <https://docs.docker.com/reference/dockerfile/#understand-how-cmd-and-entrypoint-interact>
- Imagen oficial de PostgreSQL: <https://hub.docker.com/_/postgres>
