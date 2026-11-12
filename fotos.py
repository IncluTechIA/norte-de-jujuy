# -*- coding: utf-8 -*-
"""Fotos de las tarjetas y color de cada región.

Todas las imágenes son fotografías de Wikimedia Commons con licencia libre,
recortadas a 900 × 411 y guardadas en static/img/fotos/.
"""

FOTOS = {
    "Purmamarca": {
        "k": "purmamarca",
        "cred": "Bernard Gagnon / CC BY-SA 4.0",
        "alt": "El Cerro de los Siete Colores sobre el pueblo de Purmamarca",
    },
    "Maimará": {
        "k": "maimara",
        "cred": "Adam Jones / CC BY-SA 3.0",
        "alt": "La Paleta del Pintor sobre el pueblo de Maimará",
    },
    "Tilcara": {
        "k": "tilcara",
        "cred": "Bernard Gagnon / CC BY-SA 4.0",
        "alt": "El Pucará de Tilcara con su monumento de piedra y cardones",
    },
    "Huacalera": {
        "k": "huacalera",
        "cred": "Maxihuacalera / CC BY 4.0",
        "alt": "Huacalera vista desde El Pucará, con el valle y la ruta",
    },
    "Uquía": {
        "k": "uquia",
        "cred": "Bernard Gagnon / CC BY-SA 4.0",
        "alt": "El campanario de la iglesia de Uquía contra el cielo",
    },
    "Humahuaca": {
        "k": "humahuaca",
        "cred": "kdgabbo / CC BY-SA 3.0",
        "alt": "Calle empedrada del centro histórico de Humahuaca",
    },
    "Salinas Grandes": {
        "k": "salinas",
        "cred": "Bernard Gagnon / CC BY-SA 4.0",
        "alt": "El salar de Salinas Grandes con sus piletones y montañas de sal",
    },
    "Calilegua": {
        "k": "calilegua",
        "cred": "Andrés Octavio Arias / CC BY-SA 4.0",
        "alt": "Sendero de tierra en la selva del parque nacional Calilegua",
    },
    "San Salvador de Jujuy": {
        "k": "capital",
        "cred": "Julio Benitez / CC BY 3.0",
        "alt": "La catedral de San Salvador de Jujuy frente a la plaza",
    },
    "Ruta del Vino de Altura": {
        "k": "vino",
        "cred": "Micah MacAllen / CC BY-SA 2.0",
        "alt": "Viñedo de altura del noroeste argentino con la cordillera de fondo",
    },
    "Turismo comunitario": {
        "k": "comunitario",
        "cred": "Vanina Rossi / CC BY-SA 4.0",
        "alt": "Puestos de telares y artesanías en la feria de Purmamarca",
    },
    "Trekking y aventura": {
        "k": "trekking",
        "cred": "Jorge Oscar Benítez / CC BY-SA 4.0",
        "alt": "Arriero con caballo de carga en la quebrada",
    },
    "Selva y aves de las Yungas": {
        "k": "aves",
        "cred": "Bernard Dupont / CC BY-SA 2.0",
        "alt": "Un tucán grande posado en una rama de la selva",
    },
    "Termas y ríos cerca de la capital": {
        "k": "termas",
        "cred": "Fernando Locatelli / CC BY 3.0",
        "alt": "Una pileta de aguas termales entre rocas",
    },
}

# Un video por región: el ID de YouTube, el título real del video y su canal.
# Se incrustan con click (miniaturas propias de YouTube) para no cargar el
# reproductor hasta que alguien lo pide.
VIDEOS = {
    "puna": {
        "id": "jZMWNnEuol0",
        "titulo": "Las Salinas Grandes en Jujuy: tips y recomendaciones",
        "canal": "Destinos Argentina",
    },
    "quebrada": {
        "id": "Gz9lNXgJbt8",
        "titulo": "Humahuaca, el imperdible de Jujuy",
        "canal": "Gonza & Agus",
    },
    "valles": {
        "id": "QFpm-7PqYs4",
        "titulo": "Así es San Salvador de Jujuy: qué hacer y dónde comer",
        "canal": "Gonza & Agus",
    },
    "yungas": {
        "id": "O0tDatEaFhg",
        "titulo": "Yungas de Jujuy: maravilla oculta",
        "canal": "TripinTV",
    },
}

