# PRD · Norte de Jujuy — Guía de viaje de la Quebrada y la Puna

| Campo | Valor |
| --- | --- |
| Documento | PRD (Product Requirements Document) |
| Producto | Norte de Jujuy · guía de viaje |
| Versión | 1.0 |
| Fecha | 19 de noviembre de 2026 |
| Audiencia | Desarrollo (backend/frontend), operaciones, contenido |
| Estado del producto | En producción: <https://norte-de-jujuy.onrender.com> |
| Repositorio | `IncluTechIA/norte-de-jujuy` (rama `main`) |
| Stack | Python 3.12 · Flask 3 · Jinja2 · Gunicorn · HTML/CSS/JS sin build |

---

## 1. Resumen

Sitio público de una sola página que funciona como guía de viaje del norte de la
provincia de Jujuy (Quebrada de Humahuaca y Puna): qué pueblo visitar, a qué
altura está, cuánto se tarda en llegar, qué fiesta o peña hay esta semana y qué
datos oficiales de turismo respaldan cada destino.

Todo el contenido se arma **en el servidor** con Flask + Jinja a partir de dos
archivos JSON versionados. No hay base de datos, ni panel de administración, ni
registro de usuarios. El único estado persistente del visitante son tres
preferencias guardadas en el navegador (idioma y checklist) y una cookie de
idioma que el servidor usa para el atributo `lang` del documento.

### 1.1 Objetivo del producto

Que una persona que planea viajar al norte jujeño resuelva en una sola página,
sin registrarse y sin depender de varias pestañas:

1. entender la geografía y las distancias reales entre pueblos;
2. saber qué está pasando esta semana (agenda cultural, feriados, fines largos);
3. armar un itinerario de 1 a 5 días con alturas y tiempos estimados;
4. conocer los riesgos concretos (altura, combustible, ripio, señal, efectivo);
5. ver cuánto se mueve el turismo en cada región con datos oficiales.

### 1.2 Métricas de éxito (cualitativas, sin analítica instalada)

- Un visitante nuevo encuentra en menos de 30 s la distancia y la altura de su
  destino.
- El sitio responde 200 en `/` y `/salud` y se sirve completo en menos de 2 s
  con el servicio despierto.
- El contenido se puede actualizar sin tocar código (JSON + scripts).
- La página es legible en un teléfono de 360 px y en escritorio de 1280 px.

---

## 2. Usuarios y casos de uso

| Actor | Necesidad | Recorrido principal |
| --- | --- | --- |
| Viajero que planifica desde otra provincia | Distancias, alturas, tiempos, dónde dormir | Hero → mapa RN9 → Destinos → Kit |
| Viajero ya en la Quebrada | Qué hay hoy/este fin de semana | Agenda (filtros) → Peñas → Feriados |
| Viajero internacional | Leer en su idioma | Selector ES/EN/PT/FR |
| Docente / estudiante / periodista | Cifras oficiales de turismo | Sección «Turismo en números» |
| Mantenedor del sitio | Actualizar datos sin romper nada | `datos.json`, `estadisticas.json`, scripts, workflow |
| Hosting (Render) | Saber si el proceso está vivo | `GET /salud` |

---

## 3. Alcance

### 3.1 Dentro del alcance (v1.0, implementado)

- Una única ruta de contenido (`/`) con siete secciones ancladas.
- Agenda cultural calculada por fecha (incluye fiestas móviles de Pascua).
- Feriados nacionales del año y detección de fines de semana largos.
- Calculador de distancias/tiempos por camino mínimo (Dijkstra) sobre los tramos.
- Cuatro itinerarios predefinidos y cinco experiencias temáticas.
- Sección de estadísticas EOH (DIPEC/INDEC) con actualización automatizada.
- Selector de idioma ES/EN/PT/FR con traducción en el navegador y persistencia.
- Checklist del viajero con memoria local.
- Despliegue en Render (blueprint), Docker y Procfile genérico.

### 3.2 Fuera del alcance (explícito)

- Cuentas de usuario, login, favoritos, comentarios.
- Reservas, pagos o integración con proveedores turísticos.
- Base de datos o CMS; el contenido se edita en el repo.
- Búsqueda full-text, mapas interactivos embebidos, geolocalización.
- Analítica, cookies de terceros, publicidad.
- Traducción automática en servidor: los idiomas se resuelven en el cliente.
- Aplicación móvil nativa.

