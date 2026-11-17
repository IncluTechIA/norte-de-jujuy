#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descarga la planilla de la EOH de DIPEC y regenera `estadisticas.json`.

La Encuesta de Ocupación Hotelera la publica DIPEC Jujuy en:

    https://dipec.jujuy.gob.ar/indicadores-economicos/turismo/eoh/

La página enlaza un Excel por año (`eoh_2026_Jujuy`, `eoh_2025_Jujuy`, …) detrás
de un gestor de descargas de WordPress, así que este script primero lee la
página, encuentra el id del archivo del año pedido, lo baja y lo parsea.

Uso:

    python3 scripts/actualizar_estadisticas.py              # último año publicado
    python3 scripts/actualizar_estadisticas.py --anio 2025
    python3 scripts/actualizar_estadisticas.py --archivo /tmp/eoh.xls   # sin red
    python3 scripts/actualizar_estadisticas.py --seco       # solo muestra

Dependencias (no hacen falta para correr el sitio):

    pip install -r requirements-scripts.txt
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

PAGINA = "https://dipec.jujuy.gob.ar/indicadores-economicos/turismo/eoh/"
RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "estadisticas.json"
AGENTE = "Mozilla/5.0 (compatible; norte-de-jujuy/1.0; +https://github.com/IncluTechIA/norte-de-jujuy)"

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# nombre que se muestra, id, hoja de oferta, hoja de demanda, color en el sitio
REGIONES = [
    ("Ciudad de Jujuy", "jujuy", "Jujuy", "Jujuy Demanda", "#8a6a45"),
    ("Quebrada de Humahuaca", "quebrada", "Quebrada", "Quebrada Demanda", "#b23a2f"),
    ("Valles Jujeños", "valles", "Valles", "Valles Demanda", "#5c6f4a"),
    ("Yungas Jujeñas", "yungas", "Yungas", "Yungas Demanda", "#2f6b66"),
]

ETIQUETAS_OFERTA = {
    "establecimientos": "Establecimientos",
    "habitaciones disponibles": "Habitaciones o unidades disponibles",
    "habitaciones ocupadas": "Habitaciones o unidades ocupadas",
    "plazas disponibles": "Plazas disponibles",
}


class ErrorPlanilla(RuntimeError):
    """Problema entendible: archivo que no está, hoja que cambió, etc."""


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def normalizar(valor: Any) -> str:
    """'Habitaciones o unidades disponibles (2)' -> 'habitaciones o unidades disponibles'."""
    texto = str(valor or "").strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\(\d+\)", " ", texto)
    texto = texto.replace("*", " ")
    return re.sub(r"\s+", " ", texto).strip().lower()


def numero(valor: Any) -> float:
    if valor in ("", None):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        raise ErrorPlanilla(f"no pude leer el número «{valor}»") from None


class Hoja:
    """Vista mínima de una hoja de cálculo, sirva xls o xlsx."""

    def __init__(self, filas: Iterable[Iterable[Any]]):
        self.filas = [list(f) for f in filas]

    @property
    def nrows(self) -> int:
        return len(self.filas)

    @property
    def ncols(self) -> int:
        return max((len(f) for f in self.filas), default=0)

    def valor(self, fila: int, col: int) -> Any:
        try:
            return self.filas[fila][col]
        except (IndexError, TypeError):
            return ""


def abrir_libro(ruta: Path) -> dict[str, Hoja]:
    cabecera = ruta.open("rb").read(8)

    if cabecera.startswith(b"\xd0\xcf\x11\xe0"):  # Excel 97-2003 (.xls)
        try:
            import xlrd  # type: ignore
        except ModuleNotFoundError:
            raise ErrorPlanilla(
                "la planilla es .xls y falta xlrd: pip install -r requirements-scripts.txt"
            ) from None
        libro = xlrd.open_workbook(str(ruta))
        return {
            nombre: Hoja(libro.sheet_by_name(nombre).row_values(f)
                         for f in range(libro.sheet_by_name(nombre).nrows))
            for nombre in libro.sheet_names()
        }

    if cabecera.startswith(b"PK"):  # .xlsx
        try:
            import openpyxl  # type: ignore
        except ModuleNotFoundError:
            raise ErrorPlanilla(
                "la planilla es .xlsx y falta openpyxl: pip install -r requirements-scripts.txt"
            ) from None
        libro = openpyxl.load_workbook(ruta, data_only=True)
        return {hoja.title: Hoja(hoja.iter_rows(values_only=True)) for hoja in libro.worksheets}

    raise ErrorPlanilla(
        "el archivo descargado no es un Excel: puede que DIPEC haya cambiado el formato "
        "(¿un PDF?) o que la página haya devuelto un error."
    )


def buscar_hoja(hojas: dict[str, Hoja], nombre: str) -> Hoja:
    for titulo, hoja in hojas.items():
        if normalizar(titulo) == normalizar(nombre):
            return hoja
    disponibles = ", ".join(hojas)
    raise ErrorPlanilla(f"no encontré la hoja «{nombre}» (hay: {disponibles})")


