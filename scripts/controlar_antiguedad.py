#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controla que `estadisticas.json` no se quede viejo.

El workflow mensual compara el archivo consigo mismo: si DIPEC no publica meses
nuevos, el script no cambia nada y la corrida termina en verde igual. Este
control mira la antigüedad del período publicado y falla cuando el último mes
cubierto quedó más de `--max-meses` meses atrás del mes actual.

Uso:

    python3 scripts/controlar_antiguedad.py
    python3 scripts/controlar_antiguedad.py --max-meses 2
    python3 scripts/controlar_antiguedad.py --archivo /tmp/otro.json
    python3 scripts/controlar_antiguedad.py --hoy 2027-03-15   # para probar

Sale con código 0 si está al día y con 1 (más un mensaje claro en stderr) si no.
En el workflow ese 1 pone la corrida en rojo y dispara el issue con la etiqueta
«estadisticas».
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "estadisticas.json"


def normalizar(valor: Any) -> str:
    """'Mayo' / 'MAYO' / 'mayo.' -> 'mayo'."""
    texto = str(valor or "").strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.strip(" .").lower()
    return texto


def ultimo_mes(datos: dict[str, Any]) -> tuple[int, int]:
    """Devuelve (año, mes) del último mes cubierto por el archivo."""
    if "anio" not in datos:
        raise ValueError("el archivo no tiene el campo «anio»")

    try:
        anio = int(datos["anio"])
    except (TypeError, ValueError):
        raise ValueError(f"«anio» no es un número: {datos['anio']!r}")

    meses = datos.get("meses") or []
    if not isinstance(meses, list) or not meses:
        raise ValueError("el archivo no tiene la lista «meses»")

    numeros = []
    for nombre in meses:
        texto = normalizar(nombre)
        if texto in MESES:
            numeros.append(MESES.index(texto) + 1)
    if not numeros:
        raise ValueError(f"no reconocí ningún mes en «meses»: {meses!r}")

    return anio, max(numeros)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archivo", default=str(ARCHIVO), help="JSON a revisar")
    parser.add_argument(
        "--max-meses",
        type=int,
        default=2,
        help="atraso tolerado en meses (por defecto 2)",
    )
    parser.add_argument(
        "--hoy",
        default=None,
        help="fecha de referencia en formato AAAA-MM-DD (por defecto, hoy)",
    )
    args = parser.parse_args()

    ruta = Path(args.archivo)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: no existe {ruta}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: {ruta} no es JSON válido ({exc})", file=sys.stderr)
        return 1

    if not isinstance(datos, dict):
        print(f"error: {ruta} no contiene un objeto JSON", file=sys.stderr)
        return 1

    try:
        anio, mes = ultimo_mes(datos)
    except ValueError as exc:
        print(f"error: no pude leer el período de {ruta}: {exc}", file=sys.stderr)
        return 1

    if args.hoy:
        try:
            hoy = date.fromisoformat(args.hoy)
        except ValueError:
            print(f"error: --hoy no es una fecha AAAA-MM-DD: {args.hoy!r}", file=sys.stderr)
            return 1
    else:
        hoy = date.today()

    atraso = (hoy.year - anio) * 12 + (hoy.month - mes)
    periodo = f"{MESES[mes - 1]} de {anio}"
    hoy_texto = f"{MESES[hoy.month - 1]} de {hoy.year}"

    if atraso > args.max_meses:
        print(
            f"atraso: {ruta.name} llega a {periodo} y estamos en {hoy_texto}: "
            f"{atraso} meses sin datos nuevos (el máximo aceptado es {args.max_meses}).",
            file=sys.stderr,
        )
        print(
            "Revisá https://dipec.jujuy.gob.ar/indicadores-economicos/turismo/eoh/ "
            "y probá `python3 scripts/actualizar_estadisticas.py --seco`.",
            file=sys.stderr,
        )
        return 1

    print(
        f"al día: {ruta.name} llega a {periodo}, {atraso} mes(es) de atraso "
        f"sobre {hoy_texto} (máximo {args.max_meses})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