---

## 4. Requisitos funcionales

Convención: **RF-xx** requisito, **CA** criterio de aceptación verificable.

### 4.1 Cabecera y navegación

- **RF-01** La cabecera muestra logo (SVG de las cuatro regiones), nombre del
  sitio, selector de idioma y una navegación con seis anclas: `#regiones`,
  `#numeros`, `#agenda`, `#plan`, `#destinos`, `#kit`.
- **RF-02** La cabecera es *sticky* y el `scroll-padding-top` compensa su altura
  (86 px; 120 px en móvil) para que los anclajes no queden tapados.
- **RF-03** Primer elemento del `body` es un enlace «Saltar a la agenda
  cultural» visible solo con foco de teclado.
- **CA** Con teclado (Tab) el primer foco es el skip-link; cada ancla lleva a la
  sección correspondiente sin ocultar el título.

### 4.2 Selector de idioma

- **RF-10** Botón rojo en la cabecera con el código del idioma activo
  (`ES`/`EN`/`PT`/`FR`), que abre un menú con los cuatro idiomas.
- **RF-11** Al elegir un idioma se traduce el documento en el navegador con el
  diccionario `static/i18n/<código>.json`; el español es el original y vive en
  el HTML.
- **RF-12** Se actualizan `document.documentElement.lang`
  (`es-AR`/`en`/`pt-BR`/`fr`) y `data-idioma`.
- **RF-13** Se muestra una nota de traducción automática (`#nota-idioma`) en
  todos los idiomas salvo español.
- **RF-14** La elección persiste en la cookie `idioma` (la misma que lee Flask)
  y en `localStorage["jujuy-idioma"]`, y se restaura al recargar.
- **RF-15** El servidor lee `request.cookies["idioma"]` y renderiza `<html lang>`
  y `data-idioma` desde la primera respuesta; un valor desconocido cae en `es`.
- **RF-16** El menú se cierra con clic fuera, con `Escape` y al elegir idioma;
  el botón expone `aria-haspopup`, `aria-expanded` y `aria-pressed` por opción.
- **CA** Elegir FR y recargar dos veces mantiene francés, título traducido y
  nota. Elegir ES desactiva la nota y vuelve al HTML original.
- **CA** A ≤760 px el desplegable queda alineado al borde derecho del botón sin
  generar scroll horizontal (ancho de página = ancho de cliente).

### 4.3 Hero y mapa mental de la RN9

- **RF-20** Hero con titular, bajada, dos CTA (`#agenda`, `#plan`) y cuatro
  indicadores: altura máxima, distancia Jujuy→Humahuaca, pueblos de la Quebrada
  y estaciones de servicio.
- **RF-21** Franja horizontal desplazable con los 12 hitos de la RN9 de sur a
  norte (km desde San Salvador y altura), más el detalle de desvíos
  (Salinas Grandes, Hornocal, Yavi).
- **CA** Los valores de la franja salen de `RUTA` + `LUGARES`; no están escritos
  dos veces en la plantilla.

### 4.4 Las cuatro regiones (`#regiones`)

- **RF-30** Cuatro tarjetas (Puna, Quebrada, Valles, Yungas) con mapa SVG,
  descripción, cuatro datos destacados, localidades, transporte, casillas de
  informes turísticos, cómo llegar y mejor época.
- **RF-31** Cada tarjeta usa el color de la región como variable CSS
  (`--region`).
- **CA** El listado de regiones de la plantilla y la leyenda se generan del mismo
  arreglo `REGIONES` (4 elementos).

### 4.5 Turismo en números (`#numeros`)

- **RF-40** KPIs provinciales: pernoctaciones, viajeros, estadía promedio y
  plazas disponibles (promedio diario) con período explícito.
- **RF-41** Cuatro visualizaciones: pernoctaciones por región (barras), noches
  por mes, residentes/no residentes y ocupación de plazas.
- **RF-42** Tabla de indicadores hoteleros vs. para-hoteleros por región.
- **RF-43** Nota al pie con la fuente, el período y la aclaración de datos
  provisorios cuando corresponde.
- **RF-44** Los datos provienen **solo** de `estadisticas.json`; el servidor no
  scrapea en tiempo de request.
