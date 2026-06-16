(() => {
    "use strict";

    const ESCALA_CANTIDAD = 100;
    const ESCALA_PORCENTAJE = 10000;
    const ESCALA_PORCENTAJE_CALCULO = 100 * ESCALA_PORCENTAJE;
    const TIPO_BONIFICACION_PORCENTAJE = "1";
    const TIPO_BONIFICACION_MONTO = "2";
    const TIPOS_COMPROBANTE_MODIFICADORES = new Set([
        "012",
        "013",
        "NOTA_DEBITO",
        "NOTA_CREDITO",
    ]);
    const TIPOS_COMPROBANTE_NOTA_DEBITO = new Set(["012", "NOTA_DEBITO"]);
    const TIPOS_COMPROBANTE_NOTA_CREDITO = new Set(["013", "NOTA_CREDITO"]);

    const SELECTORES = {
        formulario: "#vc-formulario",
        cantidad: "#vc-cantidad",
        precioUnitario: "#vc-precio-unitario",
        tipoBonificacion: "#vc-tipo-bonificacion",
        valorBonificacion: "#vc-bonificacion-valor",
        subtotalLinea: "#vc-subtotal-linea",
        totalComprobante: "#vc-total-comprobante",
        badgesCiclicos: '[data-role="vc-badge-ciclico"]',
        lookupArticulos: '[data-lookup="ventas-articulos-activos"]',
    };

    const CLASES_BADGE_RENGLON = [
        "vc-renglon-badge--unidad",
        "vc-renglon-badge--sin",
        "vc-renglon-badge--porcentaje",
        "vc-renglon-badge--monto",
    ];

    const obtenerNumeroArgentino = () => window.NeriSoftNumeroArgentino || {};

    const obtenerDatalistLookup = (inputLookup) => {
        const datalistId = inputLookup.getAttribute("list");

        if (!datalistId) {
            return null;
        }

        return document.getElementById(datalistId);
    };

    const obtenerHiddenLookup = (inputLookup) => (
        document.getElementById(inputLookup.dataset.lookupHidden || "")
    );

    const obtenerOpcionesLookupArticulos = (inputLookup) => {
        const datalist = obtenerDatalistLookup(inputLookup);

        if (!datalist) {
            return [];
        }

        return Array.from(datalist.options);
    };

    const parsearDecimal = (valor, escala) => {
        const numeroArgentino = obtenerNumeroArgentino();

        if (typeof numeroArgentino.decimalArAEnteroEscala !== "function") {
            return null;
        }

        return numeroArgentino.decimalArAEnteroEscala(valor, escala);
    };

    const formatearCentavos = (centavos) => {
        if (!Number.isFinite(centavos) || centavos < 0) {
            return "";
        }

        const valor = Math.round(centavos);
        const parteEntera = Math.trunc(valor / 100);
        const parteDecimal = String(valor % 100).padStart(2, "0");
        const enteroFormateado = String(parteEntera).replace(
            /\B(?=(\d{3})+(?!\d))/g,
            "."
        );

        return `${enteroFormateado},${parteDecimal}`;
    };

    const calcularBonificacionCentavos = (subtotalCentavos) => {
        const tipoBonificacion = document.querySelector(SELECTORES.tipoBonificacion);
        const valorBonificacion = document.querySelector(SELECTORES.valorBonificacion);

        if (!tipoBonificacion || !valorBonificacion || !tipoBonificacion.value) {
            return 0;
        }

        if (tipoBonificacion.value === TIPO_BONIFICACION_PORCENTAJE) {
            const porcentaje10000 = parsearDecimal(valorBonificacion.value, ESCALA_PORCENTAJE);

            if (porcentaje10000 === null || porcentaje10000 < 0) {
                return null;
            }

            return Math.round(
                (subtotalCentavos * porcentaje10000) / ESCALA_PORCENTAJE_CALCULO
            );
        }

        if (tipoBonificacion.value === TIPO_BONIFICACION_MONTO) {
            const montoCentavos = parsearDecimal(valorBonificacion.value, 100);

            if (montoCentavos === null || montoCentavos < 0) {
                return null;
            }

            return montoCentavos;
        }

        return 0;
    };

    const obtenerOpcionSeleccionada = (select) => {
        if (!select || select.selectedIndex < 0) {
            return null;
        }

        return select.options[select.selectedIndex] || null;
    };

    const obtenerTextoBadge = (opcion) => {
        if (!opcion) {
            return "";
        }

        return opcion.dataset.badge || opcion.textContent.trim();
    };

    const obtenerClaseBadge = (badge, valor) => {
        if (badge.dataset.badgeKind === "unidad") {
            return "vc-renglon-badge--unidad";
        }

        if (valor === TIPO_BONIFICACION_PORCENTAJE) {
            return "vc-renglon-badge--porcentaje";
        }

        if (valor === TIPO_BONIFICACION_MONTO) {
            return "vc-renglon-badge--monto";
        }

        return "vc-renglon-badge--sin";
    };

    const sincronizarBadge = (badge) => {
        const select = document.getElementById(badge.dataset.targetSelect || "");
        const opcion = obtenerOpcionSeleccionada(select);
        const valor = select ? select.value : "";
        const texto = obtenerTextoBadge(opcion) || "Sin";
        const titulo = opcion ? opcion.textContent.trim() : texto;

        badge.textContent = texto;
        badge.dataset.value = valor;
        CLASES_BADGE_RENGLON.forEach((clase) => badge.classList.remove(clase));
        badge.classList.add(obtenerClaseBadge(badge, valor));
        badge.setAttribute("title", titulo);
        badge.setAttribute("aria-label", `${titulo}. Click para cambiar`);
    };

    const ciclarBadge = (badge) => {
        const select = document.getElementById(badge.dataset.targetSelect || "");

        if (!select || select.options.length === 0) {
            return;
        }

        const cantidadOpciones = select.options.length;
        const indiceActual = select.selectedIndex < 0
            ? cantidadOpciones - 1
            : select.selectedIndex;

        select.selectedIndex = (indiceActual + 1) % cantidadOpciones;
        sincronizarBadge(badge);
        select.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const limpiarOpcionesLookupArticulos = (datalist) => {
        if (datalist) {
            datalist.innerHTML = "";
        }
    };

    const actualizarPrecioSugeridoArticulo = (opcion) => {
        const precioUnitario = document.querySelector(SELECTORES.precioUnitario);
        const precioSugerido = Number.parseInt(
            opcion.dataset.precioUnitarioSugeridoCentavos || "0",
            10
        );

        if (
            !precioUnitario ||
            precioUnitario.value.trim() ||
            !Number.isFinite(precioSugerido) ||
            precioSugerido <= 0
        ) {
            return;
        }

        precioUnitario.value = formatearCentavos(precioSugerido);
    };

    const seleccionarOpcionArticulo = (inputLookup, opcion, completarTexto = false) => {
        const hiddenArticulo = obtenerHiddenLookup(inputLookup);

        if (!hiddenArticulo || !opcion) {
            return false;
        }

        hiddenArticulo.value = opcion.dataset.valor || "";

        if (completarTexto && opcion.value) {
            inputLookup.value = opcion.value;
        }

        inputLookup.setCustomValidity("");
        actualizarPrecioSugeridoArticulo(opcion);
        return Boolean(hiddenArticulo.value);
    };

    const sincronizarArticuloSeleccionado = (inputLookup) => {
        const hiddenArticulo = obtenerHiddenLookup(inputLookup);
        const opciones = obtenerOpcionesLookupArticulos(inputLookup);
        const valorVisible = inputLookup.value.trim();

        if (!hiddenArticulo) {
            return false;
        }

        const opcionSeleccionada = opciones.find(
            (opcion) => opcion.value === valorVisible
        );

        if (!opcionSeleccionada) {
            hiddenArticulo.value = "";
            return false;
        }

        return seleccionarOpcionArticulo(inputLookup, opcionSeleccionada);
    };

    const seleccionarArticuloUnicoSiCorresponde = (
        inputLookup,
        completarTexto = false
    ) => {
        const opciones = obtenerOpcionesLookupArticulos(inputLookup);
        const termino = inputLookup.value.trim().toLocaleLowerCase();

        if (opciones.length !== 1 || termino.length < 2) {
            return false;
        }

        const opcion = opciones[0];
        const etiqueta = opcion.value.trim().toLocaleLowerCase();

        if (!etiqueta.includes(termino)) {
            return false;
        }

        return seleccionarOpcionArticulo(inputLookup, opcion, completarTexto);
    };

    const cargarOpcionesLookupArticulos = async (inputLookup) => {
        const datalist = obtenerDatalistLookup(inputLookup);
        const termino = inputLookup.value.trim();
        const url = inputLookup.dataset.lookupUrl || "";
        const limite = inputLookup.dataset.lookupLimite || "10";

        inputLookup.setCustomValidity("");
        sincronizarArticuloSeleccionado(inputLookup);

        if (!datalist || !url || termino.length < 2) {
            limpiarOpcionesLookupArticulos(datalist);
            return;
        }

        const parametros = new URLSearchParams({ q: termino, limite });
        const respuesta = await fetch(`${url}?${parametros.toString()}`, {
            headers: { Accept: "application/json" },
        });

        if (!respuesta.ok) {
            limpiarOpcionesLookupArticulos(datalist);
            return;
        }

        const datos = await respuesta.json();
        limpiarOpcionesLookupArticulos(datalist);

        (datos.resultados || []).forEach((articulo) => {
            const opcion = document.createElement("option");
            opcion.value = articulo.label;
            opcion.dataset.valor = articulo.valor;
            opcion.dataset.precioUnitarioSugeridoCentavos = String(
                articulo.precio_unitario_sugerido_centavos || 0
            );
            datalist.appendChild(opcion);
        });

        if (!sincronizarArticuloSeleccionado(inputLookup)) {
            seleccionarArticuloUnicoSiCorresponde(inputLookup);
        }

        actualizarSubtotalLinea();
    };

    const resolverArticuloPorLookupAntesDeEnviar = async (inputLookup) => {
        const datalist = obtenerDatalistLookup(inputLookup);
        const termino = inputLookup.value.trim();
        const url = inputLookup.dataset.lookupUrl || "";
        const limite = inputLookup.dataset.lookupLimite || "10";

        if (!datalist || !url || termino.length < 2) {
            return false;
        }

        const parametros = new URLSearchParams({ q: termino, limite });
        const respuesta = await fetch(`${url}?${parametros.toString()}`, {
            headers: { Accept: "application/json" },
        });

        if (!respuesta.ok) {
            return false;
        }

        const datos = await respuesta.json();
        limpiarOpcionesLookupArticulos(datalist);

        (datos.resultados || []).forEach((articulo) => {
            const opcion = document.createElement("option");
            opcion.value = articulo.label;
            opcion.dataset.valor = articulo.valor;
            opcion.dataset.precioUnitarioSugeridoCentavos = String(
                articulo.precio_unitario_sugerido_centavos || 0
            );
            datalist.appendChild(opcion);
        });

        return sincronizarArticuloSeleccionado(inputLookup) ||
            seleccionarArticuloUnicoSiCorresponde(inputLookup, true);
    };


    const actualizarSubtotalLinea = () => {
        const cantidad = document.querySelector(SELECTORES.cantidad);
        const precioUnitario = document.querySelector(SELECTORES.precioUnitario);
        const subtotalLinea = document.querySelector(SELECTORES.subtotalLinea);
        const totalComprobante = document.querySelector(SELECTORES.totalComprobante);

        if (!cantidad || !precioUnitario || !subtotalLinea) {
            return;
        }

        const cantidad100 = parsearDecimal(cantidad.value, ESCALA_CANTIDAD);
        const precioCentavos = parsearDecimal(precioUnitario.value, 100);

        if (
            cantidad100 === null ||
            precioCentavos === null ||
            cantidad100 <= 0 ||
            precioCentavos < 0
        ) {
            subtotalLinea.value = "";
            if (totalComprobante) {
                totalComprobante.value = "";
            }
            return;
        }

        const brutoCentavos = Math.round(
            (precioCentavos * cantidad100) / ESCALA_CANTIDAD
        );
        const bonificacionCentavos = calcularBonificacionCentavos(brutoCentavos);

        if (bonificacionCentavos === null || bonificacionCentavos > brutoCentavos) {
            subtotalLinea.value = "";
            if (totalComprobante) {
                totalComprobante.value = "";
            }
            return;
        }

        const totalLinea = formatearCentavos(brutoCentavos - bonificacionCentavos);
        subtotalLinea.value = totalLinea;
        if (totalComprobante) {
            totalComprobante.value = totalLinea;
        }
    };

    const sincronizarCabeceraPorTipoComprobante = () => {
        const tipoComprobante = document.getElementById("vc-tipo-comprobante");
        const opcion = obtenerOpcionSeleccionada(tipoComprobante);

        if (!opcion) {
            return;
        }

        const letra = document.getElementById("vc-letra");
        const puntoVenta = document.getElementById("vc-punto-venta");
        const numero = document.getElementById("vc-numero");
        const moneda = document.getElementById("vc-moneda");

        if (letra && opcion.dataset.letra) {
            letra.value = opcion.dataset.letra;
        }

        if (puntoVenta && opcion.dataset.puntoVenta) {
            puntoVenta.value = opcion.dataset.puntoVenta;
        }

        if (numero && opcion.dataset.proximoNumero) {
            numero.value = opcion.dataset.proximoNumero;
        }

        if (moneda && opcion.dataset.monedaCodigo) {
            moneda.value = opcion.dataset.monedaCodigo;
        }
    };

    const obtenerElementoAsociacion = () => ({
        cliente: document.getElementById("vc-cliente"),
        tipoComprobante: document.getElementById("vc-tipo-comprobante"),
        contenedor: document.getElementById("vc-comprobante-asociado-contenedor"),
        select: document.getElementById("vc-comprobante-asociado"),
        ayuda: document.getElementById("vc-comprobante-asociado-ayuda"),
        submit: document.getElementById("vc-submit"),
    });

    const obtenerTipoComprobanteSeleccionado = () => {
        const { tipoComprobante } = obtenerElementoAsociacion();
        return tipoComprobante ? tipoComprobante.value : "";
    };

    const esTipoNotaDebito = (valorTipo) => (
        TIPOS_COMPROBANTE_NOTA_DEBITO.has(valorTipo)
    );

    const esTipoNotaCredito = (valorTipo) => (
        TIPOS_COMPROBANTE_NOTA_CREDITO.has(valorTipo)
    );

    const requiereComprobanteAsociado = () => (
        TIPOS_COMPROBANTE_MODIFICADORES.has(obtenerTipoComprobanteSeleccionado())
    );

    const actualizarControlNeriSoftSelect = (select, deshabilitado) => {
        if (!select) {
            return;
        }

        const contenedor = select.closest(".ns-select");
        const control = contenedor
            ? contenedor.querySelector(".ns-select__control")
            : null;

        if (!control) {
            return;
        }

        control.disabled = deshabilitado;
        control.classList.toggle("disabled", deshabilitado);

        if (deshabilitado) {
            control.setAttribute("tabindex", "-1");
            return;
        }

        control.removeAttribute("tabindex");
    };

    const sincronizarSelectorComprobanteAsociado = () => {
        const {
            cliente,
            contenedor,
            select,
            ayuda,
            submit,
        } = obtenerElementoAsociacion();
        const tipoSeleccionado = obtenerTipoComprobanteSeleccionado();
        const requiereAsociacion = requiereComprobanteAsociado();
        const clienteId = cliente ? cliente.value : "";
        const esNotaDebito = esTipoNotaDebito(tipoSeleccionado);
        const esNotaCredito = esTipoNotaCredito(tipoSeleccionado);

        if (!contenedor || !select) {
            return;
        }

        contenedor.classList.toggle("d-none", !requiereAsociacion);
        select.required = requiereAsociacion;
        select.disabled = !requiereAsociacion || !clienteId;

        let cantidadOpcionesCliente = 0;

        Array.from(select.options).forEach((opcion) => {
            if (!opcion.value) {
                opcion.disabled = false;
                return;
            }

            const perteneceAlCliente = Boolean(clienteId) &&
                opcion.dataset.clienteId === clienteId;
            const tipoAsociado = opcion.dataset.tipoComprobante || "";
            const saldoDisponibleNc = Number.parseInt(
                opcion.dataset.saldoDisponibleNcCentavos || "0",
                10
            );
            const esFacturaAsociableNd = esNotaDebito &&
                tipoAsociado === "FACTURA";
            const esComprobanteAsociableNc = esNotaCredito &&
                ["FACTURA", "NOTA_DEBITO"].includes(tipoAsociado) &&
                Number.isFinite(saldoDisponibleNc) &&
                saldoDisponibleNc > 0;
            const opcionPermitida = esFacturaAsociableNd || esComprobanteAsociableNc;
            const seleccionable = perteneceAlCliente && opcionPermitida;

            opcion.disabled = !seleccionable;

            if (seleccionable) {
                cantidadOpcionesCliente += 1;
            }
        });

        if (
            select.value &&
            select.options[select.selectedIndex] &&
            select.options[select.selectedIndex].disabled
        ) {
            select.value = "";
        }

        select.dispatchEvent(new Event("change", { bubbles: true }));
        actualizarControlNeriSoftSelect(select, select.disabled);

        if (ayuda) {
            if (!requiereAsociacion) {
                ayuda.textContent = "La FC no requiere comprobante asociado.";
            } else if (!clienteId) {
                ayuda.textContent = "Elegí un cliente para listar comprobantes confirmados.";
            } else if (cantidadOpcionesCliente === 0 && esNotaCredito) {
                ayuda.textContent = "No hay FC o ND confirmadas con saldo disponible para NC.";
            } else if (cantidadOpcionesCliente === 0 && esNotaDebito) {
                ayuda.textContent = "No hay FC confirmadas para el cliente seleccionado.";
            } else if (esNotaCredito) {
                ayuda.textContent = "Elegí la FC o ND confirmada con saldo disponible para esta NC.";
            } else {
                ayuda.textContent = "Elegí la FC confirmada que modifica esta ND.";
            }
        }

        if (submit) {
            if (!submit.dataset.textoOriginal) {
                submit.dataset.textoOriginal = submit.textContent;
            }

            submit.disabled = false;
            submit.textContent = submit.dataset.textoOriginal;
        }
    };

    const validarArticuloAntesDeEnviar = async (evento) => {
        sincronizarSelectorComprobanteAsociado();

        const formulario = evento.target;
        const inputLookup = document.querySelector(SELECTORES.lookupArticulos);
        const hiddenArticulo = inputLookup ? obtenerHiddenLookup(inputLookup) : null;

        if (!inputLookup || !hiddenArticulo) {
            return;
        }

        if (formulario.dataset.vcLookupSubmitSincronizado === "1") {
            delete formulario.dataset.vcLookupSubmitSincronizado;
            return;
        }

        const articuloSincronizado = sincronizarArticuloSeleccionado(inputLookup) ||
            seleccionarArticuloUnicoSiCorresponde(inputLookup, true);

        if (articuloSincronizado && hiddenArticulo.value) {
            inputLookup.setCustomValidity("");
            return;
        }

        evento.preventDefault();

        const articuloResuelto = await resolverArticuloPorLookupAntesDeEnviar(inputLookup);

        if (articuloResuelto && hiddenArticulo.value) {
            inputLookup.setCustomValidity("");
            formulario.dataset.vcLookupSubmitSincronizado = "1";
            formulario.requestSubmit();
            return;
        }

        inputLookup.setCustomValidity(
            "Seleccioná un producto o servicio de la lista."
        );
        inputLookup.reportValidity();
        inputLookup.focus();
    };

    document.addEventListener("DOMContentLoaded", () => {
        Object.values(SELECTORES).forEach((selector) => {
            if (
                selector === SELECTORES.formulario ||
                selector === SELECTORES.badgesCiclicos ||
                selector === SELECTORES.lookupArticulos
            ) {
                return;
            }

            const elemento = document.querySelector(selector);

            if (!elemento || elemento.readOnly) {
                return;
            }

            elemento.addEventListener("input", actualizarSubtotalLinea);
            elemento.addEventListener("change", actualizarSubtotalLinea);
        });

        document.querySelectorAll(SELECTORES.badgesCiclicos).forEach((badge) => {
            const select = document.getElementById(badge.dataset.targetSelect || "");

            sincronizarBadge(badge);
            badge.addEventListener("click", () => ciclarBadge(badge));

            if (select) {
                select.addEventListener("change", () => {
                    sincronizarBadge(badge);
                    actualizarSubtotalLinea();
                });
            }
        });

        document.querySelectorAll(SELECTORES.lookupArticulos).forEach((inputLookup) => {
            inputLookup.addEventListener("input", () => {
                cargarOpcionesLookupArticulos(inputLookup);
            });
            inputLookup.addEventListener("change", () => {
                if (!sincronizarArticuloSeleccionado(inputLookup)) {
                    seleccionarArticuloUnicoSiCorresponde(inputLookup, true);
                }
                actualizarSubtotalLinea();
            });
            inputLookup.addEventListener("blur", () => {
                if (!sincronizarArticuloSeleccionado(inputLookup)) {
                    seleccionarArticuloUnicoSiCorresponde(inputLookup, true);
                }
                actualizarSubtotalLinea();
            });
        });

        const cliente = document.getElementById("vc-cliente");
        const tipoComprobante = document.getElementById("vc-tipo-comprobante");

        if (cliente) {
            cliente.addEventListener("change", sincronizarSelectorComprobanteAsociado);
        }

        if (tipoComprobante) {
            tipoComprobante.addEventListener("change", () => {
                sincronizarCabeceraPorTipoComprobante();
                sincronizarSelectorComprobanteAsociado();
            });
        }

        const formulario = document.querySelector(SELECTORES.formulario);
        if (formulario) {
            formulario.addEventListener("submit", validarArticuloAntesDeEnviar);
        }

        sincronizarCabeceraPorTipoComprobante();
        sincronizarSelectorComprobanteAsociado();
        actualizarSubtotalLinea();
    });
})();
