# Norte de Jujuy · guía de viaje (Flask)

Guía de la Quebrada de Humahuaca y la Puna servida con **Flask**: Python arma el
HTML con plantillas Jinja y todas las secciones se generan en el servidor.

## Cómo correrla en local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py                  # http://localhost:8000
```

Con recarga en caliente, como en desarrollo:

```bash
.venv/bin/flask --app app run --host 0.0.0.0 --port 8000 --debug
```

## Cómo está organizado

| Archivo | Qué contiene |
| --- | --- |
| `app.py` | Rutas, fechas de la agenda, filtros, Dijkstra de distancias y armado de cada sección. |
| `wsgi.py` | Punto de entrada para producción (`wsgi:app`). |
| `datos.json` | Contenido: pueblos y alturas, tramos, agenda, peñas, itinerarios, destinos, regiones y checklist. |
| `estadisticas.json` | Indicadores de la EOH de DIPEC que muestra la sección «Turismo en números». Se regenera con el script de `scripts/`. |
| `scripts/actualizar_estadisticas.py` | Baja la planilla de la EOH de DIPEC y reescribe `estadisticas.json`. |
| `scripts/controlar_antiguedad.py` | Falla si el período de `estadisticas.json` tiene más de dos meses de atraso. |
| `fotos.py` | Metadatos de las fotos de las tarjetas (autoría y licencia) y color de cada región. |
| `templates/index.html` | Plantilla Jinja: todo el marcado, con bucles sobre los datos. |
| `static/css/styles.css` | Diseño. |
| `static/js/site.js` | Solo dos cosas: enviar el formulario de filtros y recordar el checklist. |
| `static/img/` | Logo, mapas de las regiones y las fotos de las tarjetas. |
| `gunicorn.conf.py` | Configuración del servidor de producción. |
| `Procfile` | Orden de arranque para Railway, Heroku y similares. |
| `render.yaml` | Blueprint de Render (servicio, comando de arranque y variables). |
| `Dockerfile` | Imagen para Fly.io, Railway o cualquier VPS. |

## Rutas

| URL | Qué hace |
| --- | --- |
| `/` | Página completa (todas las secciones). |
| `/?pueblo=Tilcara&mes=2&destacados=1#agenda` | Agenda filtrada por pueblo, mes y destacadas. |
| `/?itin=clasico#plan` | Itinerario activo (`corta`, `clasico`, `extendido`, `yungas`). |
| `/?origen=jujuy&destino=hornocal#plan` | Calculador: distancia por Dijkstra sobre los tramos. |
| `/salud` | Health check en JSON (lo usa el hosting). |

## Publicarla

La app necesita Python, así que no entra en un hosting estático: hace falta un
servicio que corra un proceso (Render, Railway, Fly.io, un VPS).

### Variables de entorno

| Variable | Obligatoria | Para qué |
| --- | --- | --- |
| `SECRET_KEY` | sí en producción | Clave de Flask. En Render el blueprint la genera sola. |
| `PORT` | no | La inyecta el hosting; en local cae en 8000. |
| `WEB_CONCURRENCY` | no | Procesos de gunicorn (por defecto 2). |
| `GUNICORN_THREADS` | no | Hilos por proceso (por defecto 4). |
| `LOG_LEVEL` | no | `info` por defecto. |
| `FLASK_DEBUG` | no | Solo para `python app.py`: 1 muestra el depurador de Flask. |

Nunca subas el archivo `.env` al repo: está en `.gitignore`. `.env.example`
muestra qué lleva cada variable.

### Opción A · Render (la más corta)

1. Subí el repo a GitHub.
2. En Render: **New → Blueprint**, elegí el repo. Render lee `render.yaml` y crea
   el servicio solo, con `SECRET_KEY` generada y `PYTHON_VERSION` 3.12.7.
3. Si preferís crear el servicio a mano: tipo **Web Service**, runtime Python,
   build `pip install -r requirements.txt`, start
   `gunicorn -c gunicorn.conf.py wsgi:app`, health check `/salud`.
4. El plan gratuito duerme el servicio tras un rato sin visitas; la primera
   visita después de eso tarda unos segundos en despertar.

### Opción B · Docker (Fly.io, Railway o un VPS)

```bash
docker build -t norte-de-jujuy .
docker run --rm -p 8000:8000 -e SECRET_KEY=una-clave-larga norte-de-jujuy
```

En Fly.io: `fly launch` (detecta el Dockerfile) y `fly secrets set SECRET_KEY=...`.
En un VPS: el contenedor arriba con `-d --restart unless-stopped` y un proxy
(Nginx o Caddy) adelante para el HTTPS.