- **CA** `estadisticas.json` con 4 regiones y 5 meses se renderiza sin errores y
  las barras usan `--p`/`--h` calculados (no estilos hardcodeados).

### 4.6 Agenda cultural (`#agenda`)

- **RF-50** Listado de eventos ordenado por fecha de inicio, con cuenta
  regresiva textual («Hoy», «Mañana», «En N días», «Ya pasó»).
- **RF-51** Filtros por pueblo (`?pueblo=`), mes o ventana (`?mes=2`,
  `?mes=proximos7`, `?mes=proximos30`) y destacados (`?destacados=1`), aplicados
  en el servidor y enviados por GET con ancla `#agenda`.
- **RF-52** Los eventos sin fecha firme se marcan como «a confirmar».
- **RF-53** Fichas destacadas, bloque «Antes de salir» (riesgos), feriados del
  año con fines de semana largos y peñas por pueblo.
- **RF-54** Fechas móviles: Carnaval de la Quebrada (Pascua −50 a −42), Carnaval
  de los Valles (−49 a −47) y Semana Santa (−3 a 0) se recalculan cada año con
  el algoritmo gregoriano.
- **CA** `GET /?pueblo=todos&mes=proximos7` devuelve solo eventos con
  `dias <= 7`. Un evento con `hasta` menor que hoy ya no aparece como próximo.

### 4.7 Tu plan de viaje (`#plan`)

- **RF-60** Cuatro itinerarios (`corta`, `clasico`, `extendido`, `yungas`)
  seleccionables con `?itin=<id>`; el servidor resuelve el activo y cae en el
  primero si el id no existe.
- **RF-61** Calculador de distancias con selects de origen y destino
  (`?origen=`, `?destino=`) que muestra km, tiempo, altura del destino, desnivel
  y ruta intermedia.
- **RF-62** El cálculo usa camino mínimo por kilómetros sobre los 18 tramos
  (Dijkstra bidireccional), y los minutos se suman recorriendo ese camino.
- **RF-63** Se agregan avisos contextuales de seguridad: ripio en Hornocal,
  altura en Salinas/Lipán, cornisa en Calilegua, salto de altura, Puna, efectivo
  en La Quiaca/Yavi, combustible antes de salir, distancias sin señal.
- **RF-64** Cinco experiencias temáticas con foto, texto e ítems.
- **CA** `?origen=jujuy&destino=humahuaca` devuelve 126 km; origen = destino
  devuelve un mensaje de error legible, no una excepción.
- **CA** Un par sin camino devuelve el mensaje de «no hay tramo directo», no 500.

### 4.8 Destinos (`#destinos`)

- **RF-70** Nueve tarjetas de destino ordenadas por `orden`, con región, altura,
  distancia, historia, imperdibles y un tip.
- **RF-71** Cada tarjeta tiene foto con autoría y licencia (Wikimedia Commons)
  en `title`, y la grilla muestra el crédito al pie.
- **CA** Si `FOTOS` no tiene entrada para un destino, la tarjeta se muestra sin
  imagen (no rompe el layout).

### 4.9 Kit del viajero (`#kit`)

- **RF-80** Cuatro bloques prácticos (salud y altura, conectividad y dinero,
  clima y ropa, cómo moverse) y un checklist de 11 ítems.
- **RF-81** El checklist se guarda en `localStorage["jujuy-kit"]` como array de
  índices y se restaura al volver.
- **CA** Con `localStorage` bloqueado (modo privado) el checklist funciona en
  memoria y no lanza errores en consola.

### 4.10 Salud y metadatos

- **RF-90** `GET /salud` responde `{"estado":"ok","destinos":9,"eventos":17}`.
- **RF-91** El documento declara `title`, `meta description`, `theme-color`,
  favicon SVG, `viewport` y fuentes (Fraunces + Outfit) con `preconnect`.

---

