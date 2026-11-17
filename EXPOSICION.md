# Norte de Jujuy — guía de exposición del código

Documento para explicar el proyecto en una exposición: qué es, cómo está organizado,
qué hace cada archivo y qué decir en cada momento.

- Sitio: https://norte-de-jujuy.onrender.com
- Código: https://github.com/IncluTechIA/norte-de-jujuy
- Stack: Flask (Python 3.12) + Jinja + CSS y JavaScript propios, sin frameworks de front.
- Datos: un JSON versionado en el repo. No hay base de datos.

---

## 1. La idea en una frase

Es una guía de viaje del norte de Jujuy armada como aplicación web: el contenido
—pueblos, regiones, agenda, itinerarios— vive en un archivo de datos, la lógica de
fechas y distancias vive en Python, y el HTML se genera en el servidor. El navegador
casi no programa: recibe la página ya armada.

Eso permite tres cosas que conviene destacar en la exposición:

1. El contenido se corrige editando un JSON, sin tocar la lógica.
2. Funciona sin JavaScript para lo importante (agenda, distancias, itinerarios).
3. Se despliega con dos archivos de configuración y no necesita base de datos.

---

## 2. Mapa del proyecto

| Archivo | Líneas | Qué hace |
|---|---:|---|
| `app.py` | 421 | Toda la lógica: fechas, agenda, filtros, feriados, distancias (Dijkstra) y rutas. |
| `datos.json` | 1431 | El contenido: 17 lugares, 18 tramos, 17 eventos, 17 feriados, 4 itinerarios, 9 destinos, 5 experiencias, 4 regiones, 8 peñas, 11 ítems de checklist. |
| `fotos.py` | 190 | Qué foto y qué video lleva cada tarjeta, más el color de cada región. |
| `templates/index.html` | 540 | La única plantilla: estructura de la página y bucles de Jinja. |
| `static/css/styles.css` | 546 | Estilos: paleta, grillas, secciones, responsive, videos y feriados. |
| `static/js/site.js` | 53 | Tres interacciones: filtros que se envían solos, video que se carga al click y checklist con memoria. |
| `static/img/` | — | Fotos (900×411), mapas de las regiones y favicon. |
| `wsgi.py` | 10 | Punto de entrada que gunicorn usa en producción. |
| `gunicorn.conf.py` | 28 | Puerto, workers, hilos, timeouts y logs del servidor. |
| `Procfile` | 1 | Le dice al hosting cómo arrancar la app. |
| `requirements.txt` | 2 | Flask y gunicorn, con versión acotada. |
| `render.yaml`, `Dockerfile` | — | Despliegue alternativo (blueprint de Render y contenedor). |

Frase para la exposición: **“cuatro archivos hacen el trabajo: datos, lógica, plantilla y
estilos; el resto es configuración de despliegue”**.

---

## 3. Cómo viaja un pedido

```
Navegador  →  GET /  →  Flask (index)  →  datos.json + funciones de app.py
                                              ↓
                                        index.html (Jinja)
                                              ↓
                                    HTML final + CSS + JS
```

1. El navegador pide `/` (o `/?mes=2&pueblo=Tilcara`).
2. Flask lee los parámetros, calcula fechas, filtra eventos y resuelve la distancia.
3. Jinja recorre las listas y arma el HTML.
4. El navegador recibe una página completa. JavaScript solo agrega comodidades.

---

## 4. `app.py`, bloque por bloque

### 4.1 Configuración y datos

```python
BASE = Path(__file__).parent
DATOS = json.loads((BASE / "datos.json").read_text(encoding="utf-8"))

LUGARES = DATOS["LUGARES"]
TRAMOS = DATOS["TRAMOS"]
EVENTOS = DATOS["EVENTOS"]
```

El JSON se lee una vez, al importar el módulo, y queda en memoria. Para una guía que
cambia poco es más simple y más rápido que consultar una base en cada visita.

```python
app.secret_key = os.environ.get("SECRET_KEY", "solo-para-desarrollo-local")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
```

- La clave llega por variable de entorno; el valor de reserva es solo para local.
- `ProxyFix` hace que, detrás del proxy del hosting, la app vea el host y el HTTPS reales.

### 4.2 Fechas de la agenda

