(function () {
    "use strict";

    const SELECTOR_ROOT = "#cl-cobro";
    const SELECTOR_CHECK_COMPROBANTE = ".cl-cobro-comprobante-check";
    const SELECTOR_IMPORTE_COMPROBANTE = ".cl-cobro-importe";
    const ESCALA_CENTAVOS = 100;

    let actualizacionProgramatica = false;

    function obtenerRoot() {
        return document.querySelector(SELECTOR_ROOT);
    }

    function obtenerApiNumeroArgentino() {
        return window.NeriSoftNumeroArgentino || {};
    }

    function obtenerCentavosDesdeInput(input) {
        const apiNumero = obtenerApiNumeroArgentino();

        if (typeof apiNumero.decimalArAEnteroEscala !== "function") {
            return NaN;
        }

        return apiNumero.decimalArAEnteroEscala(input.value, ESCALA_CENTAVOS);
    }

    function setearCentavosEnInput(input, centavos) {
        const importe = Number.parseInt(String(centavos || "0"), 10) || 0;
        const signo = importe < 0 ? "-" : "";
        const absoluto = Math.abs(importe);
        const enteros = Math.floor(absoluto / ESCALA_CENTAVOS);
        const decimales = String(absoluto % ESCALA_CENTAVOS).padStart(2, "0");

        actualizacionProgramatica = true;
        input.value = `${signo}${enteros},${decimales}`;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
        actualizacionProgramatica = false;
    }

    function obtenerFilaComprobanteDesdeInput(input) {
        return input.closest("tr[data-saldo-centavos]");
    }

    function obtenerSaldoFila(fila) {
        return Number.parseInt(fila.dataset.saldoCentavos || "0", 10) || 0;
    }

    function obtenerImporteComprobante(input, normalizar) {
        const fila = obtenerFilaComprobanteDesdeInput(input);

        if (!fila) {
            return 0;
        }

        const saldo = obtenerSaldoFila(fila);
        let importe = obtenerCentavosDesdeInput(input);

        if (!Number.isFinite(importe) || importe < 0) {
            importe = 0;
        }

        if (importe > saldo) {
            importe = saldo;
        }

        if (normalizar) {
            setearCentavosEnInput(input, importe);
        }

        return importe;
    }

    function obtenerTotalCobroCentavos(normalizar) {
        let total = 0;

        document.querySelectorAll(SELECTOR_CHECK_COMPROBANTE).forEach((check) => {
            if (!check.checked) {
                return;
            }

            const fila = check.closest("tr[data-saldo-centavos]");
            const input = fila ? fila.querySelector(SELECTOR_IMPORTE_COMPROBANTE) : null;

            if (!input) {
                return;
            }

            total += obtenerImporteComprobante(input, Boolean(normalizar));
        });

        return total;
    }

    function actualizarResumenCobro(normalizar) {
        const form = document.querySelector("#cl-cobro-formulario");
        const totalInput = document.querySelector("#cl-cobro-total");
        const continuar = document.querySelector("#cl-cobro-continuar-caja");
        const total = obtenerTotalCobroCentavos(Boolean(normalizar));

        if (form) {
            form.dataset.totalCobroCentavos = String(total);
        }

        if (totalInput) {
            setearCentavosEnInput(totalInput, total);
        }

        if (continuar) {
            continuar.disabled = total <= 0;
        }
    }

    function manejarCambioSeleccionComprobante(check) {
        const fila = check.closest("tr[data-saldo-centavos]");
        const input = fila ? fila.querySelector(SELECTOR_IMPORTE_COMPROBANTE) : null;

        if (!input) {
            return;
        }

        input.disabled = !check.checked;

        if (check.checked && !input.value.trim()) {
            setearCentavosEnInput(input, obtenerSaldoFila(fila));
        }

        if (!check.checked) {
            input.value = "";
        }

        actualizarResumenCobro(true);
    }

    function inicializarFormularioCobro() {
        if (!obtenerRoot()) {
            return;
        }

        document.querySelectorAll(SELECTOR_CHECK_COMPROBANTE).forEach((check) => {
            check.addEventListener("change", () => manejarCambioSeleccionComprobante(check));
        });

        document.querySelectorAll(SELECTOR_IMPORTE_COMPROBANTE).forEach((input) => {
            input.addEventListener("blur", () => {
                obtenerImporteComprobante(input, true);
                actualizarResumenCobro(false);
            });

            input.addEventListener("input", () => {
                if (actualizacionProgramatica) {
                    return;
                }

                actualizarResumenCobro(false);
            });
        });

        const botonContinuar = document.querySelector("#cl-cobro-continuar-caja");
        if (botonContinuar) {
            botonContinuar.addEventListener("click", () => {
                actualizarResumenCobro(true);

                const form = document.querySelector("#cl-cobro-formulario");
                const urlBase = form ? form.dataset.urlMovimientoCaja : "";
                const totalCobro = Number.parseInt(
                    form ? form.dataset.totalCobroCentavos || "0" : "0",
                    10
                ) || 0;

                if (!urlBase || totalCobro <= 0) {
                    return;
                }

                const url = new URL(urlBase, window.location.origin);
                const clienteId = document.querySelector("#cl-cobro-cliente-id");

                url.searchParams.set("tipo_movimiento", "INGRESO");
                url.searchParams.set("origen_tipo", "RECIBO_CLIENTE_WIP");
                url.searchParams.set("origen_descripcion", "Recibo cliente WIP");
                url.searchParams.set("total_esperado_centavos", String(totalCobro));

                if (clienteId && clienteId.value) {
                    url.searchParams.set("cliente_id", clienteId.value);
                }

                window.location.href = url.toString();
            });
        }

        actualizarResumenCobro(false);
    }

    document.addEventListener("DOMContentLoaded", inicializarFormularioCobro);
}());