## 5. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| NFR-01 | **Sin build step**: el repo se sirve tal cual. No hay Node, bundler ni transpilación. |
| NFR-02 | **Sin base de datos**: todo el contenido son archivos JSON versionados que se leen una vez al arrancar. |
| NFR-03 | **Render en servidor** (Jinja) para que el contenido exista sin JavaScript; el JS solo mejora. |
| NFR-04 | **Responsive** con breakpoints 1000, 900, 760, 560, 520 y 420 px; mobile-first en la práctica. |
| NFR-05 | **Accesibilidad**: HTML semántico, `aria-label` en regiones/nav/controles, skip-link, `visually-hidden` en captions, foco visible, `prefers-reduced-motion`. |
| NFR-06 | **Rendimiento**: HTML ~42 KB, CSS ~38 KB, sin librerías JS; imágenes `loading="lazy"` y `decoding="async"`; el video de YouTube se carga recién al hacer clic. |
| NFR-07 | **Privacidad**: no hay analítica ni cookies de terceros; solo `idioma` (propia) y `localStorage` de idioma/checklist. |
| NFR-08 | **Robustez de datos**: valores faltantes en `estadisticas.json` se representan como `null` y se excluyen del cálculo, nunca como 0. |
| NFR-09 | **Operabilidad**: health check `/salud` para el hosting; logs a stdout. |
| NFR-10 | **Trazabilidad de contenido**: fuentes y licencias de fotos en `fotos.py`; fuente de estadísticas en el propio JSON (`fuente`, `url`, `periodo`, `nota`). |
| NFR-11 | **Paridad de diccionarios**: los tres JSON de i18n tienen las mismas 938 claves. |
| NFR-12 | **Sin tests automatizados en el repo**: la verificación es manual + health check + workflow de datos. (Ver §11.) |

---

## 6. Contratos de URL

| Método | Ruta | Parámetros | Respuesta |
| --- | --- | --- | --- |
| GET | `/` | `pueblo`, `mes`, `destacados`, `itin`, `origen`, `destino` | HTML completo |
| GET | `/salud` | — | JSON `{estado, destinos, eventos}` |
| GET | `/static/*` | — | Assets (CSS, JS, i18n, imágenes SVG/JPG) |

Reglas de validación (todas en `app.py:index`):

- `pueblo` fuera de la lista de tokens → sin resultados (no error).
- `mes` acepta `todos`, `proximos7`, `proximos30` o `1..12`.
- `itin` desconocido → primer itinerario.
- `origen`/`destino` desconocidos → `jujuy` / `humahuaca`.
- `destacados=1` activa el checkbox.

Ejemplos:

```
/?pueblo=Tilcara&mes=2&destacados=1#agenda
/?itin=yungas#plan
/?origen=jujuy&destino=hornocal#plan
```

---

## 7. Modelo de datos

### 7.1 `datos.json` (contenido editorial)

| Clave | Tipo | Longitud | Forma |
| --- | --- | --- | --- |
| `LUGARES` | objeto | 17 | `clave → {nombre, corto, alt}` (alt en m s. n. m.) |
| `TRAMOS` | lista | 18 | `[origen, destino, km, minutos]` (bidireccional) |
| `EVENTOS` | lista | 17 | `{nombre, pueblo, tipo, mes, dia, hasta?, lugar, desc, destacado?, a_confirmar?}` |
| `PENAS` | lista | 8 | `{pueblo, zona, titulo, texto, meta[]}` |
| `ITINERARIOS` | lista | 4 | `{id, titulo, ...}` con ids `corta`, `clasico`, `extendido`, `yungas` |
| `EXPERIENCIAS` | lista | 5 | `{titulo, donde, paleta, texto, items[]}` |
| `DESTINOS` | lista | 9 | `{nombre, region, orden, alt, km, paleta, historia, imperdibles, tip}` |
| `REGIONES` | lista | 4 | `{id, nombre, alt, color, mapa, texto, datos[4], localidades[], transporte, informes, llegar, cuando}` |
| `CHECKLIST` | lista | 11 | `string` |
| `FERIADOS` | lista | 17 | `{fecha: "AAAA-MM-DD", nombre, tipo}` (`inamovible`, `no laborable`, `trasladable`, `puente`) |

Claves internas de `app.py` (no están en el JSON): `MESES`, `MESES_CORTOS`,
`DIAS_CORTOS`, `RUTA`, `NORTE`, `PASCUA`, `IDIOMAS_HTML`.

### 7.2 `estadisticas.json` (generado, versionado)

