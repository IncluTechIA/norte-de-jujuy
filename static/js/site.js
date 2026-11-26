/* ============================================================
   Interacciones mínimas: el HTML ya viene armado desde Flask.
   - La agenda se filtra en el servidor; acá solo se envía el form.
   - Checklist con memoria en localStorage.
   ============================================================ */
(function () {
  "use strict";

  const form = document.getElementById("agenda-form");
  if (form) {
    ["filtro-mes", "filtro-destacados"].forEach((id) => {
      const campo = document.getElementById(id);
      if (campo) campo.addEventListener("change", () => form.submit());
    });
  }

  // Video de cada región: la miniatura ocupa el lugar del reproductor hasta
  // que se hace click, así la página no carga cuatro iframes de YouTube.
  document.querySelectorAll(".rv-play").forEach((btn) => {
    btn.addEventListener("click", () => {
      const marco = document.createElement("iframe");
      marco.className = "rv-frame";
      marco.src = "https://www.youtube-nocookie.com/embed/" + btn.dataset.video + "?autoplay=1&rel=0";
      marco.title = btn.dataset.titulo || "Video de la región";
      marco.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      marco.allowFullscreen = true;
      marco.loading = "lazy";
      btn.replaceWith(marco);
    });
  });

  // Mapa interactivo de las cuatro regiones (Leaflet + OpenStreetMap).
  // Un punto por localidad, con su departamento, y la leyenda para prender o
  // apagar cada región. Si Leaflet no cargó, la página sigue funcionando.
  const mapaEl = document.getElementById("mapa-jujuy");
  const datosEl = document.getElementById("mapa-datos");
  if (mapaEl && datosEl && window.L && !mapaEl.childElementCount) {
    let lugares = [];
    try {
      lugares = JSON.parse(datosEl.textContent) || [];
    } catch (err) {
      lugares = [];
    }

    const esc = (txt) => String(txt).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

    const mapa = L.map(mapaEl, { scrollWheelZoom: false, minZoom: 6 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 13,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>',
    }).addTo(mapa);

    const capas = {};
    const puntos = [];
    lugares.forEach((l) => {
      if (!capas[l.r]) capas[l.r] = L.layerGroup().addTo(mapa);
      const atractivo = l.t === "atractivo";
      L.circleMarker([l.lat, l.lon], {
        radius: atractivo ? 7 : 5,
        color: "#fffdf9",
        weight: 1.5,
        fillColor: l.c,
        fillOpacity: atractivo ? 0.8 : 1,
      })
        .bindTooltip(esc(l.n) + " · " + esc(l.d), { direction: "top" })
        .bindPopup(
          "<strong>" + esc(l.n) + "</strong><br>" +
          (atractivo ? "Atractivo natural" : "Localidad") + " del departamento " + esc(l.d)
        )
        .addTo(capas[l.r]);
      puntos.push([l.lat, l.lon]);
    });
    if (puntos.length) mapa.fitBounds(puntos, { padding: [24, 24] });

    // La rueda del mouse no secuestra el scroll de la página hasta que se hace click.
    mapaEl.addEventListener("click", () => mapa.scrollWheelZoom.enable());
    mapaEl.addEventListener("mouseleave", () => mapa.scrollWheelZoom.disable());

    document.querySelectorAll("#mapa-leyenda button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const visible = btn.getAttribute("aria-pressed") === "true";
        btn.setAttribute("aria-pressed", String(!visible));
        const capa = capas[btn.dataset.region];
        if (!capa) return;
        if (visible) mapa.removeLayer(capa);
        else mapa.addLayer(capa);
      });
    });
  }

  const cont = document.getElementById("checklist-items");
  if (cont) {
    try {
      const guardado = JSON.parse(localStorage.getItem("jujuy-kit") || "[]");
      guardado.forEach((i) => {
        const caja = cont.querySelector('input[data-i="' + i + '"]');
        if (caja) caja.checked = true;
      });
    } catch (err) {
      /* modo privado o datos viejos: se empieza limpio */
    }

    cont.addEventListener("change", () => {
      const marcados = Array.from(cont.querySelectorAll("input:checked")).map((c) => Number(c.dataset.i));
      try {
        localStorage.setItem("jujuy-kit", JSON.stringify(marcados));
      } catch (err) {
        /* modo privado */
      }
    });
  }
})();
