(function () {
    "use strict";

    const SELECTOR_ROOT = "#mc-form";
    const SELECTOR_LINEA = '[data-role="mc-linea"]';
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

    function leerMediosOperativos() {
        const script = document.querySelector("#mc-medios-operativos-data");

        if (!script) {
            return [];
        }

        try {
            return JSON.parse(script.textContent || "[]");
        } catch {
            return [];
        }
    }

    function obtenerMapaMedios() {
        const mapa = new Map();

        leerMediosOperativos().forEach((medio) => {
            mapa.set(String(medio.codigo || "").trim().toUpperCase(), medio);
        });

        return mapa;
    }

    let mapaMedios = new Map();

    function buscarMedioPorCodigo(codigo) {
        return mapaMedios.get(String(codigo || "").trim().toUpperCase()) || null;
    }

    function setValor(selector, valor) {
        const elemento = document.querySelector(selector);

        if (elemento) {
            elemento.value = valor || "";
        }
    }

    function actualizarInfoMedio(medio) {
        if (!medio) {
            setValor("#mc-info-cuenta", "");
            setValor("#mc-info-banco", "");
            setValor("#mc-info-plaza-sucursal", "");
            setValor("#mc-info-cuenta-cuit", "");
            return;
        }

        const cuenta = [
            medio.cuenta_contable_codigo,
            medio.cuenta_contable_descripcion,
        ].filter(Boolean).join(" - ");

        const plazaSucursal = [
            medio.plaza,
            medio.sucursal,
        ].filter(Boolean).join(" / ");

        const cuentaCuit = [
            medio.numero_cuenta,
            medio.cuit,
        ].filter(Boolean).join(" / ");

        setValor("#mc-info-cuenta", cuenta);
        setValor("#mc-info-banco", medio.banco_nombre || medio.banco_codigo || "");
        setValor("#mc-info-plaza-sucursal", plazaSucursal);
        setValor("#mc-info-cuenta-cuit", cuentaCuit);
    }

    function aplicarMedioAFila(fila, codigo) {
        const medio = buscarMedioPorCodigo(codigo);
        const codigoInput = fila.querySelector(".mc-medio-codigo");
        const select = fila.querySelector(".mc-medio-select");
        const tipoInput = fila.querySelector(".mc-medio-tipo");
        const monedaInput = fila.querySelector(".mc-medio-moneda");
        const cotizacionInput = fila.querySelector(".mc-linea-cotizacion");

        if (!medio) {
            if (tipoInput) {
                tipoInput.value = "";
            }
            if (monedaInput) {
                monedaInput.value = "";
            }
            if (cotizacionInput) {
                cotizacionInput.value = "";
                cotizacionInput.readOnly = true;
                cotizacionInput.placeholder = "-";
            }
            actualizarInfoMedio(null);
            return;
        }

        if (codigoInput) {
            codigoInput.value = medio.codigo;
        }

        if (select) {
            select.value = medio.codigo;
            select.dispatchEvent(new Event("change", { bubbles: true }));
        }

        if (tipoInput) {
            tipoInput.value = medio.tipo || "";
        }

        if (monedaInput) {
            monedaInput.value = medio.moneda_codigo || "";
        }

        if (cotizacionInput) {
            const requiereCotizacion = Number.parseInt(
                String(medio.requiere_cotizacion || "0"),
                10
            ) === 1;
            cotizacionInput.readOnly = !requiereCotizacion;
            cotizacionInput.placeholder = requiereCotizacion ? "0,000000" : "-";

            if (!requiereCotizacion) {
                cotizacionInput.value = "";
            }
        }

        actualizarInfoMedio(medio);
    }

    function obtenerTotalEsperadoCentavos() {
        const root = obtenerRoot();
        const desdeData = Number.parseInt(
            root ? root.dataset.totalEsperadoCentavos || "0" : "0",
            10
        );

        if (desdeData > 0) {
            return desdeData;
        }

        const input = document.querySelector("#mc-total-esperado");
        const desdeInput = input ? obtenerCentavosDesdeInput(input) : 0;

        return Number.isFinite(desdeInput) ? Math.max(desdeInput, 0) : 0;
    }

    function obtenerTotalLineasCentavos() {
        let total = 0;

        document.querySelectorAll(".mc-linea-importe").forEach((input) => {
            const importe = obtenerCentavosDesdeInput(input);

            if (Number.isFinite(importe) && importe > 0) {
                total += importe;
            }
        });

        return total;
    }

    function actualizarResumen() {
        const totalEsperado = obtenerTotalEsperadoCentavos();
        const totalLineas = obtenerTotalLineasCentavos();
        const diferencia = totalEsperado - totalLineas;
        const totalEsperadoInput = document.querySelector("#mc-res-total-esperado");
        const totalLineasInput = document.querySelector("#mc-res-total-lineas");
        const diferenciaInput = document.querySelector("#mc-res-diferencia");
        const confirmar = document.querySelector("#mc-confirmar-wip");
        const validacion = document.querySelector("#mc-validacion-resumen");

        if (totalEsperadoInput) {
            setearCentavosEnInput(totalEsperadoInput, totalEsperado);
        }

        if (totalLineasInput) {
            setearCentavosEnInput(totalLineasInput, totalLineas);
        }

        if (diferenciaInput) {
            setearCentavosEnInput(diferenciaInput, diferencia);
            diferenciaInput.classList.toggle("is-valid", diferencia === 0 && totalEsperado > 0);
            diferenciaInput.classList.toggle("is-invalid", diferencia !== 0 || totalEsperado <= 0);
        }

        if (confirmar) {
            confirmar.disabled = !(totalEsperado > 0 && diferencia === 0);
        }

        if (validacion) {
            validacion.classList.toggle("text-success", totalEsperado > 0 && diferencia === 0);
            validacion.classList.toggle("text-danger", diferencia !== 0 || totalEsperado <= 0);
            validacion.textContent = totalEsperado > 0 && diferencia === 0
                ? "Totales coincidentes. En una etapa posterior esto confirmara caja y asiento."
                : "El total de lineas debe coincidir con el total esperado.";
        }
    }

    function reindexarFila(fila, indice) {
        fila.dataset.rowIndex = String(indice);

        fila.querySelectorAll("input, select").forEach((campo) => {
            const nombre = campo.getAttribute("name");

            if (nombre) {
                campo.setAttribute("name", nombre.replace(/lineas\[\d+\]/, `lineas[${indice}]`));
            }
        });
    }

    function agregarLinea() {
        const tbody = document.querySelector("#mc-lineas-tbody");
        const primera = tbody ? tbody.querySelector(SELECTOR_LINEA) : null;

        if (!tbody || !primera) {
            return;
        }

        const nueva = primera.cloneNode(true);

        nueva.querySelectorAll("input").forEach((input) => {
            input.value = "";

            if (input.classList.contains("mc-linea-cotizacion")) {
                input.readOnly = true;
                input.placeholder = "-";
            }
        });

        nueva.querySelectorAll("select").forEach((select) => {
            select.selectedIndex = 0;
        });

        tbody.appendChild(nueva);
        Array.from(tbody.querySelectorAll(SELECTOR_LINEA)).forEach(reindexarFila);
        actualizarResumen();
    }

    function quitarLinea(boton) {
        const tbody = document.querySelector("#mc-lineas-tbody");
        const filas = tbody ? Array.from(tbody.querySelectorAll(SELECTOR_LINEA)) : [];

        if (filas.length <= 1) {
            filas.forEach((fila) => {
                fila.querySelectorAll("input").forEach((input) => {
                    input.value = "";
                });
                fila.querySelectorAll("select").forEach((select) => {
                    select.selectedIndex = 0;
                });
            });
            actualizarResumen();
            actualizarInfoMedio(null);
            return;
        }

        const fila = boton.closest(SELECTOR_LINEA);
        if (fila) {
            fila.remove();
        }

        Array.from(tbody.querySelectorAll(SELECTOR_LINEA)).forEach(reindexarFila);
        actualizarResumen();
    }

    function inicializarPrimerMedioDisponible() {
        const primeraFila = document.querySelector(SELECTOR_LINEA);
        const primerMedio = leerMediosOperativos()[0];

        if (!primeraFila || !primerMedio) {
            return;
        }

        aplicarMedioAFila(primeraFila, primerMedio.codigo);
    }

    function inicializarFormulario() {
        if (!obtenerRoot()) {
            return;
        }

        mapaMedios = obtenerMapaMedios();

        document.addEventListener("change", (evento) => {
            if (evento.target.matches(".mc-medio-select")) {
                aplicarMedioAFila(
                    evento.target.closest(SELECTOR_LINEA),
                    evento.target.value
                );
            }
        });

        document.addEventListener("blur", (evento) => {
            if (evento.target.matches(".mc-medio-codigo")) {
                aplicarMedioAFila(
                    evento.target.closest(SELECTOR_LINEA),
                    evento.target.value
                );
            }

            if (evento.target.matches(".mc-linea-importe")) {
                const importe = obtenerCentavosDesdeInput(evento.target);
                setearCentavosEnInput(
                    evento.target,
                    Number.isFinite(importe) && importe > 0 ? importe : 0
                );
                actualizarResumen();
            }
        }, true);

        document.addEventListener("input", (evento) => {
            if (evento.target.matches(".mc-linea-importe")) {
                if (!actualizacionProgramatica) {
                    actualizarResumen();
                }
            }
        });

        document.addEventListener("click", (evento) => {
            if (evento.target.matches(".mc-linea-quitar")) {
                quitarLinea(evento.target);
            }
        });

        const agregar = document.querySelector("#mc-agregar-linea");
        if (agregar) {
            agregar.addEventListener("click", agregarLinea);
        }

        const confirmar = document.querySelector("#mc-confirmar-wip");
        if (confirmar) {
            confirmar.addEventListener("click", () => {
                window.alert("WIP: movimiento de caja validado visualmente. Persistencia pendiente.");
            });
        }

        inicializarPrimerMedioDisponible();
        actualizarResumen();
    }

    document.addEventListener("DOMContentLoaded", inicializarFormulario);
}());