```jsonc
{
  "fuente": "DIPEC Jujuy e INDEC · Encuesta de Ocupación Hotelera (EOH)",
  "url": "https://dipec.jujuy.gob.ar/...",
  "periodo": "enero a mayo de 2026",
  "anio": 2026,
  "meses": ["Enero", "Febrero", "..."],
  "nota": "… datos provisorios …",
  "total": { "pernoctaciones", "viajeros", "estadia", "plazas",
             "establecimientos", "ocupacion_plazas", "no_residentes",
             "no_residentes_pct", "viajeros_no_residentes",
             "hoteleros": {...}, "parahoteleros": {...} },
  "serie": [123, 456, ...],            // pernoctaciones por mes
  "regiones": [{ "nombre", "id", "pernoctaciones", "viajeros", "estadia",
                 "ocupacion", "ocupacion_plazas", "plazas",
                 "establecimientos", "residentes_pct", "no_residentes",
                 "no_residentes_pct", "viajeros_no_residentes",
                 "hoteleros": {...}, "parahoteleros": {...},
                 "por_mes": [...], "parte", "color" }]
}
```

Invariantes: `regiones` ordenadas por pernoctaciones descendente; `parte` suma
100 % (±0,1 por redondeo); `serie[i]` = suma de `por_mes[i]` de las regiones.

### 7.3 Diccionarios `static/i18n/<código>.json`

```jsonc
{
  "nombre": "English",
  "corto": "EN",
  "html_lang": "en",
  "nota": "Automatic translation from Spanish…",
  "meses":   { "enero": "January", ... },      // 12
  "fechas":  { "dia": "{mes} {d}, {a}", "rango": "...", ... },
  "periodo": { "rango": "{m1} to {m2} {a}", "mes": "{m} {a}" },
  "patrones":{ "en_dias": "In {n} days", "km": "{n} km", ... },
  "textos":  { "frase en español": "traducción", ... }   // 938 entradas
}
```

La clave de `textos` es la frase **en español tal como aparece en el HTML**,
normalizada (espacios colapsados, `trim`). No se traducen nombres propios.

---

## 8. Arquitectura y estructura del código

### 8.1 Flujo de un request

```
GET /?pueblo=Tilcara&mes=2
  → gunicorn (gthread, 2 workers × 4 hilos)
  → Flask (ProxyFix: x_for, x_proto, x_host, x_port)
  → index()
      1. eventos_con_fecha()      # fechas + Pascua + orden
      2. filtrar_eventos()        # pueblo / mes / destacados
      3. calcular(origen,destino) # Dijkstra + notas de seguridad
      4. serie_mensual(), feriados_del_anio(), fines_de_semana_largos()
      5. idioma = cookie("idioma") o "es"
  → Jinja renderiza templates/index.html con ~25 variables
  → HTML 200  (+ CSS, dos JS defer, i18n on demand)
```

`datos.json`, `estadisticas.json` y `fotos.py` se leen **una vez al importar**
el módulo; no hay I/O de datos por request.

### 8.2 Árbol del repositorio

```
app.py                    # toda la lógica: rutas, fechas, filtros, Dijkstra, armado
wsgi.py                   # entrada de producción (wsgi:app)
gunicorn.conf.py          # bind, workers/hilos, logs, preload
Procfile / Dockerfile / render.yaml
requirements.txt          # Flask, gunicorn (runtime)
requirements-scripts.txt  # xlrd, openpyxl (solo mantenimiento)
datos.json                # contenido editorial
estadisticas.json         # indicadores EOH (generado)
fotos.py                  # FOTOS, VIDEOS, VIDEOS_DESTINOS, VIDEOS_EXPERIENCIAS, COLOR_REGION
templates/index.html      # único template Jinja (729 líneas): todo el marcado
static/css/styles.css     # diseño completo (632 líneas, 10 bloques @media)
static/js/site.js         # filtros, video diferido, checklist
static/js/idioma.js       # motor de traducción + selector
static/i18n/{en,pt,fr}.json
static/img/…              # logo, mapas de región, fotos 900×411, hero
scripts/actualizar_estadisticas.py
scripts/controlar_antiguedad.py
.github/workflows/estadisticas.yml
```

### 8.3 Mapa de funciones de `app.py`

