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
