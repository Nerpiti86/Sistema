(function () {
    "use strict";

    const CUENTAS_CONTABLES_SELECTOR_VALIDACION_CUENTA =
        '[data-validation="cuentas-contables-formato-cuenta"]';

    const CUENTAS_CONTABLES_REGEX_FORMATO_CUENTA =
        /^\d\.\d\.\d{2}\.\d{2}\.\d{3}$/;

    const CUENTAS_CONTABLES_MENSAJE_FORMATO_CUENTA_INVALIDO =
        "La cuenta debe respetar el formato 9.9.99.99.999.";

    function validarFormatoCuentaContableAlVuelo(valorCuentaContable) {
        const cuentaContableNormalizada = String(valorCuentaContable || "").trim();

        if (cuentaContableNormalizada === "") {
            return {
                campoVacio: true,
                formatoValido: true,
                mensajeError: "",
            };
        }

        const formatoValido = CUENTAS_CONTABLES_REGEX_FORMATO_CUENTA.test(
            cuentaContableNormalizada
        );

        return {
            campoVacio: false,
            formatoValido,
            mensajeError: formatoValido
                ? ""
                : CUENTAS_CONTABLES_MENSAJE_FORMATO_CUENTA_INVALIDO,
        };
    }

    function aplicarEstadoVisualValidacionCuentaContable(
        inputCuentaContable,
        resultadoValidacionCuentaContable
    ) {
        if (resultadoValidacionCuentaContable.campoVacio) {
            inputCuentaContable.classList.remove("is-valid", "is-invalid");
            inputCuentaContable.setCustomValidity("");
            return;
        }

        if (resultadoValidacionCuentaContable.formatoValido) {
            inputCuentaContable.classList.remove("is-invalid");
            inputCuentaContable.classList.add("is-valid");
            inputCuentaContable.setCustomValidity("");
            return;
        }

        inputCuentaContable.classList.remove("is-valid");
        inputCuentaContable.classList.add("is-invalid");
        inputCuentaContable.setCustomValidity(
            resultadoValidacionCuentaContable.mensajeError
        );
    }

    function ejecutarValidacionAlVueloCuentaContable(inputCuentaContable) {
        const resultadoValidacionCuentaContable =
            validarFormatoCuentaContableAlVuelo(inputCuentaContable.value);

        aplicarEstadoVisualValidacionCuentaContable(
            inputCuentaContable,
            resultadoValidacionCuentaContable
        );
    }

    function inicializarValidacionAlVueloCuentaContable() {
        const inputsCuentaContable = document.querySelectorAll(
            CUENTAS_CONTABLES_SELECTOR_VALIDACION_CUENTA
        );

        inputsCuentaContable.forEach((inputCuentaContable) => {
            inputCuentaContable.addEventListener("input", () => {
                ejecutarValidacionAlVueloCuentaContable(inputCuentaContable);
            });

            inputCuentaContable.addEventListener("blur", () => {
                ejecutarValidacionAlVueloCuentaContable(inputCuentaContable);
            });

            ejecutarValidacionAlVueloCuentaContable(inputCuentaContable);
        });
    }

    document.addEventListener(
        "DOMContentLoaded",
        inicializarValidacionAlVueloCuentaContable
    );
})();