| Grupo | Funciones | Responsabilidad |
| --- | --- | --- |
| Formato | `miles`, `coma`, `formato_fecha`, `formatear_tiempo`, `cuando_texto`, `rango_texto` | Localización numérica y de fechas en español (filtros Jinja `miles` y `coma`) |
| Fechas | `domingo_de_pascua`, `ocurrencia`, `eventos_con_fecha` | Calcular la próxima ocurrencia de cada evento, incluidas las móviles |
| Feriados | `feriados_del_anio`, `fines_de_semana_largos` | Fechas listas para mostrar y bloques de ≥3 días |
| Agenda | `tokens_pueblo`, `opciones_pueblo`, `filtrar_eventos` | Normalizar pueblos («Toda la Quebrada») y aplicar filtros |
| Distancias | `construir_grafo`, `camino_minimo`, `minutos_de_camino`, `calcular` | Dijkstra por km + notas de seguridad por destino/tramo |
| Estadísticas | `serie_mensual` | Altura de barra normalizada (0-100) por mes |
| Rutas | `index`, `salud` | Armar el contexto de la plantilla / health check |

### 8.4 Frontend

- **`site.js`** (sin dependencias): auto-submit del formulario de agenda al
  cambiar filtros, reemplazo de la miniatura por un `iframe` de
  `youtube-nocookie` al hacer clic, persistencia del checklist.
- **`idioma.js`** (sin dependencias): IIFE que expone el motor de traducción
  descripto en §9.
- **`styles.css`**: custom properties en `:root` (paleta y tipografías), clases
  utilitarias mínimas, grillas con `clamp()`, sin frameworks.
- Orden de scripts: `idioma.js` y luego `site.js`, ambos `defer`.

### 8.5 Convenciones del proyecto

- **Idioma del código**: identificadores, docstrings y comentarios en español;
  los commits y este PRD siguen esa línea.
- **Fin de línea**: `templates/index.html` y `static/css/styles.css` usan CRLF;
  `.py`, `.js`, `.json` y `.md` usan LF. Respetarlo evita diffs gigantes.
- **Sin dependencias JS ni CSS externas** salvo Google Fonts.
- **Datos primero**: si un texto o cifra puede vivir en `datos.json` o
  `estadisticas.json`, no se escribe en la plantilla.
- **Nombres de archivos y rutas en español** (`calcular`, `eventos_con_fecha`,
  `estadisticas.json`).
- **Sin tests**: cualquier cambio se valida con `python -c "import app"`,
  arranque local, `/salud` y revisión visual.

---

## 9. Motor de traducción (i18n)

1. Flask renderiza siempre el HTML en español y setea `<html lang>` y
   `data-idioma` según la cookie `idioma`.
2. Al arrancar, `idioma.js` resuelve el idioma en este orden:
   `localStorage["jujuy-idioma"]` → cookie `idioma` → `data-idioma` → `es`
   (validando siempre contra la lista de idiomas soportados).
3. Al cambiar de idioma: `fetch` del diccionario (cacheado en memoria) y luego
   tres pasadas:
   - `traducirArbol(body)`: recorre nodos de texto y reemplaza por la clave
     normalizada. Los originales quedan en un `WeakMap` para poder restaurar.
   - `traducirAtributos()`: `title`, `alt`, `aria-label`, `placeholder`, etc.
   - `traducirCabecera()`: `<title>` y `meta description`.
4. Los textos con datos variables (fechas, «En 5 días», «4.350 m», «126 km»,
   períodos EOH) no están en `textos`: los resuelve `reglas()` con regex y las
   plantillas de `fechas`, `periodo` y `patrones`. Así siguen funcionando cuando
   cambian los datos.
5. Los números en inglés se reformatean (4.350 → 4,350; 2,5 → 2.5).
6. Volver a español restaura los textos originales desde el `WeakMap` y oculta
   la nota de traducción.
7. Elementos con `data-no-i18n` (el propio selector) se excluyen.

**Agregar una frase:** sumarla al HTML o a `datos.json` y luego a `textos` de
los tres diccionarios. Mientras falte, se muestra en español sin romper nada.

**Limitación conocida:** la traducción es por coincidencia exacta de texto; si se
edita una frase en la plantilla, su clave vieja deja de aplicar y hay que
actualizarla en los tres JSON.

---

## 10. Operación

### 10.1 Actualización de estadísticas

```
cron día 10 de cada mes (12:00 UTC)  ─┐
Actions → Run workflow (manual)      ─┴→ actualizar_estadisticas.py
                                          │ descarga planilla EOH (DIPEC)
                                          │ parsea 4 regiones / 5-12 meses
                                          ▼
                                    estadisticas.json
                                          │ si cambió → commit a main
                                          ▼
                                    Render autoDeploy → producción
```