def fila_con_etiqueta(hoja: Hoja, etiqueta: str, saltar: int = 0) -> int:
    for fila in range(hoja.nrows):
        if normalizar(hoja.valor(fila, 0)) == normalizar(etiqueta):
            return fila + saltar
    raise ErrorPlanilla(f"no encontré la fila «{etiqueta}» en la hoja (¿cambió el formato?)")


def columnas_de_meses(hoja: Hoja) -> tuple[int, list[tuple[int, int]]]:
    """Devuelve la fila de encabezados y [(columna, número de mes)] en orden."""
    mejor: tuple[int, list[tuple[int, int]]] | None = None
    for fila in range(min(12, hoja.nrows)):
        encontrados = []
        for col in range(1, hoja.ncols):
            texto = normalizar(hoja.valor(fila, col))
            if texto in MESES:
                encontrados.append((col, MESES.index(texto) + 1))
        if len(encontrados) >= 3 and (mejor is None or len(encontrados) > len(mejor[1])):
            mejor = (fila, encontrados)
    if not mejor:
        raise ErrorPlanilla("no encontré la fila con los meses")
    return mejor


def leer(ruta: Path, anio: int) -> dict[str, Any]:
    hojas = abrir_libro(ruta)

    hoja_jujuy = buscar_hoja(hojas, "Jujuy")
    fila_meses, meses = columnas_de_meses(hoja_jujuy)

    dias = [calendar.monthrange(anio, mes)[1] for _, mes in meses]
    # En el encabezado, DIPEC marca con un asterisco la columna siguiente al mes
    # cuando ese mes todavía es provisorio.
    provisorios = [
        MESES[mes - 1]
        for col, mes in meses
        if str(hoja_jujuy.valor(fila_meses, col + 1)).strip() == "*"
    ]

    regiones = []
    for nombre, rid, hoja_oferta, hoja_demanda, color in REGIONES:
        oferta = buscar_hoja(hojas, hoja_oferta)
        demanda = buscar_hoja(hojas, hoja_demanda)

        def serie(hoja: Hoja, etiqueta: str, saltar: int = 0) -> list[float]:
            fila = fila_con_etiqueta(hoja, etiqueta, saltar)
            return [numero(hoja.valor(fila, col)) for col, _ in meses]

        pernoctaciones = serie(demanda, "Pernoctaciones")
        residentes = serie(demanda, "Residentes")
        viajeros = serie(demanda, "Viajeros")

        hab_disponibles = serie(oferta, ETIQUETAS_OFERTA["habitaciones disponibles"], saltar=1)
        hab_ocupadas = serie(oferta, ETIQUETAS_OFERTA["habitaciones ocupadas"], saltar=1)
        plazas = serie(oferta, ETIQUETAS_OFERTA["plazas disponibles"], saltar=1)
        establecimientos = serie(oferta, ETIQUETAS_OFERTA["establecimientos"], saltar=1)

        if not any(pernoctaciones) or not any(viajeros):
            raise ErrorPlanilla(f"la hoja «{hoja_demanda}» vino sin datos de demanda")

        plazas_dia = [p / d for p, d in zip(plazas, dias) if d]
        regiones.append({
            "nombre": nombre,
            "id": rid,
            "pernoctaciones": int(sum(pernoctaciones)),
            "viajeros": int(sum(viajeros)),
            "estadia": round(sum(pernoctaciones) / sum(viajeros), 2),
            "ocupacion": round(sum(hab_ocupadas) / sum(hab_disponibles) * 100, 1),
            "plazas": int(sum(plazas_dia) / len(plazas_dia)) if plazas_dia else 0,
            "establecimientos": int(establecimientos[-1]),
            "residentes_pct": round(sum(residentes) / sum(pernoctaciones) * 100, 1),
            "por_mes": [int(v) for v in pernoctaciones],
            "color": color,
        })

    total_pernoctaciones = sum(r["pernoctaciones"] for r in regiones)
    total_viajeros = sum(r["viajeros"] for r in regiones)
    for region in regiones:
        region["parte"] = round(region["pernoctaciones"] / total_pernoctaciones * 100, 1)

    regiones.sort(key=lambda r: -r["pernoctaciones"])

    nombres_meses = [MESES[mes - 1] for _, mes in meses]
    nota = ""
    if provisorios:
        nota = f"{' y '.join(provisorios).capitalize()} son datos provisorios. "
    nota += (
        "La EOH releva establecimientos de más de 12 plazas en las cuatro regiones "
        "y se actualiza todos los meses."
    )

    return {
        "fuente": "DIPEC Jujuy e INDEC · Encuesta de Ocupación Hotelera (EOH)",
        "url": PAGINA,
        "periodo": f"{nombres_meses[0]} a {nombres_meses[-1]} de {anio}",
        "anio": anio,
        "meses": [m.capitalize() for m in nombres_meses],
        "nota": nota,
        "total": {
            "pernoctaciones": total_pernoctaciones,
            "viajeros": total_viajeros,
            "estadia": round(total_pernoctaciones / total_viajeros, 2),
            "plazas": sum(r["plazas"] for r in regiones),
            "establecimientos": sum(r["establecimientos"] for r in regiones),
        },
        "serie": [sum(r["por_mes"][i] for r in regiones) for i in range(len(meses))],
        "regiones": regiones,
    }


