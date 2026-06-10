(function () {
    "use strict";

    const CUENTAS_CONTABLES_SELECTOR_DISPONIBILIDAD =
        '[data-disponibilidad="cuentas-contables-cuenta-disponible"]';

    const CUENTAS_CONTABLES_TOKEN_URL_DISPONIBILIDAD = "__CUENTA_CONTABLE__";

    const CUENTAS_CONTABLES_REGEX_FORMATO_CUENTA_DISPONIBILIDAD =
        /^\d\.\d\.\d{2}\.\d{2}\.\d{3}$/;

    const CUENTAS_CONTABLES_MENSAJE_FORMATO_CUENTA_INVALIDO =
        "La cuenta debe respetar el formato 9.9.99.99.999.";

    const CUENTAS_CONTABLES_MENSAJE_CUENTA_OCUPADA =
        "La cuenta contable ya está ocupada.";

    const CUENTAS_CONTABLES_MENSAJE_ERROR_DISPONIBILIDAD =
        "No se pudo validar si la cuenta contable está disponible.";

    let secuenciaValidacionDisponibilidadCuentaContable = 0;
    const timersDisponibilidadCuentaContable = new WeakMap();

    function obtenerFeedbackCuentaContable(inputCuentaContable) {
        const idsDescriptivos = String(
            inputCuentaContable.getAttribute("aria-describedby") || ""
        ).split(/\s+/);

        const idFeedback = idsDescriptivos.find((idDescriptivo) =>
            idDescriptivo.endsWith("-error")
        );

        if (!idFeedback) {
            return null;
        }

        return document.getElementById(idFeedback);
    }

    function restaurarMensajeFormatoCuentaContable(inputCuentaContable) {
        const feedbackCuentaContable =
            obtenerFeedbackCuentaContable(inputCuentaContable);

        if (feedbackCuentaContable) {
            feedbackCuentaContable.textContent =
                CUENTAS_CONTABLES_MENSAJE_FORMATO_CUENTA_INVALIDO;
        }
    }

    function obtenerUrlDisponibilidadCuentaContable(
        inputCuentaContable,
        cuentaContable
    ) {
        const urlBaseDisponibilidad =
            inputCuentaContable.dataset.disponibilidadUrl || "";

        return urlBaseDisponibilidad.replace(
            CUENTAS_CONTABLES_TOKEN_URL_DISPONIBILIDAD,
            encodeURIComponent(cuentaContable)
        );
    }

    function limpiarDisponibilidadCuentaContable(inputCuentaContable) {
        restaurarMensajeFormatoCuentaContable(inputCuentaContable);
    }

    function aplicarCuentaContableDisponible(inputCuentaContable) {
        restaurarMensajeFormatoCuentaContable(inputCuentaContable);
        inputCuentaContable.classList.remove("is-invalid");
        inputCuentaContable.classList.add("is-valid");
        inputCuentaContable.setCustomValidity("");
    }

    function aplicarCuentaContableOcupada(inputCuentaContable, descripcionCuenta) {
        const feedbackCuentaContable =
            obtenerFeedbackCuentaContable(inputCuentaContable);

        const mensajeCuentaOcupada = descripcionCuenta
            ? `${CUENTAS_CONTABLES_MENSAJE_CUENTA_OCUPADA} ${descripcionCuenta}.`
            : CUENTAS_CONTABLES_MENSAJE_CUENTA_OCUPADA;

        if (feedbackCuentaContable) {
            feedbackCuentaContable.textContent = mensajeCuentaOcupada;
        }

        inputCuentaContable.classList.remove("is-valid");
        inputCuentaContable.classList.add("is-invalid");
        inputCuentaContable.setCustomValidity(mensajeCuentaOcupada);
    }

    function aplicarErrorDisponibilidadCuentaContable(inputCuentaContable) {
        const feedbackCuentaContable =
            obtenerFeedbackCuentaContable(inputCuentaContable);

        if (feedbackCuentaContable) {
            feedbackCuentaContable.textContent =
                CUENTAS_CONTABLES_MENSAJE_ERROR_DISPONIBILIDAD;
        }

        inputCuentaContable.classList.remove("is-valid");
        inputCuentaContable.classList.add("is-invalid");
        inputCuentaContable.setCustomValidity(
            CUENTAS_CONTABLES_MENSAJE_ERROR_DISPONIBILIDAD
        );
    }

    async function validarDisponibilidadCuentaContable(inputCuentaContable) {
        if (inputCuentaContable.readOnly || inputCuentaContable.disabled) {
            return;
        }

        const cuentaContable = String(inputCuentaContable.value || "").trim();

        if (
            cuentaContable === "" ||
            !CUENTAS_CONTABLES_REGEX_FORMATO_CUENTA_DISPONIBILIDAD.test(
                cuentaContable
            )
        ) {
            limpiarDisponibilidadCuentaContable(inputCuentaContable);
            return;
        }

        const secuenciaActual = String(
            ++secuenciaValidacionDisponibilidadCuentaContable
        );

        inputCuentaContable.dataset.disponibilidadSecuencia = secuenciaActual;

        try {
            const respuestaDisponibilidad = await fetch(
                obtenerUrlDisponibilidadCuentaContable(
                    inputCuentaContable,
                    cuentaContable
                ),
                {
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (
                inputCuentaContable.dataset.disponibilidadSecuencia !==
                secuenciaActual
            ) {
                return;
            }

            if (!respuestaDisponibilidad.ok) {
                aplicarErrorDisponibilidadCuentaContable(inputCuentaContable);
                return;
            }

            const datosDisponibilidad = await respuestaDisponibilidad.json();

            if (datosDisponibilidad.ocupada || !datosDisponibilidad.disponible) {
                aplicarCuentaContableOcupada(
                    inputCuentaContable,
                    datosDisponibilidad.descripcion
                );
                return;
            }

            aplicarCuentaContableDisponible(inputCuentaContable);
        } catch (error) {
            if (
                inputCuentaContable.dataset.disponibilidadSecuencia ===
                secuenciaActual
            ) {
                aplicarErrorDisponibilidadCuentaContable(inputCuentaContable);
            }
        }
    }

    function programarValidacionDisponibilidadCuentaContable(inputCuentaContable) {
        const timerAnterior =
            timersDisponibilidadCuentaContable.get(inputCuentaContable);

        if (timerAnterior) {
            window.clearTimeout(timerAnterior);
        }

        const timerNuevo = window.setTimeout(() => {
            validarDisponibilidadCuentaContable(inputCuentaContable);
        }, 300);

        timersDisponibilidadCuentaContable.set(inputCuentaContable, timerNuevo);
    }

    function inicializarDisponibilidadCuentaContable() {
        const inputsCuentaContable = document.querySelectorAll(
            CUENTAS_CONTABLES_SELECTOR_DISPONIBILIDAD
        );

        inputsCuentaContable.forEach((inputCuentaContable) => {
            inputCuentaContable.addEventListener("input", () => {
                programarValidacionDisponibilidadCuentaContable(
                    inputCuentaContable
                );
            });

            inputCuentaContable.addEventListener("blur", () => {
                validarDisponibilidadCuentaContable(inputCuentaContable);
            });

            validarDisponibilidadCuentaContable(inputCuentaContable);
        });
    }

    document.addEventListener(
        "DOMContentLoaded",
        inicializarDisponibilidadCuentaContable
    );
})();