Los eventos se guardan como día y mes (`{"mes": 2, "dia": 2}`), sin año, porque la
mayoría se repite todos los años. Al mostrarlos, la app calcula la **próxima ocurrencia**
a partir de hoy:

```python
def ocurrencia(ev, referencia=None):
    ref = referencia or date.today()
    inicio = date(ref.year, ev["mes"], ev["dia"])
    fin = date(ref.year, ev["mes"], ev["hasta"]) if ev.get("hasta") else inicio
    if fin < ref:                       # ya pasó: se pasa al año que viene
        inicio = date(ref.year + 1, ev["mes"], ev["dia"])
        fin = date(ref.year + 1, ev["mes"], ev["hasta"]) if ev.get("hasta") else inicio
    return inicio, fin
```

Y las fiestas que dependen de la Pascua no tienen fecha fija: se calculan.

```python
PASCUA = {
    "Carnaval de la Quebrada": (-50, -42),   # del sábado al domingo de entierro
    "Carnaval de los Valles":  (-49, -47),
    "Semana Santa en la Quebrada": (-3, 0),  # jueves a domingo
}

def domingo_de_pascua(anio):
    """Algoritmo gregoriano anónimo: devuelve el Domingo de Pascua del año."""
```

Con eso, en 2027 el carnaval cae del 6 al 14 de febrero y en 2028, del 26 al 29.
Si estuviera escrito a mano, en 2028 la agenda mostraría fechas equivocadas.

`eventos_con_fecha()` agrega a cada evento lo que la plantilla necesita: fecha de
inicio y fin, cuántos días faltan (`dias`), el texto “En 86 días” (`cuando_texto`),
el mes corto para el badge y si dura varios días (`multi`).

### 4.3 Feriados y fines de semana largos

```python
def fines_de_semana_largos():
    festivos = {fecha: nombre for ... if tipo in ("inamovible", "no laborable")}
    # recorre el año y arma bloques de días feriados + sábados y domingos
```

No hay una lista de findes largos escrita a mano: se calculan uniendo feriados con
fines de semana y quedándose con los bloques de tres días o más. Los feriados
“trasladables” no entran en el cálculo porque su fecha depende de un decreto.

### 4.4 Filtros de la agenda

```python
def filtrar_eventos(eventos, pueblo, mes, solo_destacados):
    for ev in eventos:
        if pueblo not in ("", "todos") and pueblo not in ev["pueblos"]:
            continue
        if solo_destacados and not ev.get("destacado"):
            continue
        if mes == "proximos7" and ev["dias"] > 7:
            continue
```

El filtrado ocurre **en el servidor**: la URL queda compartible (`/?mes=2`) y la página
funciona igual sin JavaScript. El `<select>` solo envía el formulario cuando cambia.

### 4.5 Distancias: Dijkstra

Los tramos son pares `(origen, destino, km, minutos)`. Con ellos se arma un grafo no
dirigido —cada tramo se agrega en los dos sentidos— y se busca el camino más corto:

```python
def camino_minimo(origen, destino):
    dist = {k: math.inf for k in LUGARES}
    dist[origen] = 0
    while len(visto) < len(LUGARES):
        candidatos = [k for k in dist if k not in visto and dist[k] < math.inf]
        if not candidatos:
            break
        actual = min(candidatos, key=lambda k: dist[k])   # el más cercano sin visitar
        if actual == destino:
            break
        visto.add(actual)
        for tramo in GRAFO[actual]:
            alt = dist[actual] + tramo["km"]
            if alt < dist[tramo["a"]]:                     # relajación de la arista
                dist[tramo["a"]] = alt
                previo[tramo["a"]] = actual
```

Con 17 lugares, la versión simple (elegir el mínimo en cada vuelta) es más clara que
usar una cola de prioridad y sobra en velocidad. Devuelve el camino y los kilómetros;
después se suman los minutos de cada tramo.

`calcular()` convierte eso en lo que se ve: kilómetros, tiempo, desnivel y **avisos
automáticos** según el trayecto:

```python
if destino == "hornocal":
    notas.append("<strong>Camino de ripio de montaña:</strong> 25 km sin baranda...")
if destino in ("laquiaca", "yavi"):
    notas.append("<strong>Efectivo obligatorio:</strong> ...")
```

Es el aporte más “de guía” del código: no muestra solo la distancia, avisa lo que
importa (altura, nafta, ripio, efectivo, falta de señal).

