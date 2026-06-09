(function () {
    "use strict";

    const CUENTAS_CONTABLES_SELECTOR_LOOKUP_SUMARIZADORA =
        '[data-lookup="cuentas-contables-descripcion-sumarizadora"]';

    const CUENTAS_CONTABLES_SELECTOR_RESULTADO_LOOKUP_SUMARIZADORA =
        '[data-lookup-result="cuentas-contables-descripcion-sumarizadora"]';

    const CUENTAS_CONTABLES_TOKEN_URL_LOOKUP_SUMARIZADORA =
        "__CUENTA_CONTABLE__";

    const CUENTAS_CONTABLES_REGEX_FORMATO_SUMARIZADORA =
        /^\d\.\d\.\d{2}\.\d{2}\.\d{3}$/;

    const CUENTAS_CONTABLES_MENSAJE_SUMARIZADORA_FORMATO_INVALIDO =
        "La sumarizadora debe respetar el formato 9.9.99.99.999.";

    const CUENTAS_CONTABLES_MENSAJE_SUMARIZADORA_NO_ENCONTRADA =
        "Cuenta sumarizadora no encontrada.";

    const CUENTAS_CONTABLES_MENSAJE_SUMARIZADORA_ERROR_LOOKUP =
        "No se pudo buscar la cuenta sumarizadora.";

    function obtenerResultadoLookupSumarizadoraCuentaContable() {
        return document.querySelector(
            CUENTAS_CONTABLES_SELECTOR_RESULTADO_LOOKUP_SUMARIZADORA
        );
    }

    function obtenerUrlLookupSumarizadoraCuentaContable(
        inputSumarizadoraCuentaContable,
        cuentaSumarizadora
    ) {
        const urlBaseLookupSumarizadora =
            inputSumarizadoraCuentaContable.dataset.lookupUrl || "";

        return urlBaseLookupSumarizadora.replace(
            CUENTAS_CONTABLES_TOKEN_URL_LOOKUP_SUMARIZADORA,
            encodeURIComponent(cuentaSumarizadora)
        );
    }

    function limpiarLookupSumarizadoraCuentaContable(
        inputSumarizadoraCuentaContable,
        resultadoLookupSumarizadoraCuentaContable
    ) {
        if (resultadoLookupSumarizadoraCuentaContable) {
            resultadoLookupSumarizadoraCuentaContable.value = "";
        }

        inputSumarizadoraCuentaContable.classList.remove(
            "is-valid",
            "is-invalid"
        );
        inputSumarizadoraCuentaContable.setCustomValidity("");
    }

    function aplicarErrorLookupSumarizadoraCuentaContable(
        inputSumarizadoraCuentaContable,
        resultadoLookupSumarizadoraCuentaContable,
        mensajeErrorLookupSumarizadora
    ) {
        if (resultadoLookupSumarizadoraCuentaContable) {
            resultadoLookupSumarizadoraCuentaContable.value =
                mensajeErrorLookupSumarizadora;
        }

        inputSumarizadoraCuentaContable.classList.remove("is-valid");
        inputSumarizadoraCuentaContable.classList.add("is-invalid");
        inputSumarizadoraCuentaContable.setCustomValidity(
            mensajeErrorLookupSumarizadora
        );
    }

    function aplicarResultadoLookupSumarizadoraCuentaContable(
        inputSumarizadoraCuentaContable,
        resultadoLookupSumarizadoraCuentaContable,
        descripcionSumarizadoraCuentaContable
    ) {
        if (resultadoLookupSumarizadoraCuentaContable) {
            resultadoLookupSumarizadoraCuentaContable.value =
                descripcionSumarizadoraCuentaContable || "";
        }

        inputSumarizadoraCuentaContable.classList.remove("is-invalid");
        inputSumarizadoraCuentaContable.classList.add("is-valid");
        inputSumarizadoraCuentaContable.setCustomValidity("");
    }

    async function buscarDescripcionSumarizadoraCuentaContable(
        inputSumarizadoraCuentaContable
    ) {
        const resultadoLookupSumarizadoraCuentaContable =
            obtenerResultadoLookupSumarizadoraCuentaContable();

        const cuentaSumarizadora = String(
            inputSumarizadoraCuentaContable.value || ""
        ).trim();

        if (cuentaSumarizadora === "") {
            limpiarLookupSumarizadoraCuentaContable(
                inputSumarizadoraCuentaContable,
                resultadoLookupSumarizadoraCuentaContable
            );
            return;
        }

        if (!CUENTAS_CONTABLES_REGEX_FORMATO_SUMARIZADORA.test(cuentaSumarizadora)) {
            aplicarErrorLookupSumarizadoraCuentaContable(
                inputSumarizadoraCuentaContable,
                resultadoLookupSumarizadoraCuentaContable,
                CUENTAS_CONTABLES_MENSAJE_SUMARIZADORA_FORMATO_INVALIDO
            );
            return;
        }

        const urlLookupSumarizadora = obtenerUrlLookupSumarizadoraCuentaContable(
            inputSumarizadoraCuentaContable,
            cuentaSumarizadora
        );

        try {
            const respuestaLookupSumarizadora = await fetch(urlLookupSumarizadora, {
                headers: {
                    Accept: "application/json",
                },
            });

            if (!respuestaLookupSumarizadora.ok) {
                aplicarErrorLookupSumarizadoraCuentaContable(
                    inputSumarizadoraCuentaContable,
                    resultadoLookupSumarizadoraCuentaContable,
                    CUENTAS_CONTABLES_MENSAJE_SUMARIZADORA_NO_ENCONTRADA
                );
                return;
            }

            const datosLookupSumarizadora =
                await respuestaLookupSumarizadora.json();

            aplicarResultadoLookupSumarizadoraCuentaContable(
                inputSumarizadoraCuentaContable,
                resultadoLookupSumarizadoraCuentaContable,
                datosLookupSumarizadora.descripcion
            );
        } catch (error) {
            aplicarErrorLookupSumarizadoraCuentaContable(
                inputSumarizadoraCuentaContable,
                resultadoLookupSumarizadoraCuentaContable,
                CUENTAS_CONTABLES_MENSAJE_SUMARIZADORA_ERROR_LOOKUP
            );
        }
    }

    function inicializarLookupDescripcionSumarizadoraCuentaContable() {
        const inputsLookupSumarizadora = document.querySelectorAll(
            CUENTAS_CONTABLES_SELECTOR_LOOKUP_SUMARIZADORA
        );

        inputsLookupSumarizadora.forEach((inputSumarizadoraCuentaContable) => {
            inputSumarizadoraCuentaContable.addEventListener("input", () => {
                buscarDescripcionSumarizadoraCuentaContable(
                    inputSumarizadoraCuentaContable
                );
            });

            inputSumarizadoraCuentaContable.addEventListener("blur", () => {
                buscarDescripcionSumarizadoraCuentaContable(
                    inputSumarizadoraCuentaContable
                );
            });

            buscarDescripcionSumarizadoraCuentaContable(
                inputSumarizadoraCuentaContable
            );
        });
    }

    document.addEventListener(
        "DOMContentLoaded",
        inicializarLookupDescripcionSumarizadoraCuentaContable
    );
})();
