# -*- coding: utf-8 -*-
"""Configuración de gunicorn leída por `-c gunicorn.conf.py`.

Todo se puede pisar con variables de entorno, que es lo que hacen los hostings
(Render, Railway, Fly.io o un VPS) al inyectar `PORT` y `WEB_CONCURRENCY`.
"""

import os

# El hosting decide el puerto; en local cae en 8000.
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Sitio chico y sin base de datos: pocos procesos con hilos alcanza.
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

# Logs a la salida estándar: así los levanta el hosting.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

# Carga la app una sola vez por worker (arranque más rápido y menos memoria).
preload_app = True
