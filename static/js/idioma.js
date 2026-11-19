/* ============================================================
   Selector de idioma.

   El español es el idioma original y vive en el HTML. Cada idioma
   tiene un diccionario en /static/i18n/<código>.json con las mismas
   frases en español como clave; acá se recorre el texto de la página
   y se reemplaza lo que tenga traducción. Lo que no esté traducido
   se queda en español, así que se pueden ir agregando frases sin
   tocar la plantilla.

   La elección se guarda en una cookie (para que Flask ponga el
   atributo lang correcto en la próxima visita) y en localStorage.
   ============================================================ */
(function () {
  "use strict";

  const IDIOMAS = [
    { codigo: "es", nombre: "Español", corto: "ES", html: "es-AR" },
    { codigo: "en", nombre: "English", corto: "EN", html: "en" },
    { codigo: "pt", nombre: "Português", corto: "PT", html: "pt-BR" },
    { codigo: "fr", nombre: "Français", corto: "FR", html: "fr" }
  ];
  const CLAVE = "jujuy-idioma";   // localStorage
  const COOKIE = "idioma";        // la misma cookie que lee Flask en app.py
  const UN_ANIO = 60 * 60 * 24 * 365;

  const boton = document.querySelector(".lang-btn");
  const menu = document.querySelector(".lang-menu");
  const caja = document.querySelector(".lang-switch");
  const nota = document.getElementById("nota-idioma");
  if (!boton || !menu) return;

  const originales = new WeakMap();   // nodo de texto -> texto original
  const atributos = new WeakMap();    // elemento -> { atributo: valor original }
  let datos = null;                   // diccionario del idioma activo
  let idioma = leerGuardado() || document.documentElement.dataset.idioma || "es";
  let tituloOriginal = document.title;
  let descripcionOriginal = null;

  /* ---------- utilidades ---------- */

  function normalizar(texto) {
    return texto.replace(/\s+/g, " ").trim();
  }

  function plantilla(texto, valores) {
    return texto.replace(/\{(\w+)\}/g, function (todo, clave) {
      return Object.prototype.hasOwnProperty.call(valores, clave) ? valores[clave] : todo;
    });
  }

  function mes(nombre) {
    return (datos.meses[nombre.toLowerCase()] || nombre);
  }

  // Los números en inglés llevan coma de miles y punto decimal.
  function numero(valor) {
    if (idioma !== "en") return valor;
    if (/^\d{1,3}(\.\d{3})+$/.test(valor)) return valor.replace(/\./g, ",");
    if (/^\d{1,3}(\.\d{3})+,\d+$/.test(valor)) {
      return valor.replace(/\./g, "").replace(",", ".");
    }
    if (/^\d+,\d+$/.test(valor)) return valor.replace(",", ".");
    return valor;
  }

  function numeros(texto) {
    if (idioma !== "en") return texto;
    return texto.replace(/\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+/g, numero);
  }

  /* ---------- fechas y períodos ---------- */

  const FECHA = /^(\d{1,2}) de ([a-záéíóúñ]+) de (\d{4})$/i;
  const RANGO = /^(\d{1,2}) al (\d{1,2}) de ([a-záéíóúñ]+) de (\d{4})$/i;
  const RANGO_MES = /^(\d{1,2}) de ([a-záéíóúñ]+) al (\d{1,2}) de ([a-záéíóñ]+) de (\d{4})$/i;
  const RANGO_COMPLETO = /^(\d{1,2}) de ([a-záéíóúñ]+) de (\d{4}) al (\d{1,2}) de ([a-záéíóúñ]+) de (\d{4})$/i;

  function fecha(texto) {
    let m = FECHA.exec(texto);
    if (m) return plantilla(datos.fechas.dia, { d: m[1], mes: mes(m[2]), a: m[3] });

    m = RANGO.exec(texto);
    if (m) {
      return plantilla(datos.fechas.rango, { d1: m[1], d2: m[2], mes: mes(m[3]), a: m[4] });
    }

    m = RANGO_MES.exec(texto);
    if (m) {
      return plantilla(datos.fechas.rango_mes, {
        d1: m[1], m1: mes(m[2]), d2: m[3], m2: mes(m[4]), a: m[5]
      });
    }

    m = RANGO_COMPLETO.exec(texto);
    if (m) {
      const a = plantilla(datos.fechas.dia, { d: m[1], mes: mes(m[2]), a: m[3] });
      const b = plantilla(datos.fechas.dia, { d: m[4], mes: mes(m[5]), a: m[6] });
      return a + " – " + b;
    }

    return null;
  }

  function periodo(texto) {
    const m = /^([a-záéíóúñ]+)(?: a ([a-záéíóúñ]+))? de (\d{4})$/i.exec(texto);
    if (!m) return null;
    if (m[2]) return plantilla(datos.periodo.rango, { m1: mes(m[1]), m2: mes(m[2]), a: m[3] });
    return plantilla(datos.periodo.mes, { m: mes(m[1]), a: m[3] });
  }

  /* ---------- reglas para los textos que arma el servidor ---------- */

  function reglas(texto) {
    let m;

    m = /^Fecha: (.+)\.$/.exec(texto);
    if (m) {
      const f = fecha(m[1]) || m[1];
      return plantilla(datos.patrones.prefijo_fecha, { f: f });
    }

    m = /^Última revisión del contenido: (.+)\.$/.exec(texto);
    if (m) {
      const f = fecha(m[1]) || m[1];
      return plantilla(datos.patrones.revision, { f: f });
    }

    const f = fecha(texto);
    if (f) return f;

    const p = periodo(texto);
    if (p) return p;

    m = /^En (\d+) días$/.exec(texto);
    if (m) return plantilla(datos.patrones.en_dias, { n: m[1] });

    m = /^Día (\d+)$/.exec(texto);
    if (m) return plantilla(datos.patrones.dia, { n: m[1] });

    m = /^(\d+) eventos?$/.exec(texto);
    if (m) {
      const clave = m[1] === "1" ? "evento" : "eventos";
      return plantilla(datos.patrones[clave], { n: m[1] });
    }

    m = /^([\d.,]+) noches$/.exec(texto);
    if (m) return plantilla(datos.patrones.noches, { n: m[1] });

    m = /^(\d+) días$/.exec(texto);
    if (m) return plantilla(datos.patrones.dias, { n: m[1] });

    m = /^([\d.,]+) a ([\d.,]+) m s\. n\. m\.$/.exec(texto);
    if (m) return plantilla(datos.patrones.msnm_rango, { a: m[1], b: m[2] });

    m = /^([\d.,]+) m s\. n\. m\.$/.exec(texto);
    if (m) return plantilla(datos.patrones.msnm, { n: m[1] });

    m = /^Máx\. ([\d.,]+) m$/.exec(texto);
    if (m) return plantilla(datos.patrones.msnm_max, { n: m[1] });

    m = /^([\d.,]+) km de (.+)$/.exec(texto);
    if (m) return plantilla(datos.patrones.km_desde, { n: m[1], l: m[2] });

    m = /^([\d.,]+) km$/.exec(texto);
    if (m) return plantilla(datos.patrones.km, { n: m[1] });

    m = /^([\d.,]+) m$/.exec(texto);
    if (m) return plantilla(datos.patrones.m, { n: m[1] });

    m = /^Salto de altura de ([\d.,]+) m\.$/.exec(texto);
    if (m) return plantilla(datos.patrones.salto, { n: m[1] });

    m = /^promedio diario, en (\d+) establecimientos$/.exec(texto);
    if (m) return plantilla(datos.patrones.promedio, { n: m[1] });

    m = /^Porcentaje de las pernoctaciones que hicieron personas que no residen en Jujuy\. En toda la provincia son ([\d.]+) noches sobre ([\d.]+) \(([\d,]+) %\)\.$/.exec(texto);
    if (m) return plantilla(datos.patrones.no_resid, { n: m[1], t: m[2], p: m[3] });

    m = /^Plazas ocupadas sobre plazas disponibles en el período, que es el otro termómetro de la ocupación además de las habitaciones\. Total provincial: ([\d,]+) %\.$/.exec(texto);
    if (m) return plantilla(datos.patrones.ocup_plazas, { n: m[1] });

    m = /^Vía (.+)$/.exec(texto);
    if (m) return plantilla(datos.patrones.via, { r: m[1] });

    return null;
  }

  function traducir(texto) {
    if (!datos) return null;
    const clave = normalizar(texto);
    if (!clave) return null;
    if (/^[\d.,\s%+–—-]+$/.test(clave)) return null;   // solo números: los formatea numeros()
    const regla = reglas(clave);
    if (regla) return numeros(regla);
    if (Object.prototype.hasOwnProperty.call(datos.textos, clave)) {
      return numeros(datos.textos[clave]);
    }
    return null;
  }

  /* ---------- recorrido del DOM ---------- */

  function textoDe(nodo) {
    const valor = nodo.nodeValue;
    if (!originales.has(nodo)) originales.set(nodo, valor);
    const original = originales.get(nodo);
    const partes = /^(\s*)([\s\S]*?)(\s*)$/.exec(original);
    if (!partes || !partes[2]) return null;
    return { nodo: nodo, antes: partes[1], texto: partes[2], despues: partes[3] };
  }

  function traducirArbol(raiz) {
    const pila = [raiz];
    while (pila.length) {
      const nodo = pila.pop();
      if (nodo.nodeType === 1) {
        const etiqueta = nodo.tagName;
        if (etiqueta === "SCRIPT" || etiqueta === "STYLE" || etiqueta === "NOSCRIPT") continue;
        if (nodo.hasAttribute("data-no-i18n")) continue;
        for (let i = nodo.childNodes.length - 1; i >= 0; i--) pila.push(nodo.childNodes[i]);
      } else if (nodo.nodeType === 3) {
        const info = textoDe(nodo);
        if (!info) continue;
        const nueva = traducir(info.texto);
        nodo.nodeValue = info.antes + (nueva === null ? numeros(info.texto) : nueva) + info.despues;
      }
    }
  }

  const ATRIBUTOS = ["alt", "title", "aria-label", "placeholder"];

  function traducirAtributos() {
    ATRIBUTOS.forEach(function (nombre) {
      document.querySelectorAll("[" + nombre + "]").forEach(function (el) {
        if (el.closest("[data-no-i18n]")) return;
        let guardados = atributos.get(el);
        if (!guardados) {
          guardados = {};
          atributos.set(el, guardados);
        }
        if (!Object.prototype.hasOwnProperty.call(guardados, nombre)) {
          guardados[nombre] = el.getAttribute(nombre);
        }
        const original = guardados[nombre];
        if (!original) return;
        const nueva = traducir(original);
        if (nueva !== null) el.setAttribute(nombre, nueva);
      });
    });
  }

  function traducirCabecera() {
    if (!datos) return;
    tituloOriginal = document.documentElement.dataset.titulo || tituloOriginal;
    const titulo = traducir(tituloOriginal);
    if (titulo) document.title = titulo;
    const meta = document.querySelector('meta[name="description"]');
    if (meta) {
      if (descripcionOriginal === null) descripcionOriginal = meta.getAttribute("content") || "";
      const desc = traducir(descripcionOriginal);
      if (desc) meta.setAttribute("content", desc);
    }
  }

  function restaurar() {
    (function recorrer(raiz) {
      const pila = [raiz];
      while (pila.length) {
        const nodo = pila.pop();
        if (nodo.nodeType === 1) {
          for (let i = nodo.childNodes.length - 1; i >= 0; i--) pila.push(nodo.childNodes[i]);
        } else if (nodo.nodeType === 3 && originales.has(nodo)) {
          nodo.nodeValue = originales.get(nodo);
        }
      }
    })(document.body);

    ATRIBUTOS.forEach(function (nombre) {
      document.querySelectorAll("[" + nombre + "]").forEach(function (el) {
        const guardados = atributos.get(el);
        if (guardados && Object.prototype.hasOwnProperty.call(guardados, nombre)) {
          el.setAttribute(nombre, guardados[nombre]);
        }
      });
    });

    const meta = document.querySelector('meta[name="description"]');
    if (meta && descripcionOriginal !== null) meta.setAttribute("content", descripcionOriginal);
    document.title = tituloOriginal;
  }

  /* ---------- estado del idioma ---------- */

  function esIdioma(codigo) {
    return IDIOMAS.some(function (i) { return i.codigo === codigo; });
  }

  // Idioma elegido en una visita anterior (localStorage o cookie), o null.
  function leerGuardado() {
    try {
      const guardado = localStorage.getItem(CLAVE);
      if (guardado && esIdioma(guardado)) return guardado;
    } catch (error) { /* modo privado */ }
    const partes = document.cookie.split(";");
    for (let i = 0; i < partes.length; i++) {
      const par = partes[i].trim().split("=");
      if (par[0] === COOKIE && esIdioma(par[1])) return par[1];
    }
    return null;
  }

  function guardar(codigo) {
    try {
      localStorage.setItem(CLAVE, codigo);
    } catch (error) { /* modo privado */ }
    document.cookie = COOKIE + "=" + codigo + ";path=/;max-age=" + UN_ANIO + ";SameSite=Lax";
  }

  function pintarBoton(codigo) {
    const info = IDIOMAS.find(function (i) { return i.codigo === codigo; }) || IDIOMAS[0];
    const actual = boton.querySelector(".lang-code");
    if (actual) actual.textContent = info.corto;
    boton.setAttribute("aria-label", (datos && datos.textos["Cambiar idioma"]) || "Cambiar idioma");
    menu.querySelectorAll("button[data-idioma]").forEach(function (opcion) {
      opcion.setAttribute("aria-pressed", String(opcion.dataset.idioma === codigo));
    });
  }

  function idiomaHtml(codigo) {
    const info = IDIOMAS.find(function (i) { return i.codigo === codigo; });
    return info ? info.html : "es-AR";
  }

  function aplicar(codigo) {
    const anterior = idioma;
    idioma = codigo;
    document.documentElement.lang = idiomaHtml(codigo);
    document.documentElement.dataset.idioma = codigo;

    if (codigo === "es") {
      if (anterior !== "es") restaurar();
      datos = null;
      if (nota) nota.hidden = true;
      pintarBoton("es");
      guardar("es");
      return;
    }

    cargar(codigo).then(function (diccionario) {
      datos = diccionario;
      if (anterior !== "es") restaurar();
      traducirArbol(document.body);
      traducirAtributos();
      traducirCabecera();
      if (nota) {
        nota.textContent = datos.nota;
        nota.hidden = false;
      }
      pintarBoton(codigo);
      guardar(codigo);
    }).catch(function () {
      idioma = anterior;
      document.documentElement.lang = idiomaHtml(anterior);
      pintarBoton(anterior);
    });
  }

  const cache = {};
  function cargar(codigo) {
    if (cache[codigo]) return Promise.resolve(cache[codigo]);
    return fetch("/static/i18n/" + codigo + ".json", { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) throw new Error("No se pudo cargar el idioma");
        return r.json();
      })
      .then(function (diccionario) {
        cache[codigo] = diccionario;
        return diccionario;
      });
  }

  /* ---------- menú ---------- */

  function abrir() {
    menu.hidden = false;
    boton.setAttribute("aria-expanded", "true");
    const activo = menu.querySelector('button[aria-pressed="true"]') || menu.querySelector("button");
    if (activo) activo.focus();
  }

  function cerrar() {
    menu.hidden = true;
    boton.setAttribute("aria-expanded", "false");
  }

  boton.addEventListener("click", function (evento) {
    evento.stopPropagation();
    if (menu.hidden) abrir();
    else cerrar();
  });

  menu.addEventListener("click", function (evento) {
    const opcion = evento.target.closest("button[data-idioma]");
    if (!opcion) return;
    aplicar(opcion.dataset.idioma);
    cerrar();
    boton.focus();
  });

  document.addEventListener("click", function (evento) {
    if (!menu.hidden && caja && !caja.contains(evento.target)) cerrar();
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape" && !menu.hidden) {
      cerrar();
      boton.focus();
    }
  });

  /* ---------- arranque ---------- */

  pintarBoton(idioma);
  if (idioma !== "es") aplicar(idioma);
})();
