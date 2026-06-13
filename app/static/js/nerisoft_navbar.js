(function () {
    "use strict";

    function cerrarDropdownsAbiertos(navbar) {
        if (!window.bootstrap || !window.bootstrap.Dropdown) {
            return;
        }

        navbar.querySelectorAll(".dropdown-toggle.show").forEach((toggle) => {
            const instancia = window.bootstrap.Dropdown.getInstance(toggle);

            if (instancia) {
                instancia.hide();
            }
        });
    }

    function inicializarNavbarGlobal() {
        const navbar = document.getElementById("ns-navbar");

        if (!navbar) {
            return;
        }

        document.addEventListener("keydown", (event) => {
            if (event.key !== "Escape") {
                return;
            }

            cerrarDropdownsAbiertos(navbar);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializarNavbarGlobal);
        return;
    }

    inicializarNavbarGlobal();
}());
