(function () {
    "use strict";

    const CUENTAS_CONTABLES_SELECTOR_CUENTA_PARA_SUMARIZADORA =
        '[data-validation="cuentas-contables-formato-cuenta"]';

    const CUENTAS_CONTABLES_SELECTOR_SUMARIZADORA_DERIVADA =
        '[data-derived="cuentas-contables-sumarizadora-desde-cuenta"]';

    const CUENTAS_CONTABLES_REGEX_CUENTA_PARA_SUMARIZADORA =
        /^\d\.\d\.\d{2}\.\d{2}\.\d{3}$/;

    function calcularSumarizadoraDerivadaDesdeCuentaContable(cuentaContable) {
        const cuentaContableNormalizada = String(cuentaContable || "").trim();

        if (!CUENTAS_CONTABLES_REGEX_CUENTA_PARA_SUMARIZADORA.test(
            cuentaContableNormalizada
        )) {
            return "";
        }

        const partesCuentaContable = cuentaContableNormalizada.split(".");
        const claseCuentaContable = partesCuentaContable[0];
        const grupoCuentaContable = partesCuentaContable[1];
        const rubroCuentaContable = partesCuentaContable[2];
        const subrubroCuentaContable = partesCuentaContable[3];
        const cuentaAnaliticaContable = partesCuentaContable[4];

        if (cuentaAnaliticaContable !== "000") {
            return [
                claseCuentaContable,
                grupoCuentaContable,
                rubroCuentaContable,
                subrubroCuentaContable,
                "000",
            ].join(".");
        }

        if (subrubroCuentaContable !== "00") {
            return [
                claseCuentaContable,
                grupoCuentaContable,
                rubroCuentaContable,
                "00",
                "000",
            ].join(".");
        }

        if (rubroCuentaContable !== "00") {
            return [
                claseCuentaContable,
                grupoCuentaContable,
                "00",
                "00",
                "000",
            ].join(".");
        }

        if (grupoCuentaContable !== "0") {
            return [
                claseCuentaContable,
                "0",
                "00",
                "00",
                "000",
            ].join(".");
        }

        return "";
    }

    function dispararLookupDescripcionSumarizadoraCuentaContable(
        inputSumarizadoraCuentaContable
    ) {
        inputSumarizadoraCuentaContable.dispatchEvent(
            new Event("input", { bubbles: true })
        );
    }

    function aplicarSumarizadoraDerivadaDesdeCuentaContable(
        inputCuentaContable,
        inputSumarizadoraCuentaContable
    ) {
        const sumarizadoraDerivadaCuentaContable =
            calcularSumarizadoraDerivadaDesdeCuentaContable(
                inputCuentaContable.value
            );

        if (inputSumarizadoraCuentaContable.value === sumarizadoraDerivadaCuentaContable) {
            return;
        }

        inputSumarizadoraCuentaContable.value = sumarizadoraDerivadaCuentaContable;
        dispararLookupDescripcionSumarizadoraCuentaContable(
            inputSumarizadoraCuentaContable
        );
    }

    function inicializarSugerenciaSumarizadoraDesdeCuentaContable() {
        const inputCuentaContable = document.querySelector(
            CUENTAS_CONTABLES_SELECTOR_CUENTA_PARA_SUMARIZADORA
        );

        const inputSumarizadoraCuentaContable = document.querySelector(
            CUENTAS_CONTABLES_SELECTOR_SUMARIZADORA_DERIVADA
        );

        if (!inputCuentaContable || !inputSumarizadoraCuentaContable) {
            return;
        }

        inputCuentaContable.addEventListener("input", () => {
            aplicarSumarizadoraDerivadaDesdeCuentaContable(
                inputCuentaContable,
                inputSumarizadoraCuentaContable
            );
        });

        inputCuentaContable.addEventListener("blur", () => {
            aplicarSumarizadoraDerivadaDesdeCuentaContable(
                inputCuentaContable,
                inputSumarizadoraCuentaContable
            );
        });

        aplicarSumarizadoraDerivadaDesdeCuentaContable(
            inputCuentaContable,
            inputSumarizadoraCuentaContable
        );
    }

    document.addEventListener(
        "DOMContentLoaded",
        inicializarSugerenciaSumarizadoraDesdeCuentaContable
    );
})();
