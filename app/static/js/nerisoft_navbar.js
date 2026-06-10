(function () {
    "use strict";

    function cerrarSubmenusHermanos(submenuActual) {
        const padre = submenuActual.parentElement;

        if (!padre) {
            return;
        }

        padre.querySelectorAll(":scope > .dropdown-submenu.show").forEach((submenu) => {
            if (submenu !== submenuActual) {
                submenu.classList.remove("show");

                const toggle = submenu.querySelector(":scope > .dropdown-toggle");
                if (toggle) {
                    toggle.setAttribute("aria-expanded", "false");
                }
            }
        });
    }

    function inicializarNavbarGlobal() {
        document.querySelectorAll(".ns-dropdown-submenu > .dropdown-toggle").forEach((toggle) => {
            toggle.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();

                const submenu = toggle.closest(".ns-dropdown-submenu");

                if (!submenu) {
                    return;
                }

                cerrarSubmenusHermanos(submenu);

                const estaAbierto = submenu.classList.toggle("show");
                toggle.setAttribute("aria-expanded", estaAbierto ? "true" : "false");
            });
        });

        document.addEventListener("click", () => {
            document.querySelectorAll(".ns-dropdown-submenu.show").forEach((submenu) => {
                submenu.classList.remove("show");

                const toggle = submenu.querySelector(":scope > .dropdown-toggle");
                if (toggle) {
                    toggle.setAttribute("aria-expanded", "false");
                }
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializarNavbarGlobal);
        return;
    }

    inicializarNavbarGlobal();
}());
