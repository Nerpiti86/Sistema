(function () {
    "use strict";

    const ASIENTOS_SELECTOR_LOOKUP_CUENTAS =
        '[data-lookup="asientos-cuentas-imputables"]';

    const ASIENTOS_MENSAJE_LOOKUP_CUENTA_ERROR =
        "No se pudo buscar la cuenta contable.";

    const ASIENTOS_MINIMO_CARACTERES_LOOKUP_CUENTA = 2;

    function obtenerDatalistLookupCuenta(inputCuentaContable) {
        const datalistId = inputCuentaContable.getAttribute("list");

        if (!datalistId) {
            return null;
        }

        return document.getElementById(datalistId);
    }

    function obtenerInputNombreCuenta(inputCuentaContable) {
        const resultadoId = inputCuentaContable.dataset.lookupResult || "";

        if (!resultadoId) {
            return null;
        }

        return document.getElementById(resultadoId);
    }

    function limpiarResultadoLookupCuenta(inputCuentaContable) {
        const inputNombreCuenta = obtenerInputNombreCuenta(inputCuentaContable);
        const datalistLookup = obtenerDatalistLookupCuenta(inputCuentaContable);

        if (inputNombreCuenta) {
            inputNombreCuenta.value = "";
            inputNombreCuenta.dataset.cuenta = "";
        }

        if (datalistLookup) {
            datalistLookup.innerHTML = "";
        }

        inputCuentaContable.classList.remove("is-valid", "is-invalid");
        inputCuentaContable.setCustomValidity("");
    }

    function obtenerUrlLookupCuenta(inputCuentaContable, terminoBusqueda) {
        const urlLookup = new URL(
            inputCuentaContable.dataset.lookupUrl,
            window.location.origin
        );

        urlLookup.searchParams.set("q", terminoBusqueda);
        urlLookup.searchParams.set(
            "limite",
            inputCuentaContable.dataset.lookupLimite || "10"
        );

        return urlLookup.toString();
    }

    function renderizarOpcionesLookupCuenta(inputCuentaContable, resultados) {
        const datalistLookup = obtenerDatalistLookupCuenta(inputCuentaContable);

        if (!datalistLookup) {
            return;
        }

        datalistLookup.innerHTML = "";

        resultados.forEach((cuentaContable) => {
            const opcionCuenta = document.createElement("option");
            opcionCuenta.value = cuentaContable.cuenta;
            opcionCuenta.label = cuentaContable.descripcion;
            opcionCuenta.dataset.descripcion = cuentaContable.descripcion;
            datalistLookup.appendChild(opcionCuenta);
        });
    }

    function aplicarCuentaSeleccionada(inputCuentaContable, resultados) {
        const inputNombreCuenta = obtenerInputNombreCuenta(inputCuentaContable);
        const cuentaIngresada = String(inputCuentaContable.value || "").trim();

        const cuentaSeleccionada = resultados.find(
            (cuentaContable) => cuentaContable.cuenta === cuentaIngresada
        );

        if (!inputNombreCuenta) {
            return;
        }

        if (!cuentaSeleccionada) {
            inputNombreCuenta.value = "";
            inputNombreCuenta.dataset.cuenta = "";
            inputCuentaContable.classList.remove("is-valid");
            return;
        }

        inputNombreCuenta.value = cuentaSeleccionada.descripcion;
        inputNombreCuenta.dataset.cuenta = cuentaSeleccionada.cuenta;
        inputCuentaContable.classList.remove("is-invalid");
        inputCuentaContable.classList.add("is-valid");
        inputCuentaContable.setCustomValidity("");
    }

    function aplicarErrorLookupCuenta(inputCuentaContable, mensajeError) {
        const inputNombreCuenta = obtenerInputNombreCuenta(inputCuentaContable);

        if (inputNombreCuenta) {
            inputNombreCuenta.value = mensajeError;
            inputNombreCuenta.dataset.cuenta = "";
        }

        inputCuentaContable.classList.remove("is-valid");
        inputCuentaContable.classList.add("is-invalid");
        inputCuentaContable.setCustomValidity(mensajeError);
    }

    async function buscarCuentasImputablesParaAsiento(inputCuentaContable) {
        const terminoBusqueda = String(inputCuentaContable.value || "").trim();

        if (
            terminoBusqueda.length <
            ASIENTOS_MINIMO_CARACTERES_LOOKUP_CUENTA
        ) {
            limpiarResultadoLookupCuenta(inputCuentaContable);
            return;
        }

        try {
            const respuestaLookupCuenta = await fetch(
                obtenerUrlLookupCuenta(inputCuentaContable, terminoBusqueda),
                {
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (!respuestaLookupCuenta.ok) {
                aplicarErrorLookupCuenta(
                    inputCuentaContable,
                    ASIENTOS_MENSAJE_LOOKUP_CUENTA_ERROR
                );
                return;
            }

            const datosLookupCuenta = await respuestaLookupCuenta.json();
            const resultados = datosLookupCuenta.resultados || [];

            renderizarOpcionesLookupCuenta(inputCuentaContable, resultados);
            aplicarCuentaSeleccionada(inputCuentaContable, resultados);
        } catch (error) {
            aplicarErrorLookupCuenta(
                inputCuentaContable,
                ASIENTOS_MENSAJE_LOOKUP_CUENTA_ERROR
            );
        }
    }

    function crearDebounceLookupCuenta(funcionLookup, demoraMilisegundos) {
        let timeoutLookupCuenta = null;

        return function ejecutarLookupCuenta(inputCuentaContable) {
            window.clearTimeout(timeoutLookupCuenta);
            timeoutLookupCuenta = window.setTimeout(() => {
                funcionLookup(inputCuentaContable);
            }, demoraMilisegundos);
        };
    }

    function inicializarLookupCuentasImputablesAsiento() {
        const inputsCuentaContable = document.querySelectorAll(
            ASIENTOS_SELECTOR_LOOKUP_CUENTAS
        );

        const buscarCuentasConDebounce = crearDebounceLookupCuenta(
            buscarCuentasImputablesParaAsiento,
            250
        );

        inputsCuentaContable.forEach((inputCuentaContable) => {
            inputCuentaContable.addEventListener("input", () => {
                buscarCuentasConDebounce(inputCuentaContable);
            });

            inputCuentaContable.addEventListener("change", () => {
                buscarCuentasImputablesParaAsiento(inputCuentaContable);
            });

            inputCuentaContable.addEventListener("blur", () => {
                buscarCuentasImputablesParaAsiento(inputCuentaContable);
            });
        });
    }

    document.addEventListener(
        "DOMContentLoaded",
        inicializarLookupCuentasImputablesAsiento
    );
})();
