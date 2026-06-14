(function () {
    "use strict";

    const SELECTOR_FORM_ROOT = "#mope-form";
    const SELECTOR_TIPO = "#mope-tipo";
    const SELECTOR_MONEDA = "#mope-moneda";
    const SELECTOR_REQUIERE_COTIZACION = "#mope-requiere-cotizacion";
    const SELECTOR_COTIZACION = "#mope-cotizacion";
    const SELECTOR_CUENTA_CONTABLE = "#mope-cuenta-contable";
    const SELECTOR_CUENTA_CONTABLE_ESTADO = "#mope-cuenta-contable-estado";
    const SELECTOR_CUENTAS_CONTABLES_LISTA = "#mope-cuentas-contables-lista";
    const SELECTOR_CAMPOS_BANCO = "[data-mope-bank-field]";

    const TIPO_BANCO_PROPIO = "BANCO_PROPIO";
    const MONEDA_CONTABLE = "ARS";
    const MENSAJE_CUENTA_INICIAL = "Ingrese una cuenta imputable existente.";
    const MENSAJE_CUENTA_OBLIGATORIA = "La cuenta contable es obligatoria.";
    const MENSAJE_CUENTA_MINIMO = "Ingrese al menos 3 caracteres para buscar la cuenta.";
    const MENSAJE_CUENTA_INVALIDA = "La cuenta contable no existe o no es imputable.";
    const MENSAJE_CUENTA_SUGERENCIAS = "Seleccione una cuenta imputable de las sugerencias.";
    const MENSAJE_CUENTA_ERROR = "No se pudo validar la cuenta contable.";

    let cuentaLookupTimeout = null;

    function obtenerRaizFormulario() {
        return document.querySelector(SELECTOR_FORM_ROOT);
    }

    function obtenerUrlCuentasImputables(terminoBusqueda) {
        const raizFormulario = obtenerRaizFormulario();

        if (!raizFormulario || !raizFormulario.dataset.cuentasImputablesUrl) {
            return null;
        }

        const urlLookup = new URL(
            raizFormulario.dataset.cuentasImputablesUrl,
            window.location.origin
        );

        urlLookup.searchParams.set("q", terminoBusqueda);
        urlLookup.searchParams.set(
            "limite",
            raizFormulario.dataset.cuentasImputablesLimite || "10"
        );

        return urlLookup.toString();
    }

    function limpiarCampo(campo) {
        if (campo.type === "checkbox") {
            campo.checked = false;
            return;
        }

        campo.value = "";
    }

    function actualizarCamposBanco() {
        const tipo = document.querySelector(SELECTOR_TIPO);
        const usaBanco = tipo && tipo.value === TIPO_BANCO_PROPIO;
        const camposBanco = Array.from(
            document.querySelectorAll(SELECTOR_CAMPOS_BANCO)
        );

        camposBanco.forEach((campo) => {
            campo.disabled = !usaBanco;

            if (!usaBanco) {
                limpiarCampo(campo);
            }
        });
    }

    function actualizarCamposCotizacion() {
        const moneda = document.querySelector(SELECTOR_MONEDA);
        const requiereCotizacion = document.querySelector(
            SELECTOR_REQUIERE_COTIZACION
        );
        const cotizacion = document.querySelector(SELECTOR_COTIZACION);
        const monedaEsArs = moneda && moneda.value === MONEDA_CONTABLE;
        const permiteCambio = !monedaEsArs;

        if (requiereCotizacion) {
            requiereCotizacion.disabled = !permiteCambio;

            if (!permiteCambio) {
                requiereCotizacion.checked = false;
            }
        }

        if (cotizacion) {
            const deshabilitarCotizacion =
                !permiteCambio ||
                !requiereCotizacion ||
                !requiereCotizacion.checked;

            cotizacion.disabled = deshabilitarCotizacion;

            if (deshabilitarCotizacion) {
                cotizacion.value = "";
            }
        }
    }

    function pintarEstadoCuenta(mensaje, estado) {
        const cuentaContable = document.querySelector(SELECTOR_CUENTA_CONTABLE);
        const cuentaContableEstado = document.querySelector(
            SELECTOR_CUENTA_CONTABLE_ESTADO
        );

        if (!cuentaContableEstado || !cuentaContable) {
            return;
        }

        cuentaContableEstado.textContent = mensaje;
        cuentaContableEstado.classList.remove(
            "text-muted",
            "text-success",
            "text-danger",
            "text-warning"
        );
        cuentaContableEstado.classList.add(estado);
    }

    function resetearLookupCuenta() {
        const cuentaContable = document.querySelector(SELECTOR_CUENTA_CONTABLE);
        const cuentasContablesLista = document.querySelector(
            SELECTOR_CUENTAS_CONTABLES_LISTA
        );

        if (!cuentaContable || !cuentasContablesLista) {
            return;
        }

        cuentasContablesLista.innerHTML = "";
        cuentaContable.setCustomValidity("");
        pintarEstadoCuenta(MENSAJE_CUENTA_INICIAL, "text-muted");
    }

    function renderizarOpcionesCuenta(cuentasContablesLista, resultados) {
        cuentasContablesLista.innerHTML = "";

        resultados.forEach((cuenta) => {
            const opcion = document.createElement("option");
            opcion.value = cuenta.cuenta;
            opcion.label = cuenta.label || cuenta.descripcion || cuenta.cuenta;
            cuentasContablesLista.appendChild(opcion);
        });
    }

    function aplicarResultadoCuenta(cuentaContable, resultados, terminoBusqueda) {
        const cuentaExacta = resultados.find(
            (cuenta) => cuenta.cuenta === terminoBusqueda
        );

        if (cuentaExacta) {
            cuentaContable.setCustomValidity("");
            pintarEstadoCuenta(
                `Cuenta imputable: ${cuentaExacta.descripcion}`,
                "text-success"
            );
            return;
        }

        cuentaContable.setCustomValidity(MENSAJE_CUENTA_INVALIDA);

        if (resultados.length > 0) {
            pintarEstadoCuenta(MENSAJE_CUENTA_SUGERENCIAS, "text-warning");
            return;
        }

        pintarEstadoCuenta(MENSAJE_CUENTA_INVALIDA, "text-danger");
    }

    async function validarCuentaContableVisual() {
        const cuentaContable = document.querySelector(SELECTOR_CUENTA_CONTABLE);
        const cuentasContablesLista = document.querySelector(
            SELECTOR_CUENTAS_CONTABLES_LISTA
        );

        if (!cuentaContable || !cuentasContablesLista) {
            return;
        }

        const terminoBusqueda = cuentaContable.value.trim();
        cuentasContablesLista.innerHTML = "";

        if (!terminoBusqueda) {
            cuentaContable.setCustomValidity(MENSAJE_CUENTA_OBLIGATORIA);
            pintarEstadoCuenta(MENSAJE_CUENTA_INICIAL, "text-muted");
            return;
        }

        if (terminoBusqueda.length < 3) {
            cuentaContable.setCustomValidity(MENSAJE_CUENTA_MINIMO);
            pintarEstadoCuenta(MENSAJE_CUENTA_MINIMO, "text-warning");
            return;
        }

        const urlLookup = obtenerUrlCuentasImputables(terminoBusqueda);

        if (!urlLookup) {
            cuentaContable.setCustomValidity(MENSAJE_CUENTA_ERROR);
            pintarEstadoCuenta(MENSAJE_CUENTA_ERROR, "text-danger");
            return;
        }

        try {
            const respuesta = await fetch(urlLookup, {
                headers: {
                    Accept: "application/json",
                },
            });

            if (!respuesta.ok) {
                throw new Error(MENSAJE_CUENTA_ERROR);
            }

            const datos = await respuesta.json();
            const resultados = Array.isArray(datos.resultados)
                ? datos.resultados
                : [];

            renderizarOpcionesCuenta(cuentasContablesLista, resultados);
            aplicarResultadoCuenta(cuentaContable, resultados, terminoBusqueda);
        } catch (error) {
            cuentaContable.setCustomValidity(MENSAJE_CUENTA_ERROR);
            pintarEstadoCuenta(MENSAJE_CUENTA_ERROR, "text-danger");
        }
    }

    function programarLookupCuenta() {
        if (cuentaLookupTimeout) {
            window.clearTimeout(cuentaLookupTimeout);
        }

        cuentaLookupTimeout = window.setTimeout(validarCuentaContableVisual, 250);
    }

    function inicializarFormularioMediosOperativos() {
        const raizFormulario = obtenerRaizFormulario();

        if (!raizFormulario) {
            return;
        }

        const tipo = document.querySelector(SELECTOR_TIPO);
        const moneda = document.querySelector(SELECTOR_MONEDA);
        const requiereCotizacion = document.querySelector(
            SELECTOR_REQUIERE_COTIZACION
        );
        const cuentaContable = document.querySelector(SELECTOR_CUENTA_CONTABLE);

        if (tipo) {
            tipo.addEventListener("change", actualizarCamposBanco);
        }

        if (moneda) {
            moneda.addEventListener("change", actualizarCamposCotizacion);
        }

        if (requiereCotizacion) {
            requiereCotizacion.addEventListener("change", actualizarCamposCotizacion);
        }

        if (cuentaContable) {
            cuentaContable.addEventListener("input", programarLookupCuenta);
            cuentaContable.addEventListener("blur", validarCuentaContableVisual);
        }

        actualizarCamposBanco();
        actualizarCamposCotizacion();

        if (cuentaContable && cuentaContable.value.trim()) {
            validarCuentaContableVisual();
            return;
        }

        resetearLookupCuenta();
    }

    document.addEventListener("DOMContentLoaded", inicializarFormularioMediosOperativos);
}());