### 4.6 Las dos rutas

```python
@app.get("/salud")
def salud():
    return jsonify(estado="ok", destinos=len(DESTINOS), eventos=len(EVENTOS))

@app.get("/")
def index():
    ...
    return render_template("index.html", eventos=..., feriados=..., calculo=...)
```

- `/salud` es el chequeo que usa Render para saber si la instancia está viva.
- `/` arma todo y lo entrega a la plantilla. La app no tiene base de datos ni estado:
  cada visita se resuelve con lo que viene en la URL.

---

## 5. `datos.json`

Todo el contenido, agrupado por tema:

| Clave | Cantidad | Para qué |
|---|---:|---|
| `LUGARES` | 17 | Pueblos y atractivos con altura y nombre corto. |
| `TRAMOS` | 18 | Conexiones con kilómetros y minutos (alimentan a Dijkstra). |
| `EVENTOS` | 17 | Agenda cultural: mes, día, lugar, descripción, destacado. |
| `FERIADOS` | 17 | Feriados 2027 con tipo: inamovible, no laborable o trasladable. |
| `ITINERARIOS` | 4 | Planes de 3, 5, 7 días y la bajada a las Yungas. |
| `DESTINOS` | 9 | Tarjetas pueblo por pueblo con historia, imperdibles y consejo. |
| `EXPERIENCIAS` | 5 | Vino de altura, turismo comunitario, trekking, selva y termas. |
| `REGIONES` | 4 | Puna, Quebrada, Valles y Yungas con transporte e informes. |
| `PENAS` | 8 | Dónde comer y escuchar folklore. |
| `CHECKLIST` | 11 | Kit del viajero. |

Ejemplo real de un destino:

```json
{
  "nombre": "Purmamarca",
  "region": "Quebrada",
  "alt": 2324,
  "km": "65 km de S.S. de Jujuy",
  "historia": "El pueblo más fotografiado del norte jujeño...",
  "imperdibles": ["...", "...", "...", "..."],
  "tip": "<strong>Cuándo:</strong> el cerro se ve mejor con luz baja."
}
```

Punto para la exposición: separar datos de lógica permite corregir un precio, una
fecha o un texto sin programar, y tener todo el contenido en un solo archivo revisable.

---

## 6. `fotos.py`

Dos diccionarios con criterio editorial:

- `FOTOS`: una foto por tarjeta, con clave corta, autoría/licencia y texto alternativo.
- `VIDEOS`, `VIDEOS_DESTINOS`, `VIDEOS_EXPERIENCIAS`: el video de cada tarjeta, con
  ID de YouTube, título real y canal.
- `COLOR_REGION`: el color de cada región, que la plantilla usa como variable CSS.

Las 14 fotos son de Wikimedia Commons con licencia libre, recortadas a 900×411 y
guardadas en el repo: el sitio no depende de servidores externos para las imágenes.

---

## 7. `templates/index.html`

Una sola página con secciones ancladas (`#regiones`, `#agenda`, `#plan`, `#destinos`,
`#kit`). Jinja hace tres cosas: bucles, condicionales y datos calculados.

Bucle típico de una tarjeta (resumido del original):

```jinja
{% for d in destinos %}
{% set f = fotos.get(d.nombre) %}
<article class="dest-card">
  <h3>{{ d.nombre }}</h3>
  <p class="dest-story">{{ d.historia }}</p>
  <ul>{% for x in d.imperdibles %}<li>{{ x }}</li>{% endfor %}</ul>
</article>
{% endfor %}
```

Detalle que conviene mencionar: `{{ }}` escapa el HTML por seguridad, y por eso los
textos con negritas usan `|safe` solo en campos controlados por nosotros (`tip`).

Video con carga diferida (no hay iframe hasta el click):

```jinja
<button class="rv-play" data-video="{{ v.id }}" data-titulo="{{ v.titulo }}">
  <img src="https://i.ytimg.com/vi/{{ v.id }}/mqdefault.jpg" alt="" loading="lazy" />
</button>
```

También hay etiquetas semánticas y accesibilidad: `aria-labelledby` en cada sección,
`aria-pressed` en los filtros, texto solo para lectores de pantalla en las fechas y
enlace para saltear al contenido.

---

## 8. `static/css/styles.css`

Organizado por componentes, con comentarios de sección:

