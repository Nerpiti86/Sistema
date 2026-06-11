(function () {
    "use strict";

    const ASIENTOS_SELECTOR_LOOKUP_CUENTAS =
        '[data-lookup="asientos-cuentas-imputables"]';

    const ASIENTOS_SELECTOR_RENGLONES = "#as-det-renglones";
    const ASIENTOS_SELECTOR_RENGLON = '[data-role="asiento-renglon"]';
    const ASIENTOS_SELECTOR_AGREGAR_RENGLON =
        '[data-action="agregar-renglon"]';
    const ASIENTOS_SELECTOR_QUITAR_RENGLON =
        '[data-action="quitar-renglon"]';
    const ASIENTOS_SELECTOR_CANTIDAD_RENGLONES =
        '[data-role="asiento-renglones-cantidad"]';
    const ASIENTOS_SELECTOR_TOTAL_DEBE =
        '[data-role="asiento-total-debe"]';
    const ASIENTOS_SELECTOR_TOTAL_HABER =
        '[data-role="asiento-total-haber"]';
    const ASIENTOS_SELECTOR_DIFERENCIA =
        '[data-role="asiento-diferencia"]';
    const ASIENTOS_SELECTOR_MONEDA_RENGLON =
        '[data-role="asiento-moneda-renglon"]';
    const ASIENTOS_SELECTOR_MONEDA_BADGE =
        '[data-role="asiento-moneda-badge"]';
    const ASIENTOS_SELECTOR_INPUT_DEBE_NOMINAL =
        'input[data-field="nominal_debe_centavos"]';
    const ASIENTOS_SELECTOR_INPUT_HABER_NOMINAL =
        'input[data-field="nominal_haber_centavos"]';
    const ASIENTOS_SELECTOR_INPUT_DEBE_ARS =
        'input[data-field="debe_ars_centavos"]';
    const ASIENTOS_SELECTOR_INPUT_HABER_ARS =
        'input[data-field="haber_ars_centavos"]';
    const ASIENTOS_SELECTOR_INPUT_COTIZACION_RENGLON =
        'input[data-field="cotizacion_1000000"]';
    const ASIENTOS_SELECTOR_IMPORTE_NOMINAL =
        'input[data-field="nominal_debe_centavos"], input[data-field="nominal_haber_centavos"], input[data-field="cotizacion_1000000"]';
    const ASIENTOS_SELECTOR_INPUT_BORRAR_FOCUS_RENGLON =
        ASIENTOS_SELECTOR_IMPORTE_NOMINAL;
    const ASIENTOS_SELECTOR_GUARDAR_BORRADOR =
        "#as-guardar";

    const ASIENTOS_MENSAJE_LOOKUP_CUENTA_ERROR =
        "No se pudo buscar la cuenta contable.";
    const ASIENTOS_MENSAJE_ASIENTO_DESBALANCEADO =
        "El asiento debe balancear para guardar.";
    const ASIENTOS_MONEDA_CONTABLE = "ARS";
    const ASIENTOS_MONEDA_BADGE_CLASES = [
        "ns-moneda-badge--ars",
        "ns-moneda-badge--usd",
        "ns-moneda-badge--eur",
        "ns-moneda-badge--default",
    ];
    const ASIENTOS_COTIZACION_ESCALA = 1000000;
    const ASIENTOS_MENSAJE_COTIZACION_INVALIDA = "Revisar cotizacion";

    const ASIENTOS_MINIMO_CARACTERES_LOOKUP_CUENTA = 2;
    const ASIENTOS_MINIMO_RENGLONES = 2;

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

    const buscarCuentasConDebounce = crearDebounceLookupCuenta(
        buscarCuentasImputablesParaAsiento,
        250
    );

    function obtenerRenglonesAsiento() {
        const contenedorRenglones = document.querySelector(
            ASIENTOS_SELECTOR_RENGLONES
        );

        if (!contenedorRenglones) {
            return [];
        }

        return Array.from(
            contenedorRenglones.querySelectorAll(ASIENTOS_SELECTOR_RENGLON)
        );
    }

    function reemplazarIndiceRenglon(valor, indiceRenglon) {
        if (!valor) {
            return valor;
        }

        return String(valor)
            .replace(/as-det-\d+-/g, `as-det-${indiceRenglon}-`)
            .replace(/detalles\[\d+\]/g, `detalles[${indiceRenglon}]`)
            .replace(/renglon \d+/gi, `renglon ${indiceRenglon + 1}`);
    }

    function reindexarAtributo(elemento, atributo, indiceRenglon) {
        const valorActual = elemento.getAttribute(atributo);

        if (!valorActual) {
            return;
        }

        const valorNuevo = reemplazarIndiceRenglon(
            valorActual,
            indiceRenglon
        );

        if (valorNuevo !== valorActual) {
            elemento.setAttribute(atributo, valorNuevo);
        }
    }

    function reindexarRenglonAsiento(renglonAsiento, indiceRenglon) {
        renglonAsiento.dataset.rowIndex = String(indiceRenglon);

        reindexarAtributo(renglonAsiento, "id", indiceRenglon);

        const elementosReindexables = renglonAsiento.querySelectorAll(
            "[id], [name], [list], [data-lookup-result], [data-row-index], [aria-label]"
        );

        elementosReindexables.forEach((elemento) => {
            reindexarAtributo(elemento, "id", indiceRenglon);
            reindexarAtributo(elemento, "name", indiceRenglon);
            reindexarAtributo(elemento, "list", indiceRenglon);
            reindexarAtributo(elemento, "data-lookup-result", indiceRenglon);
            reindexarAtributo(elemento, "aria-label", indiceRenglon);
            elemento.dataset.rowIndex = String(indiceRenglon);
        });
    }

    function limpiarValorCampoNuevoRenglon(campoRenglon) {
        const campo = campoRenglon.dataset.field || "";

        if (
            campo === "cuenta_contable_codigo" ||
            campo === "cuenta_contable_descripcion" ||
            campo === "descripcion" ||
            campo === "nominal_debe_centavos" ||
            campo === "nominal_haber_centavos" ||
            campo === "debe_ars_centavos" ||
            campo === "haber_ars_centavos"
        ) {
            campoRenglon.value = "";
        }

        if (campo === "moneda_codigo") {
            campoRenglon.value = "ARS";
        }

        if (campo === "cotizacion_1000000") {
            campoRenglon.value = "1,000000";
        }

        campoRenglon.classList.remove("is-valid", "is-invalid");
        campoRenglon.setCustomValidity("");
    }

    function limpiarRenglonClonado(renglonAsiento) {
        const camposRenglon = renglonAsiento.querySelectorAll("input, select");
        const datalistsRenglon = renglonAsiento.querySelectorAll("datalist");

        camposRenglon.forEach((campoRenglon) => {
            limpiarValorCampoNuevoRenglon(campoRenglon);
        });

        datalistsRenglon.forEach((datalistRenglon) => {
            datalistRenglon.innerHTML = "";
        });

        sincronizarBadgeMonedaRenglon(renglonAsiento);
    }


    function normalizarImporteArgentinoACentavos(valor) {
        const valorNormalizado = String(valor || "")
            .trim()
            .replace(/\./g, "")
            .replace(",", ".");

        if (!valorNormalizado) {
            return 0;
        }

        const valorDecimal = Number.parseFloat(valorNormalizado);

        if (!Number.isFinite(valorDecimal)) {
            return 0;
        }

        return Math.round(valorDecimal * 100);
    }

    function formatearCentavosArgentino(importeCentavos) {
        const signo = importeCentavos < 0 ? "-" : "";
        const importeAbsoluto = Math.abs(importeCentavos);
        const parteEntera = Math.trunc(importeAbsoluto / 100);
        const parteDecimal = String(importeAbsoluto % 100).padStart(2, "0");
        const parteEnteraFormateada = String(parteEntera).replace(
            /\B(?=(\d{3})+(?!\d))/g,
            "."
        );

        return `${signo}${parteEnteraFormateada},${parteDecimal}`;
    }

    function obtenerImporteRenglonAsiento(renglonAsiento, selectorImporte) {
        const inputImporte = renglonAsiento.querySelector(selectorImporte);

        if (!inputImporte) {
            return 0;
        }

        return normalizarImporteArgentinoACentavos(inputImporte.value);
    }

    function sumarImportesRenglones(selectorImporte) {
        return obtenerRenglonesAsiento().reduce(
            (totalImporte, renglonAsiento) => totalImporte + obtenerImporteRenglonAsiento(
                renglonAsiento,
                selectorImporte
            ),
            0
        );
    }

    function asignarValorCalculado(inputImporteCalculado, valorCalculado) {
        if (!inputImporteCalculado) {
            return;
        }

        inputImporteCalculado.value = valorCalculado;
    }

    function asignarImporteCalculado(inputImporteCalculado, importeCentavos) {
        asignarValorCalculado(
            inputImporteCalculado,
            formatearCentavosArgentino(importeCentavos)
        );
    }

    function obtenerInputCotizacionRenglon(renglonAsiento) {
        return renglonAsiento.querySelector(
            ASIENTOS_SELECTOR_INPUT_COTIZACION_RENGLON
        );
    }

    function obtenerCotizacionRenglonAsiento(renglonAsiento) {
        const inputCotizacion = obtenerInputCotizacionRenglon(renglonAsiento);
        const numeroArgentino = window.NeriSoftNumeroArgentino || {};

        if (
            !inputCotizacion ||
            typeof numeroArgentino.cotizacionArA1000000 !== "function"
        ) {
            return null;
        }

        return numeroArgentino.cotizacionArA1000000(inputCotizacion.value);
    }

    function calcularEquivalenteArsCentavos(
        nominalCentavos,
        cotizacion1000000
    ) {
        if (nominalCentavos === 0) {
            return 0;
        }

        return Math.round(
            (nominalCentavos * cotizacion1000000) / ASIENTOS_COTIZACION_ESCALA
        );
    }

    function obtenerMonedaRenglonAsiento(renglonAsiento) {
        const inputMoneda = renglonAsiento.querySelector(
            ASIENTOS_SELECTOR_MONEDA_RENGLON
        );

        return String(
            inputMoneda ? inputMoneda.value : ASIENTOS_MONEDA_CONTABLE
        ).trim().toUpperCase();
    }

    function obtenerBadgeMonedaRenglon(renglonAsiento) {
        return renglonAsiento.querySelector(
            ASIENTOS_SELECTOR_MONEDA_BADGE
        );
    }

    function obtenerClaseBadgeMoneda(monedaRenglon) {
        const monedaNormalizada = String(monedaRenglon || "")
            .trim()
            .toLowerCase();

        if (monedaNormalizada === "ars") {
            return "ns-moneda-badge--ars";
        }

        if (monedaNormalizada === "usd") {
            return "ns-moneda-badge--usd";
        }

        if (monedaNormalizada === "eur") {
            return "ns-moneda-badge--eur";
        }

        return "ns-moneda-badge--default";
    }

    function sincronizarBadgeMonedaRenglon(renglonAsiento) {
        const badgeMoneda = obtenerBadgeMonedaRenglon(renglonAsiento);

        if (!badgeMoneda) {
            return;
        }

        const monedaRenglon = obtenerMonedaRenglonAsiento(renglonAsiento);
        const numeroRenglon = (
            Number.parseInt(renglonAsiento.dataset.rowIndex || "0", 10) + 1
        );

        badgeMoneda.textContent = monedaRenglon;
        badgeMoneda.dataset.value = monedaRenglon;
        ASIENTOS_MONEDA_BADGE_CLASES.forEach((claseBadge) => {
            badgeMoneda.classList.remove(claseBadge);
        });
        badgeMoneda.classList.remove(
            "text-bg-light",
            "text-bg-secondary",
            "border-secondary"
        );
        badgeMoneda.classList.add(obtenerClaseBadgeMoneda(monedaRenglon));
        badgeMoneda.setAttribute(
            "aria-label",
            `Moneda ${monedaRenglon} del renglon ${numeroRenglon}. Click para cambiar moneda`
        );
        badgeMoneda.setAttribute("title", `Moneda ${monedaRenglon}`);
    }

    function ciclarMonedaRenglon(badgeMoneda) {
        const renglonAsiento = badgeMoneda.closest(ASIENTOS_SELECTOR_RENGLON);

        if (!renglonAsiento) {
            return;
        }

        const inputMoneda = renglonAsiento.querySelector(
            ASIENTOS_SELECTOR_MONEDA_RENGLON
        );

        if (!inputMoneda || inputMoneda.options.length === 0) {
            return;
        }

        const cantidadOpciones = inputMoneda.options.length;
        const indiceActual = inputMoneda.selectedIndex < 0
            ? cantidadOpciones - 1
            : inputMoneda.selectedIndex;

        inputMoneda.selectedIndex = (indiceActual + 1) % cantidadOpciones;

        sincronizarBadgeMonedaRenglon(renglonAsiento);
        inputMoneda.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function manejarFocusinInputBorrableRenglon(evento) {
        if (!(evento.target instanceof Element)) {
            return;
        }

        const inputRenglon = evento.target.closest(
            ASIENTOS_SELECTOR_INPUT_BORRAR_FOCUS_RENGLON
        );

        if (!inputRenglon || inputRenglon.readOnly || inputRenglon.disabled) {
            return;
        }

        if (inputRenglon.value === "") {
            return;
        }

        inputRenglon.value = "";
        inputRenglon.dispatchEvent(new Event("input", { bubbles: true }));
        inputRenglon.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function aplicarCotizacionInvalida(renglonAsiento) {
        const inputCotizacion = obtenerInputCotizacionRenglon(renglonAsiento);

        renglonAsiento.dataset.cotizacionValida = "0";

        asignarValorCalculado(
            renglonAsiento.querySelector(ASIENTOS_SELECTOR_INPUT_DEBE_ARS),
            ""
        );
        asignarValorCalculado(
            renglonAsiento.querySelector(ASIENTOS_SELECTOR_INPUT_HABER_ARS),
            ""
        );

        if (inputCotizacion) {
            inputCotizacion.classList.add("is-invalid");
            inputCotizacion.classList.remove("is-valid");
        }
    }

    function aplicarCotizacionValida(renglonAsiento, cotizacion1000000) {
        const inputCotizacion = obtenerInputCotizacionRenglon(renglonAsiento);

        renglonAsiento.dataset.cotizacionValida = "1";

        if (inputCotizacion) {
            inputCotizacion.classList.remove("is-invalid");
            inputCotizacion.classList.add("is-valid");
            inputCotizacion.dataset.cotizacion1000000 = String(cotizacion1000000);
        }
    }

    function actualizarImportesArsRenglon(renglonAsiento) {
        const monedaRenglon = obtenerMonedaRenglonAsiento(renglonAsiento);
        const inputCotizacion = obtenerInputCotizacionRenglon(renglonAsiento);
        const debeNominalCentavos = obtenerImporteRenglonAsiento(
            renglonAsiento,
            ASIENTOS_SELECTOR_INPUT_DEBE_NOMINAL
        );
        const haberNominalCentavos = obtenerImporteRenglonAsiento(
            renglonAsiento,
            ASIENTOS_SELECTOR_INPUT_HABER_NOMINAL
        );

        let cotizacion1000000 = obtenerCotizacionRenglonAsiento(renglonAsiento);

        if (monedaRenglon === ASIENTOS_MONEDA_CONTABLE) {
            cotizacion1000000 = ASIENTOS_COTIZACION_ESCALA;

            if (inputCotizacion) {
                inputCotizacion.value = "1,000000";
                inputCotizacion.readOnly = true;
            }
        } else if (inputCotizacion) {
            inputCotizacion.readOnly = false;
        }

        sincronizarBadgeMonedaRenglon(renglonAsiento);

        if (!cotizacion1000000 || cotizacion1000000 <= 0) {
            aplicarCotizacionInvalida(renglonAsiento);
            return;
        }

        aplicarCotizacionValida(renglonAsiento, cotizacion1000000);

        asignarImporteCalculado(
            renglonAsiento.querySelector(ASIENTOS_SELECTOR_INPUT_DEBE_ARS),
            calcularEquivalenteArsCentavos(debeNominalCentavos, cotizacion1000000)
        );
        asignarImporteCalculado(
            renglonAsiento.querySelector(ASIENTOS_SELECTOR_INPUT_HABER_ARS),
            calcularEquivalenteArsCentavos(haberNominalCentavos, cotizacion1000000)
        );
    }

    function actualizarImportesArsRenglones() {
        obtenerRenglonesAsiento().forEach(actualizarImportesArsRenglon);
    }

    function existeCotizacionInvalida() {
        return obtenerRenglonesAsiento().some(
            (renglonAsiento) => renglonAsiento.dataset.cotizacionValida === "0"
        );
    }

    function actualizarClaseDiferencia(elementoDiferencia, diferenciaCentavos) {
        elementoDiferencia.classList.toggle("text-success", diferenciaCentavos === 0);
        elementoDiferencia.classList.toggle("text-danger", diferenciaCentavos !== 0);
    }

    function obtenerBotonGuardarBorrador() {
        return document.querySelector(ASIENTOS_SELECTOR_GUARDAR_BORRADOR);
    }

    function inicializarEstadoOriginalBotonGuardarBorrador(botonGuardarBorrador) {
        if (!botonGuardarBorrador || botonGuardarBorrador.dataset.disabledOriginal) {
            return;
        }

        botonGuardarBorrador.dataset.disabledOriginal = botonGuardarBorrador.disabled
            ? "true"
            : "false";
    }

    function actualizarEstadoBotonGuardarBorrador(diferenciaCentavos) {
        const botonGuardarBorrador = obtenerBotonGuardarBorrador();

        if (!botonGuardarBorrador) {
            return;
        }

        inicializarEstadoOriginalBotonGuardarBorrador(botonGuardarBorrador);

        if (botonGuardarBorrador.dataset.disabledOriginal === "true") {
            botonGuardarBorrador.disabled = true;
            return;
        }

        const debeBloquearGuardar = diferenciaCentavos !== 0;

        botonGuardarBorrador.disabled = debeBloquearGuardar;
        botonGuardarBorrador.classList.toggle("disabled", debeBloquearGuardar);

        if (debeBloquearGuardar) {
            botonGuardarBorrador.title = ASIENTOS_MENSAJE_ASIENTO_DESBALANCEADO;
            botonGuardarBorrador.setAttribute("aria-disabled", "true");
            return;
        }

        botonGuardarBorrador.removeAttribute("title");
        botonGuardarBorrador.removeAttribute("aria-disabled");
    }

    function actualizarTotalesAsiento() {
        const totalDebe = document.querySelector(ASIENTOS_SELECTOR_TOTAL_DEBE);
        const totalHaber = document.querySelector(ASIENTOS_SELECTOR_TOTAL_HABER);
        const diferencia = document.querySelector(ASIENTOS_SELECTOR_DIFERENCIA);

        if (!totalDebe || !totalHaber || !diferencia) {
            return;
        }

        actualizarImportesArsRenglones();

        if (existeCotizacionInvalida()) {
            totalDebe.textContent = ASIENTOS_MENSAJE_COTIZACION_INVALIDA;
            totalHaber.textContent = ASIENTOS_MENSAJE_COTIZACION_INVALIDA;
            diferencia.textContent = ASIENTOS_MENSAJE_COTIZACION_INVALIDA;
            diferencia.classList.remove("text-success", "text-danger");
            actualizarEstadoBotonGuardarBorrador(1);
            return;
        }

        const totalDebeCentavos = sumarImportesRenglones(
            ASIENTOS_SELECTOR_INPUT_DEBE_ARS
        );
        const totalHaberCentavos = sumarImportesRenglones(
            ASIENTOS_SELECTOR_INPUT_HABER_ARS
        );
        const diferenciaCentavos = totalDebeCentavos - totalHaberCentavos;

        totalDebe.textContent = formatearCentavosArgentino(totalDebeCentavos);
        totalHaber.textContent = formatearCentavosArgentino(totalHaberCentavos);
        diferencia.textContent = formatearCentavosArgentino(diferenciaCentavos);

        actualizarClaseDiferencia(diferencia, diferenciaCentavos);
        actualizarEstadoBotonGuardarBorrador(diferenciaCentavos);
    }

    function actualizarCantidadRenglonesAsiento() {
        const contadorRenglones = document.querySelector(
            ASIENTOS_SELECTOR_CANTIDAD_RENGLONES
        );

        if (!contadorRenglones) {
            return;
        }

        contadorRenglones.textContent = String(obtenerRenglonesAsiento().length);
    }

    function actualizarEstadoBotonesQuitarRenglon() {
        const renglonesAsiento = obtenerRenglonesAsiento();
        const debeBloquearQuitar =
            renglonesAsiento.length <= ASIENTOS_MINIMO_RENGLONES;

        renglonesAsiento.forEach((renglonAsiento) => {
            const botonQuitar = renglonAsiento.querySelector(
                ASIENTOS_SELECTOR_QUITAR_RENGLON
            );

            if (botonQuitar) {
                botonQuitar.disabled = debeBloquearQuitar;
                botonQuitar.classList.toggle(
                    "disabled",
                    debeBloquearQuitar
                );
            }
        });
    }

    function reindexarRenglonesAsiento() {
        obtenerRenglonesAsiento().forEach((renglonAsiento, indiceRenglon) => {
            reindexarRenglonAsiento(renglonAsiento, indiceRenglon);
        });

        actualizarEstadoBotonesQuitarRenglon();
        actualizarCantidadRenglonesAsiento();
        actualizarTotalesAsiento();
    }

    function agregarRenglonAsiento() {
        const contenedorRenglones = document.querySelector(
            ASIENTOS_SELECTOR_RENGLONES
        );
        const renglonesAsiento = obtenerRenglonesAsiento();
        const ultimoRenglon = renglonesAsiento[renglonesAsiento.length - 1];

        if (!contenedorRenglones || !ultimoRenglon) {
            return;
        }

        const nuevoRenglon = ultimoRenglon.cloneNode(true);

        limpiarRenglonClonado(nuevoRenglon);
        contenedorRenglones.appendChild(nuevoRenglon);
        reindexarRenglonesAsiento();
    }

    function quitarRenglonAsiento(botonQuitar) {
        const renglonesAsiento = obtenerRenglonesAsiento();

        if (renglonesAsiento.length <= ASIENTOS_MINIMO_RENGLONES) {
            actualizarEstadoBotonesQuitarRenglon();
            return;
        }

        const renglonAsiento = botonQuitar.closest(ASIENTOS_SELECTOR_RENGLON);

        if (!renglonAsiento) {
            return;
        }

        renglonAsiento.remove();
        reindexarRenglonesAsiento();
    }

    function inicializarEventosLookupCuenta() {
        const contenedorRenglones = document.querySelector(
            ASIENTOS_SELECTOR_RENGLONES
        );

        if (!contenedorRenglones) {
            return;
        }

        contenedorRenglones.addEventListener(
            "focusin",
            manejarFocusinInputBorrableRenglon
        );

        contenedorRenglones.addEventListener("input", (evento) => {
            const inputCuentaContable = evento.target.closest(
                ASIENTOS_SELECTOR_LOOKUP_CUENTAS
            );

            if (inputCuentaContable) {
                buscarCuentasConDebounce(inputCuentaContable);
            }

            const inputImporteNominal = evento.target.closest(
                ASIENTOS_SELECTOR_IMPORTE_NOMINAL
            );

            if (inputImporteNominal) {
                actualizarTotalesAsiento();
            }
        });

        contenedorRenglones.addEventListener("change", (evento) => {
            const inputMonedaRenglon = evento.target.closest(
                ASIENTOS_SELECTOR_MONEDA_RENGLON
            );

            if (inputMonedaRenglon) {
                actualizarTotalesAsiento();
            }

            const inputCuentaContable = evento.target.closest(
                ASIENTOS_SELECTOR_LOOKUP_CUENTAS
            );

            if (inputCuentaContable) {
                buscarCuentasImputablesParaAsiento(inputCuentaContable);
            }
        });

        contenedorRenglones.addEventListener("blur", (evento) => {
            const inputCuentaContable = evento.target.closest(
                ASIENTOS_SELECTOR_LOOKUP_CUENTAS
            );

            if (inputCuentaContable) {
                buscarCuentasImputablesParaAsiento(inputCuentaContable);
            }
        }, true);
    }

    function inicializarEventosRenglonesDinamicos() {
        const botonAgregar = document.querySelector(
            ASIENTOS_SELECTOR_AGREGAR_RENGLON
        );

        if (botonAgregar) {
            botonAgregar.addEventListener("click", agregarRenglonAsiento);
        }

        document.addEventListener("click", (evento) => {
            const botonMoneda = evento.target.closest(
                ASIENTOS_SELECTOR_MONEDA_BADGE
            );

            if (botonMoneda) {
                ciclarMonedaRenglon(botonMoneda);
                return;
            }

            const botonQuitar = evento.target.closest(
                ASIENTOS_SELECTOR_QUITAR_RENGLON
            );

            if (botonQuitar) {
                quitarRenglonAsiento(botonQuitar);
            }
        });
    }

    function inicializarLookupCuentasImputablesAsiento() {
        inicializarEventosLookupCuenta();
        inicializarEventosRenglonesDinamicos();
        reindexarRenglonesAsiento();
    }

    document.addEventListener(
        "DOMContentLoaded",
        inicializarLookupCuentasImputablesAsiento
    );
})();