- `actualizar_estadisticas.py`: descubre la planilla del último año en la página
  de DIPEC, la descarga por el gestor de WordPress, lee `.xls` (xlrd) o `.xlsx`
  (openpyxl), extrae oferta y demanda y reescribe el JSON. Opciones:
  `--anio`, `--archivo`, `--seco`, `--salida`.
- `controlar_antiguedad.py`: falla si el último mes publicado tiene más de
  `--max-meses` (2 por defecto) de atraso.
- Errores → issue con etiqueta `estadisticas` (o comentario si ya existe); al
  volver a estar verde, se comenta y se cierra.
- El script **no** corre en el servidor: el resultado se versiona.

### 10.2 Despliegue

| Vía | Configuración |
| --- | --- |
| Render (actual) | `render.yaml`: Python 3.12.7, `pip install -r requirements.txt`, `gunicorn -c gunicorn.conf.py wsgi:app`, health `/salud`, `SECRET_KEY` generada, plan free (duerme por inactividad) |
| Docker | `python:3.12-slim`, usuario no root, `HEALTHCHECK` contra `/salud` |
| Procfile | `web: gunicorn -c gunicorn.conf.py wsgi:app` |

Variables: `SECRET_KEY` (obligatoria en producción), `PORT`, `WEB_CONCURRENCY`,
`GUNICORN_THREADS`, `LOG_LEVEL`, `FLASK_DEBUG` (solo local). `.env` está
ignorado; `.env.example` documenta cada una.

### 10.3 Publicar un cambio de contenido

```
editar datos.json / estadisticas.json / i18n
  → python3 -c "import app"        # valida JSON y arranque
  → git commit && git push origin main
  → Render deploy (~40 s)
  → verificar /salud y la sección tocada
```

---

## 11. Criterios de aceptación globales (QA manual)

Antes de dar por bueno un cambio:

1. `python3 -c "import app"` no lanza excepciones.
2. `GET /` responde 200 y `GET /salud` devuelve `estado: ok` con los conteos
   esperados.
3. Las siete secciones se ven completas a 360, 736 y 1280 px, sin scroll
   horizontal.
4. Los filtros de agenda y el calculador devuelven resultados coherentes con
   los parámetros de la URL.
5. El selector de idioma traduce las cuatro opciones, muestra la nota y conserva
   la elección tras recargar.
6. No hay errores en la consola del navegador.
7. `estadisticas.json` y los diccionarios siguen siendo JSON válido.

---

## 12. Riesgos y deuda conocida

| Riesgo | Impacto | Mitigación actual |
| --- | --- | --- |
| DIPEC cambia el formato de la planilla | La sección de números queda vieja | Script con mensajes de error claros, control de antigüedad, issue automático |
| Frases editadas en la plantilla quedan sin traducir | Texto en español en otro idioma | Documentado en §9; los diccionarios usan la frase como clave |
| Plan free de Render duerme el servicio | Primera visita lenta (~10 s) | Aceptado; health check y `autoDeploy` |
| Contenido editorial solo en JSON | Edición requiere repo y deploy | Fuera de alcance: no hay CMS |
| Sin tests automatizados | Regresiones detectadas a mano | Checklist de §11; el workflow cubre los datos |

---

## 13. Próximos pasos sugeridos (fuera de v1.0)

- Tests de humo para `app.py` (fechas, filtros, Dijkstra) con `pytest`.
- Verificación automática de paridad de claves entre los tres diccionarios.
- `sitemap.xml` y datos estructurados (`TouristDestination`) para SEO.
- Modo «hoy» con datos de clima y estado de rutas.
- Imágenes en `webp` con `srcset` para móvil.

---

## 14. Glosario

- **EOH**: Encuesta de Ocupación Hotelera (DIPEC Jujuy / INDEC).
- **Quebrada / Puna / Valles / Yungas**: las cuatro regiones de Jujuy que
  estructuran el sitio.
- **RN9**: Ruta Nacional 9, eje sur-norte de la guía.
- **Pernoctaciones**: noches de alojamiento; métrica principal de la EOH.
- **Plazas**: camas/plazas disponibles u ocupadas según el contexto.
- **Pascua**: domingo de Pascua, base para calcular carnaval y Semana Santa.