```
header · hero · secciones · agenda tools · planificador · destinos
regiones · kit · footer · responsive · videos · feriados
```

- Paleta y medidas en variables CSS (`--tinta`, `--arena`, `--linea`, `--verde`…), así
  el color de una región se cambia con una línea (`--region`).
- Grillas con `minmax(0,1fr)` para que el contenido largo no rompa las columnas.
- Un bloque `@media` para móvil: de dos columnas a una, mapas y fotos más chicos.
- Los videos y feriados tienen su propio bloque al final, para no mezclarlos con el resto.

---

## 9. `static/js/site.js` (53 líneas)

Tres cosas, ninguna imprescindible para leer la guía:

```js
// 1) Los filtros se envían solos al cambiar
campo.addEventListener("change", () => form.submit());

// 2) El video se carga recién al hacer click
marco.src = "https://www.youtube-nocookie.com/embed/" + btn.dataset.video;

// 3) Checklist con memoria en el navegador
localStorage.setItem("jujuy-kit", JSON.stringify(marcados));
```

Por qué se destaca: 18 videos en una página serían 18 reproductores de YouTube
cargando de golpe. Con este patrón la página baja rápido y el reproductor aparece solo
si el visitante lo pide. Y el checklist se guarda en el navegador, no en un servidor:
no hay cuentas ni datos personales.

---

## 10. Despliegue

```
Procfile            web: gunicorn -c gunicorn.conf.py wsgi:app
requirements.txt    Flask>=3.0,<4  ·  gunicorn>=22,<24
```

`gunicorn.conf.py` toma el puerto del entorno y usa 2 procesos con 4 hilos cada uno:

```python
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
worker_class = "gthread"
accesslog = "-"
```

En Render: build `pip install -r requirements.txt`, health check `/salud`, deploy
automático en cada push a `main`. El plan gratuito duerme la instancia, así que la
primera visita puede tardar unos 20 segundos: es bueno decirlo antes de que pregunten.

---

## 11. Guion sugerido (6–8 minutos)

1. **Qué es (30 s).** “Una guía de viaje del norte de Jujuy que funciona como aplicación
   web: agenda cultural, planificador de distancias y fichas de cada pueblo.”
2. **Arquitectura (1 min).** Mostrar el mapa de archivos y la idea: datos separados de
   lógica, HTML generado en el servidor.
3. **La agenda (1,5 min).** Filtrar por mes en vivo. Explicar que el filtro es del
   servidor, que la URL se comparte y que las fiestas móviles se calculan desde la Pascua.
   Mostrar la etiqueta “Fecha a confirmar”.
4. **El planificador (1,5 min).** Elegir origen y destino, mostrar kilómetros, tiempo y
   los avisos automáticos de altura, ripio o efectivo. Decir que por dentro es Dijkstra.
5. **El contenido (1 min).** Abrir `datos.json` y mostrar que agregar un pueblo o una
   fiesta es editar un bloque de texto.
6. **Detalles de oficio (1 min).** Fotos propias con licencia, videos que se cargan al
   click, accesibilidad, `/salud`, deploy automático.
7. **Cierre (30 s).** “Todo el sitio son 3.200 líneas, sin base de datos, y se actualiza
   con un push.”

---

## 12. Preguntas probables y respuestas cortas

- **¿Por qué Flask y no React?** Porque el contenido es fijo y se genera en el servidor;
  no hace falta hidratar nada. Menos dependencias, más rápido de mantener.
- **¿Dónde está la base de datos?** No hay: el contenido es un JSON versionado. Si
  hiciera falta, el mismo esquema se migra a SQLite sin cambiar la plantilla.
- **¿Cómo se calculan las distancias?** Grafo no dirigido con los 18 tramos y Dijkstra
  sobre kilómetros; los minutos se suman tramo por tramo.
- **¿Y si cambia una fecha de carnaval?** No se toca nada: se calcula desde la Pascua.
- **¿Por qué no cargan 18 videos juntos?** Porque el iframe se inserta al hacer click;
  la miniatura pesa unos 30 KB.
- **¿Qué pasa si el sitio “duerme”?** Es el plan gratuito: la primera visita despierta
  la instancia y tarda unos 20 segundos.
- **¿Cómo se actualiza?** Se edita el JSON o la plantilla, `git push`, y Render
  reconstruye y publica solo.
