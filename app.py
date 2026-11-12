# -*- coding: utf-8 -*-
"""Guía «Norte de Jujuy» servida con Flask.

Los textos y los datos viven en `datos.json` (pueblos, tramos, agenda, peñas,
itinerarios, destinos, regiones y checklist). Acá está toda la lógica: fechas de
la agenda, filtros, cálculo de distancias y armado de las secciones.
"""

from __future__ import annotations

import json
import math
import os
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from fotos import COLOR_REGION, FOTOS, VIDEOS, VIDEOS_DESTINOS, VIDEOS_EXPERIENCIAS

BASE = Path(__file__).parent
DATOS = json.loads((BASE / "datos.json").read_text(encoding="utf-8"))

LUGARES = DATOS["LUGARES"]
TRAMOS = DATOS["TRAMOS"]
EVENTOS = DATOS["EVENTOS"]
PENAS = DATOS["PENAS"]
ITINERARIOS = DATOS["ITINERARIOS"]
EXPERIENCIAS = DATOS["EXPERIENCIAS"]
DESTINOS = DATOS["DESTINOS"]
REGIONES = DATOS["REGIONES"]
CHECKLIST = DATOS["CHECKLIST"]

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_CORTOS = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
                "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

# Pueblos de la RN9 de sur a norte, con su kilómetro desde San Salvador.
RUTA = [
    ("jujuy", 0), ("yala", 13), ("purmamarca", 65), ("maimara", 76),
    ("tilcara", 84), ("huacalera", 100), ("uquia", 111), ("humahuaca", 126),
    ("trecruces", 152), ("abrapampa", 197), ("laquiaca", 290), ("yavi", 303),
]

# Pueblos del norte: sirven para decidir los avisos de combustible.
NORTE = {
    "purmamarca", "maimara", "tilcara", "huacalera", "uquia", "humahuaca",
    "trecruces", "abrapampa", "laquiaca", "yavi", "salinas", "hornocal",
}

app = Flask(__name__)

# En producción la clave llega por variable de entorno; el valor de reserva solo
# sirve para correr en local (la app no usa sesiones ni formularios con estado).
app.secret_key = os.environ.get("SECRET_KEY", "solo-para-desarrollo-local")

# Detrás del proxy del hosting (Render, Fly, Railway) hay un salto de HTTPS:
# esto hace que request.scheme y el host sean los que ve el navegador.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)


def miles(valor: int) -> str:
    """1234 -> '1.234' (separador de miles como en la Argentina)."""
    return f"{valor:,}".replace(",", ".")


