(function () {
    "use strict";

    function formatearFechaHoraMensaje() {
        const ahora = new Date();

        try {
            return new Intl.DateTimeFormat("es-AR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false
            }).format(ahora);
        } catch (error) {
            const dia = String(ahora.getDate()).padStart(2, "0");
            const mes = String(ahora.getMonth() + 1).padStart(2, "0");
            const anio = ahora.getFullYear();
            const hora = String(ahora.getHours()).padStart(2, "0");
            const minutos = String(ahora.getMinutes()).padStart(2, "0");

            return `${dia}/${mes}/${anio} ${hora}:${minutos}`;
        }
    }

    function completarFechasDeAlerts() {
        document.querySelectorAll("[data-ns-alert-created-at]").forEach((elemento) => {
            if (!elemento.textContent.trim()) {
                elemento.textContent = formatearFechaHoraMensaje();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", completarFechasDeAlerts);
        return;
    }

    completarFechasDeAlerts();
}());
