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