### Opción C · Cualquier host con Procfile

Railway y Heroku leen el `Procfile`:

```
web: gunicorn -c gunicorn.conf.py wsgi:app
```

Cargá `SECRET_KEY` en el panel de variables y listo.

### Después de publicar

- Revisá que `/salud` devuelva `{"estado":"ok",...}`.
- Confirmá que las fotos cargan: `/static/img/fotos/aves.jpg`.
- Si vas a usar dominio propio, agregalo en el panel del hosting; el `ProxyFix`
  de `app.py` ya está puesto para que las URLs y el HTTPS salgan bien detrás del
  proxy.

## Actualizar las estadísticas

La sección «Turismo en números» se alimenta de la **Encuesta de Ocupación
Hotelera** que publica DIPEC Jujuy. Cuando salen datos nuevos alcanza con un
comando:

```bash
pip install -r requirements-scripts.txt   # una sola vez: xlrd y openpyxl
python3 scripts/actualizar_estadisticas.py
```

El script lee la página de la EOH, encuentra la planilla del último año
publicado, la descarga, extrae las cuatro regiones y reescribe
`estadisticas.json`. Después, `git diff` muestra qué cambió y con un push se
publica.

Opciones útiles:

```bash
python3 scripts/actualizar_estadisticas.py --seco           # ver sin escribir
python3 scripts/actualizar_estadisticas.py --anio 2025      # un año concreto
python3 scripts/actualizar_estadisticas.py --archivo eoh.xls --anio 2026   # sin red
```

### Actualización automática

El workflow `.github/workflows/estadisticas.yml` hace esto solo: corre el script
el día 10 de cada mes (y cuando se lo dispara a mano desde **Actions →
Actualizar estadísticas EOH → Run workflow**). Si `estadisticas.json` cambió, lo
commitea a `main` con el período en el mensaje y Render publica el deploy; si no
hay datos nuevos, el script deja el archivo igual y el workflow termina sin
commit.

El workflow declara `permissions: contents: write`, que es lo que habilita el
push: GitHub permite ajustar los permisos del token por workflow, aunque el
repo tenga el valor por defecto en solo lectura. La única excepción es una
política de la organización que lo impida; en ese caso hay que poner *Workflow
permissions* en «Read and write» desde **Settings → Actions → General**.

Para comprobarlo sin esperar al mes, al dispararlo a mano desde **Actions** el
workflow hace un `git push --dry-run`: si el token no puede escribir, falla ahí
mismo con un mensaje que dice qué revisar.

### Avisos de falla y de datos viejos

Si la corrida falla (DIPEC cambió el formato, la descarga viene vacía, el push
se rechaza), el workflow abre un issue con la etiqueta `estadisticas` y el
enlace al run. Si ya había uno abierto, suma un comentario en vez de abrir otro,
para no llenar el repo de avisos repetidos. Cuando una corrida vuelve a salir
bien, comenta el issue y lo cierra solo.

El workflow también corre `scripts/controlar_antiguedad.py`, que mira la
antigüedad del período de `estadisticas.json`: si el último mes publicado quedó
más de **dos meses** atrás, la corrida falla a propósito y el aviso llega al
mismo issue. Sin ese control, un mes sin datos nuevos se ve igual que un mes sin
publicación de DIPEC y la sección quedaría vieja en silencio.

```bash
python3 scripts/controlar_antiguedad.py                    # usa estadisticas.json
python3 scripts/controlar_antiguedad.py --max-meses 3      # tolera más atraso
python3 scripts/controlar_antiguedad.py --hoy 2027-03-15   # simula otra fecha
```

El issue incluye el nombre del paso que falló y qué mirar según el caso. Para
probar el aviso de falla sin esperar un problema real, se dispara el workflow a
mano con la opción **«Provocar un fallo a propósito para probar el aviso»**.

Notas:

- El script no corre en el servidor: lo ejecuta el workflow (o vos a mano) y el
  resultado se versiona, así el sitio sigue funcionando aunque DIPEC no esté
  disponible.
- Si DIPEC cambia el nombre de las hojas o el formato del archivo, el script
  corta con un mensaje claro en vez de escribir números raros.
- Los meses que la planilla marca como provisorios se reflejan solos en la nota
  al pie de la sección.

## Fotos

Todas las imágenes de las tarjetas son fotografías de Wikimedia Commons con
licencia libre, recortadas a 900 × 411. La autoría y la licencia de cada una
están en `fotos.py`, en el `title` de la imagen y en el pie de cada grilla.