def formato_fecha(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def formatear_tiempo(minutos: float) -> str:
    horas, resto = divmod(int(round(minutos)), 60)
    if not horas:
        return f"{resto} min"
    return f"{horas} h {resto} min" if resto else f"{horas} h"


def cuando_texto(dias: int) -> str:
    if dias == 0:
        return "Hoy"
    if dias == 1:
        return "Mañana"
    if dias < 0:
        return "Ya pasó"
    return f"En {dias} días"


def tokens_pueblo(texto: str) -> list[str]:
    if "toda la quebrada" in texto.lower():
        return ["Toda la Quebrada"]
    return [t.strip() for t in texto.split("·") if t.strip()]


# Fiestas que se mueven con la Pascua, en días respecto del Domingo de Pascua:
# (primer día, último día). Así la agenda sirve para cualquier año, no solo
# para el que se cargó a mano: en 2027 el carnaval cae del 6 al 9 de febrero
# y en 2028, del 26 al 29.
PASCUA = {
    "Carnaval de la Quebrada": (-50, -42),
    "Carnaval de los Valles": (-49, -47),
    "Semana Santa en la Quebrada": (-3, 0),
}


def domingo_de_pascua(anio: int) -> date:
    """Domingo de Pascua del año (algoritmo gregoriano anónimo)."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(anio, mes, dia + 1)


def ocurrencia(ev: dict, referencia: date | None = None) -> tuple[date, date]:
    """Próxima vez que cae el evento a partir de la fecha de referencia."""
    ref = referencia or date.today()

    if ev["nombre"] in PASCUA:
        desde, hasta = PASCUA[ev["nombre"]]
        base = domingo_de_pascua(ref.year)
        inicio, fin = base + timedelta(days=desde), base + timedelta(days=hasta)
        if fin < ref:
            base = domingo_de_pascua(ref.year + 1)
            inicio, fin = base + timedelta(days=desde), base + timedelta(days=hasta)
        return inicio, fin

    inicio = date(ref.year, ev["mes"], ev["dia"])
    fin = date(ref.year, ev["mes"], ev["hasta"]) if ev.get("hasta") else inicio
    if fin < ref:
        inicio = date(ref.year + 1, ev["mes"], ev["dia"])
        fin = date(ref.year + 1, ev["mes"], ev["hasta"]) if ev.get("hasta") else inicio
    return inicio, fin


def eventos_con_fecha() -> list[dict]:
    ref = date.today()
    salida = []
    for ev in EVENTOS:
        inicio, fin = ocurrencia(ev, ref)
        salida.append({
            **ev,
            "inicio": inicio,
            "fin": fin,
            "dias": (inicio - ref).days,
            "pueblos": tokens_pueblo(ev["pueblo"]),
            "multi": fin != inicio,
            "mes_corto": MESES_CORTOS[inicio.month - 1],
            "fecha_texto": formato_fecha(inicio),
            "fecha_fin_texto": formato_fecha(fin),
        })
    return sorted(salida, key=lambda e: e["inicio"])


def opciones_pueblo(eventos: list[dict]) -> list[str]:
    pueblo = {t for ev in eventos for t in ev["pueblos"]}
    return ["Todos"] + sorted(pueblo, key=lambda p: p.lower())


def filtrar_eventos(eventos: list[dict], pueblo: str, mes: str, solo_destacados: bool) -> list[dict]:
    salida = []
    for ev in eventos:
        if pueblo not in ("", "todos") and pueblo not in ev["pueblos"]:
            continue
        if solo_destacados and not ev.get("destacado"):
            continue
        if mes == "proximos7" and ev["dias"] > 7:
            continue
        if mes == "proximos30" and ev["dias"] > 30:
            continue
        if mes not in ("", "todos", "proximos7", "proximos30") and ev["inicio"].month != int(mes):
            continue
        salida.append(ev)
    return salida


# --------------------------------------------------------------------------
# Calculador de distancias: Dijkstra sobre los tramos de la hoja de datos
# --------------------------------------------------------------------------
def construir_grafo() -> dict[str, list[dict]]:
    grafo: dict[str, list[dict]] = {k: [] for k in LUGARES}
    for desde, hasta, km, minutos in TRAMOS:
        grafo[desde].append({"a": hasta, "km": km, "min": minutos})
        grafo[hasta].append({"a": desde, "km": km, "min": minutos})
    return grafo


GRAFO = construir_grafo()


def camino_minimo(origen: str, destino: str) -> tuple[list[str], int] | None:
    dist = {k: math.inf for k in LUGARES}
    previo: dict[str, str] = {}
    visto: set[str] = set()
    dist[origen] = 0

    while len(visto) < len(LUGARES):
        candidatos = [k for k in dist if k not in visto and dist[k] < math.inf]
        if not candidatos:
            break
        actual = min(candidatos, key=lambda k: dist[k])
        if actual == destino:
            break
        visto.add(actual)
        for tramo in GRAFO[actual]:
            alt = dist[actual] + tramo["km"]
            if alt < dist[tramo["a"]]:
                dist[tramo["a"]] = alt
                previo[tramo["a"]] = actual

    if dist[destino] == math.inf:
        return None

    camino: list[str] = []
    nodo: str | None = destino
    while nodo:
        camino.insert(0, nodo)
        nodo = previo.get(nodo)
    return camino, int(dist[destino])


def minutos_de_camino(camino: list[str]) -> int:
    total = 0
    for a, b in zip(camino, camino[1:]):
        tramo = next((t for t in GRAFO[a] if t["a"] == b), None)
        total += tramo["min"] if tramo else 0
    return total


def calcular(origen: str, destino: str) -> dict:
    origen = origen if origen in LUGARES else "jujuy"
    destino = destino if destino in LUGARES else "humahuaca"

    if origen == destino:
        return {"error": "Elegí dos lugares distintos para ver el tramo."}

    resultado = camino_minimo(origen, destino)
    if not resultado:
        return {"error": "No hay un tramo directo entre esos puntos: hacé el viaje por la RN9, pasando por Tilcara o Humahuaca."}

    camino, km = resultado
    o, d = LUGARES[origen], LUGARES[destino]
    minutos = minutos_de_camino(camino)
    desnivel = d["alt"] - o["alt"]
    nombres = [LUGARES[k]["corto"] for k in camino]
    ruta_texto = f"Vía {' → '.join(nombres[1:-1])}" if len(nombres) > 2 else "Tramo directo"

    notas: list[str] = []
    if destino == "hornocal":
        notas.append("<strong>Camino de ripio de montaña:</strong> 25 km sin baranda desde Humahuaca. Solo con vehículo alto o excursión 4x4; no subas con lluvia.")
    if destino == "salinas" or "salinas" in camino:
        notas.append("<strong>Se sube a 4.170 m</strong> en la Cuesta del Lipán. Llevá abrigo, agua y protector solar: en el salar el viento y el reflejo son fuertes.")
    if destino in ("calilegua", "vallegrande") or "calilegua" in camino:
        notas.append("<strong>Camino de cornisa:</strong> la RP83 es ripio consolidado y angosto, con curvas, niebla y fauna en la ruta. Manejá de día, despacio y sin apuro.")
    if d["alt"] >= 2800 and o["alt"] < 2800:
        notas.append(f"<strong>Salto de altura de {miles(desnivel)} m.</strong> Andá liviano las primeras horas, tomá agua y evitá el alcohol esa noche.")
    elif d["alt"] >= 3000:
        notas.append("<strong>Estás en la Puna.</strong> Aire seco y frío nocturno: abrigo sí o sí, y nada de esfuerzo grande el primer día.")
    if destino in ("laquiaca", "yavi"):
        notas.append("<strong>Efectivo obligatorio:</strong> cargá pesos en la Quebrada. Después de Humahuaca las cajetas son escasas y hay pueblos sin internet.")
    if km >= 100 and any(k in NORTE for k in camino):
        notas.append("<strong>Llená el tanque antes de salir.</strong> Tilcara tiene la única estación de servicio del tramo central; no cuentes con nafta en los pueblos chicos ni los domingos.")
    if km >= 100 and any(k in ("calilegua", "vallegrande") for k in camino):
        notas.append("<strong>Cargá nafta en San Salvador o en Libertador San Martín.</strong> En la RP83 no hay estaciones de servicio y la señal se corta en buena parte del camino.")
    if minutos >= 90 and destino not in ("salinas", "hornocal"):
        notas.append("<strong>Distancias largas, sin señal:</strong> avisá a alguien tu recorrido y salí con luz de día.")

    return {
        "km": km,
        "minutos": minutos,
        "tiempo": formatear_tiempo(minutos),
        "alt_destino": d["alt"],
        "desnivel": desnivel,
        "desnivel_texto": ("+" if desnivel > 0 else "") + miles(desnivel),
        "o_corto": o["corto"],
        "d_corto": d["corto"],
        "nombres": nombres,
        "ruta_texto": ruta_texto,
        "notas": notas,
    }


app.jinja_env.filters["miles"] = miles


@app.get("/salud")
def salud():
    """Chequeo de vida para el hosting (health check)."""
    return jsonify(estado="ok", destinos=len(DESTINOS), eventos=len(EVENTOS))


@app.get("/")
def index():
    eventos = eventos_con_fecha()
    pueblo = request.args.get("pueblo", "todos")
    mes = request.args.get("mes", "todos")
    solo_destacados = request.args.get("destacados") == "1"
    itin_id = request.args.get("itin", ITINERARIOS[0]["id"])
    origen = request.args.get("origen", "jujuy")
    destino = request.args.get("destino", "humahuaca")

    itinerario = next((i for i in ITINERARIOS if i["id"] == itin_id), ITINERARIOS[0])

    return render_template(
        "index.html",
        ruta=RUTA,
        lugares=LUGARES,
        regiones=REGIONES,
        colores_region=COLOR_REGION,
        destinos=DESTINOS,
        experiencias=EXPERIENCIAS,
        fotos=FOTOS,
        videos=VIDEOS,
        videos_destinos=VIDEOS_DESTINOS,
        videos_experiencias=VIDEOS_EXPERIENCIAS,
        penas=PENAS,
        itinerarios=ITINERARIOS,
        itinerario=itinerario,
        checklist=CHECKLIST,
        meses=MESES,
        eventos=filtrar_eventos(eventos, pueblo, mes, solo_destacados),
        destacados=[e for e in eventos if e.get("destacado")],
        pueblos=opciones_pueblo(eventos),
        pueblo=pueblo,
        mes=mes,
        solo_destacados=solo_destacados,
        cuando=cuando_texto,
        calculo=calcular(origen, destino),
        origen=origen if origen in LUGARES else "jujuy",
        destino=destino if destino in LUGARES else "humahuaca",
        lugares_por_altura=sorted(LUGARES.items(), key=lambda kv: kv[1]["alt"]),
    )


if __name__ == "__main__":
    # Solo para desarrollo: en producción se usa gunicorn (ver gunicorn.conf.py).
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        # Apagado por defecto: para recarga en caliente usá `flask run --debug`.
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