# --------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------
def bajar_texto(url: str, timeout: int = 60) -> str:
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "es-AR,es;q=0.9"})
    with urllib.request.urlopen(pedido, timeout=timeout) as respuesta:
        return respuesta.read().decode("utf-8", "replace")


def planillas(html: str) -> dict[int, dict[str, str]]:
    """Año -> {id, categoria, titulo} leyendo los enlaces del gestor de descargas."""
    encontradas: dict[int, dict[str, str]] = {}
    for etiqueta in re.findall(r"<a\b[^>]*>", html, flags=re.IGNORECASE):
        titulo = re.search(r'title="([^"]*eoh[^"]*)"', etiqueta, flags=re.IGNORECASE)
        ident = re.search(r'data-id="(\d+)"', etiqueta)
        if not (titulo and ident):
            continue
        anio = re.search(r"(20\d{2})", titulo.group(1))
        categoria = re.search(r'data-category_id="(\d+)"', etiqueta)
        if not anio:
            continue
        encontradas[int(anio.group(1))] = {
            "id": ident.group(1),
            "categoria": categoria.group(1) if categoria else "0",
            "titulo": titulo.group(1),
        }
    return encontradas


def descargar(anio: int | None) -> tuple[Path, str, int]:
    html = bajar_texto(PAGINA)
    disponibles = planillas(html)
    if not disponibles:
        raise ErrorPlanilla(
            "la página de DIPEC no mostró planillas: puede que hayan cambiado el gestor "
            "de descargas. Probá con --archivo si ya la bajaste a mano."
        )

    elegido = max(disponibles) if anio is None else anio
    if elegido not in disponibles:
        años = ", ".join(str(a) for a in sorted(disponibles))
        raise ErrorPlanilla(f"no hay planilla de {elegido} en la página (sí de: {años})")

    datos = disponibles[elegido]
    url = (
        "https://dipec.jujuy.gob.ar/wp-admin/admin-ajax.php"
        "?juwpfisadmin=false&action=wpfd&task=file.download"
        f"&wpfd_category_id={datos['categoria']}&wpfd_file_id={datos['id']}"
    )
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=120) as respuesta:
        contenido = respuesta.read()
    if len(contenido) < 5000:
        raise ErrorPlanilla("la descarga vino vacía o demasiado chica; probá de nuevo en un rato")

    sufijo = ".xlsx" if contenido[:2] == b"PK" else ".xls"
    archivo = Path(tempfile.mkstemp(prefix=f"eoh_{elegido}_", suffix=sufijo)[1])
    archivo.write_bytes(contenido)
    return archivo, datos["titulo"], elegido


# --------------------------------------------------------------------------
# Programa
# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Regenera estadisticas.json con la EOH de DIPEC.")
    parser.add_argument("--anio", type=int, help="año de la planilla (por defecto, la última publicada)")
    parser.add_argument("--archivo", type=Path, help="usar un Excel ya descargado en vez de bajar")
    parser.add_argument("--salida", type=Path, default=SALIDA, help=f"JSON de salida (por defecto {SALIDA})")
    parser.add_argument("--seco", action="store_true", help="mostrar el resultado sin escribir el archivo")
    args = parser.parse_args()

    try:
        if args.archivo:
            ruta, planilla, anio = args.archivo, args.archivo.name, args.anio
            if anio is None:
                match = re.search(r"(20\d{2})", ruta.name)
                if not match:
                    raise ErrorPlanilla("con --archivo hace falta --anio (no lo pude sacar del nombre)")
                anio = int(match.group(1))
        else:
            ruta, planilla, anio = descargar(args.anio)

        datos = leer(ruta, anio)
    except (ErrorPlanilla, urllib.error.URLError, TimeoutError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    texto = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"
    total = datos["total"]

    print(f"planilla: {planilla} · {datos['periodo']}")
    print(f"  pernoctaciones {total['pernoctaciones']:,} · viajeros {total['viajeros']:,} "
          f"· estadía {total['estadia']} · plazas {total['plazas']:,}".replace(",", "."))
    for region in datos["regiones"]:
        print(f"  {region['nombre']:<22} {region['pernoctaciones']:>8,} noches "
              f"({region['parte']} %)".replace(",", "."))

    if args.seco:
        print("\n(--seco: no escribí el archivo)")
        return 0

    anterior = args.salida.read_text(encoding="utf-8") if args.salida.exists() else ""
    args.salida.write_text(texto, encoding="utf-8")
    if anterior == texto:
        print(f"\nsin cambios: {args.salida.name} ya estaba al día")
    else:
        print(f"\nescrito {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
