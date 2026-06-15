(() => {
    "use strict";

    const MONEDA_CONTABLE = "ARS";
    const SELECTOR_MONEDA = "#psv-moneda";
    const SELECTOR_PRECIO = "#psv-precio-sugerido";
    const SELECTOR_COTIZACION = "#psv-cotizacion";
    const SELECTOR_PRECIO_ARS = "#psv-precio-sugerido-ars";

    const ESCALA_COTIZACION = 1000000;

    const normalizarImporteCentavos = (valor) => {
        const numeroArgentino = window.NeriSoftNumeroArgentino || {};

        if (typeof numeroArgentino.decimalArAEnteroEscala !== "function") {
            return null;
        }

        return numeroArgentino.decimalArAEnteroEscala(valor, 100);
    };

    const normalizarCotizacion = (valor) => {
        const numeroArgentino = window.NeriSoftNumeroArgentino || {};

        if (typeof numeroArgentino.cotizacionArA1000000 !== "function") {
            return null;
        }

        return numeroArgentino.cotizacionArA1000000(valor);
    };

    const formatearCentavos = (centavos) => {
        if (!Number.isFinite(centavos) || centavos < 0) {
            return "";
        }

        const valorRedondeado = Math.round(centavos);
        const parteEntera = Math.trunc(valorRedondeado / 100);
        const parteDecimal = String(valorRedondeado % 100).padStart(2, "0");
        const enteroFormateado = String(parteEntera).replace(
            /\B(?=(\d{3})+(?!\d))/g,
            "."
        );

        return `${enteroFormateado},${parteDecimal}`;
    };

    const actualizarPrecioArs = () => {
        const precio = document.querySelector(SELECTOR_PRECIO);
        const cotizacion = document.querySelector(SELECTOR_COTIZACION);
        const precioArs = document.querySelector(SELECTOR_PRECIO_ARS);

        if (!precio || !cotizacion || !precioArs) {
            return;
        }

        const precioCentavos = normalizarImporteCentavos(precio.value);
        const cotizacion1000000 = normalizarCotizacion(cotizacion.value);

        if (
            precioCentavos === null ||
            cotizacion1000000 === null ||
            cotizacion1000000 <= 0
        ) {
            precioArs.value = "";
            return;
        }

        precioArs.value = formatearCentavos(
            (precioCentavos * cotizacion1000000) / ESCALA_COTIZACION
        );
    };

    const actualizarCotizacion = () => {
        const moneda = document.querySelector(SELECTOR_MONEDA);
        const cotizacion = document.querySelector(SELECTOR_COTIZACION);

        if (!moneda || !cotizacion) {
            return;
        }

        const usaMonedaContable = moneda.value === MONEDA_CONTABLE;

        cotizacion.required = !usaMonedaContable;
        cotizacion.readOnly = usaMonedaContable;

        if (usaMonedaContable) {
            cotizacion.value = "1,000000";
        }

        actualizarPrecioArs();
    };

    document.addEventListener("DOMContentLoaded", () => {
        const moneda = document.querySelector(SELECTOR_MONEDA);
        const precio = document.querySelector(SELECTOR_PRECIO);
        const cotizacion = document.querySelector(SELECTOR_COTIZACION);

        actualizarCotizacion();

        if (moneda) {
            moneda.addEventListener("change", actualizarCotizacion);
        }

        if (precio) {
            precio.addEventListener("input", actualizarPrecioArs);
            precio.addEventListener("change", actualizarPrecioArs);
        }

        if (cotizacion) {
            cotizacion.addEventListener("input", actualizarPrecioArs);
            cotizacion.addEventListener("change", actualizarPrecioArs);
        }
    });
})();