# Un video por destino y por experiencia. Los títulos son los reales de
# YouTube; en las tarjetas se muestran recortados a dos líneas.
VIDEOS_DESTINOS = {
    "Purmamarca": {
        "id": "NmCo3nVHkIc",
        "titulo": "Este es el pueblo mas hermoso de Argentina | Purmamarca y Salinas Grandes, Jujuy",
        "canal": "Pablo Sabarotz",
    },
    "Maimará": {
        "id": "WaM-8JJIKQU",
        "titulo": "Este PUEBLO es HERMOSO ➜ PAISAJES INCREIBLES: MAIMARÁ JUJUY",
        "canal": "Conociendo Lugares",
    },
    "Tilcara": {
        "id": "0-6DVBdmV7Y",
        "titulo": "El pueblo que es Patrimonio de la Humanidad y corazón de la Quebrada de Humahuaca | Tilcara, Jujuy",
        "canal": "Pablo Sabarotz",
    },
    "Huacalera": {
        "id": "nFsSpfKC0Ro",
        "titulo": "Huacalera (Jujuy) - Un lugar histórico y un pueblo para visitar",
        "canal": "Esteban por Argentina y el Mundo",
    },
    "Uquía": {
        "id": "AKgCAft8bgM",
        "titulo": "UQUIA en Jujuy. Iglesia con ángeles arcabuceros",
        "canal": "Viajando con Cesar",
    },
    "Humahuaca": {
        "id": "9EFQq-qSDZk",
        "titulo": "QUEBRADA de HUMAHUACA ➜ Este PUEBLO es HERMOSO: HUMAHUACA - JUJUY",
        "canal": "Conociendo Lugares",
    },
    "Salinas Grandes": {
        "id": "FEKiFAvly4c",
        "titulo": "SALINAS GRANDES JUJUY",
        "canal": "Conociendo Lugares",
    },
    "Calilegua": {
        "id": "Oa4XPPtjmZ0",
        "titulo": "Parque Nacional CALILEGUA | YUNGAS JUJEÑAS | San Francisco | Jujuy",
        "canal": "Gino Valentini En Moto por Argentina",
    },
    "San Salvador de Jujuy": {
        "id": "Ogc-uCbLI-g",
        "titulo": "RECORRIENDO SAN SALVADOR DE JUJUY | MERCADO CENTRAL Y FERIA DE ARTESANOS",
        "canal": "Matias Juri",
    },
}

VIDEOS_EXPERIENCIAS = {
    "Ruta del Vino de Altura": {
        "id": "N09zv4rXev0",
        "titulo": "De altura: vinos orgánicos de Jujuy",
        "canal": "DW Español",
    },
    "Turismo comunitario": {
        "id": "sWYWirIA7rU",
        "titulo": "QUÉ HACER en Hornaditas: Turismo Comunitario en Jujuy",
        "canal": "De Jujuy Turismo",
    },
    "Trekking y aventura": {
        "id": "llJ0a7mvJjs",
        "titulo": "La travesía más increíble de Jujuy: Tilcara - Calilegua",
        "canal": "Mons Actividades de Montaña",
    },
    "Selva y aves de las Yungas": {
        "id": "ey1_IECFQMk",
        "titulo": "Explorando la SELVA ARGENTINA - Animales en las yungas de Jujuy",
        "canal": "Santiago Arias Fotógrafo",
    },
    "Termas y ríos cerca de la capital": {
        "id": "p21_epdGw_c",
        "titulo": "Termas de Reyes - Jujuy",
        "canal": "Magazine Mujer TV",
    },
}

COLOR_REGION = {
    "Puna": "#d99a2b",
    "Quebrada": "#b23a2f",
    "Valles": "#5c6f4a",
    "Yungas": "#2f6b66",
}
