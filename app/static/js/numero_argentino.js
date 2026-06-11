(() => {
    "use strict";

    const SELECTOR_DECIMAL_ARGENTINO = 'input[data-decimal="argentino"]';
    const SELECTOR_MONEDA_ARGENTINA_CENTAVOS =
        'input[data-money-ar="centavos"]';
    const SELECTOR_COTIZACION_ARGENTINA =
        'input[data-cotizacion-ar="1000000"]';

    const esPuntoDecimal = (evento) => (
        evento.key === "." ||
        evento.code === "NumpadDecimal" ||
        evento.data === "."
    );

    const esSeparadorDecimalArgentino = (evento) => (
        esPuntoDecimal(evento) ||
        evento.key === "," ||
        evento.data === ","
    );

    const insertarComaDecimal = (input) => {
        const inicio = input.selectionStart ?? input.value.length;
        const fin = input.selectionEnd ?? input.value.length;

        if (typeof input.setRangeText === "function") {
            input.setRangeText(",", inicio, fin, "end");
        } else {
            input.value = `${input.value.slice(0, inicio)},${input.value.slice(fin)}`;
            input.selectionStart = inicio + 1;
            input.selectionEnd = inicio + 1;
        }

        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const manejarKeydownDecimalArgentino = (input, evento) => {
        if (evento.ctrlKey || evento.altKey || evento.metaKey) {
            return;
        }

        if (!esPuntoDecimal(evento)) {
            return;
        }

        evento.preventDefault();
        insertarComaDecimal(input);
    };

    const manejarBeforeInputDecimalArgentino = (input, evento) => {
        if (evento.inputType !== "insertText" || !esPuntoDecimal(evento)) {
            return;
        }

        evento.preventDefault();
        insertarComaDecimal(input);
    };

    const normalizarPegadoDecimalArgentino = (input) => {
        const valorNormalizado = input.value.replaceAll(".", ",");

        if (valorNormalizado === input.value) {
            return;
        }

        input.value = valorNormalizado;
        input.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const inicializarDecimalArgentino = (input) => {
        if (input.dataset.decimalInicializado === "1") {
            return;
        }

        input.dataset.decimalInicializado = "1";

        input.addEventListener("keydown", (evento) => {
            manejarKeydownDecimalArgentino(input, evento);
        });

        input.addEventListener("beforeinput", (evento) => {
            manejarBeforeInputDecimalArgentino(input, evento);
        });

        input.addEventListener("paste", () => {
            setTimeout(() => normalizarPegadoDecimalArgentino(input), 0);
        });
    };

    const obtenerInputMonedaArgentinaDesdeEvento = (evento) => {
        if (!(evento.target instanceof Element)) {
            return null;
        }

        return evento.target.closest(SELECTOR_MONEDA_ARGENTINA_CENTAVOS);
    };

    const obtenerIndices = (valor, caracter) => {
        const indices = [];

        Array.from(String(valor || "")).forEach((valorCaracter, indice) => {
            if (valorCaracter === caracter) {
                indices.push(indice);
            }
        });

        return indices;
    };

    const obtenerIndiceSeparadorDecimal = (valor) => {
        const valorTexto = String(valor || "");
        const indiceComa = valorTexto.indexOf(",");

        if (indiceComa >= 0) {
            return indiceComa;
        }

        const indicesPunto = obtenerIndices(valorTexto, ".");

        if (indicesPunto.length === 0) {
            return -1;
        }

        if (indicesPunto.length === 1) {
            return indicesPunto[0];
        }

        const ultimoIndicePunto = indicesPunto[indicesPunto.length - 1];
        const digitosLuegoDelUltimoPunto = valorTexto
            .slice(ultimoIndicePunto + 1)
            .replace(/\D/g, "");

        if (digitosLuegoDelUltimoPunto.length <= 2) {
            return ultimoIndicePunto;
        }

        return -1;
    };

    const contarDigitos = (valor) => (
        String(valor || "").replace(/\D/g, "").length
    );

    const normalizarPartesMonedaArgentina = (valor) => {
        const valorTexto = String(valor || "").trim();

        if (!valorTexto) {
            return {
                signo: "",
                parteEntera: "",
                parteDecimal: "",
            };
        }

        const signo = valorTexto.startsWith("-") ? "-" : "";
        const valorSinSigno = valorTexto.replace(/^[+-]/, "");
        const indiceSeparador = obtenerIndiceSeparadorDecimal(valorSinSigno);

        if (indiceSeparador < 0) {
            return {
                signo,
                parteEntera: valorSinSigno.replace(/\D/g, ""),
                parteDecimal: "",
            };
        }

        return {
            signo,
            parteEntera: valorSinSigno
                .slice(0, indiceSeparador)
                .replace(/\D/g, ""),
            parteDecimal: valorSinSigno
                .slice(indiceSeparador + 1)
                .replace(/\D/g, "")
                .slice(0, 2),
        };
    };

    const formatearMilesArgentinos = (digitosEnteros) => {
        const parteEntera = String(digitosEnteros || "")
            .replace(/^0+(?=\d)/, "") || "0";

        return parteEntera.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    };

    const formatearMonedaArgentinaCentavos = (partes) => {
        const tieneValor = Boolean(partes.parteEntera || partes.parteDecimal);

        if (!tieneValor) {
            return "";
        }

        const parteEntera = formatearMilesArgentinos(partes.parteEntera);
        const parteDecimal = String(partes.parteDecimal || "")
            .slice(0, 2)
            .padEnd(2, "0");

        return `${partes.signo}${parteEntera},${parteDecimal}`;
    };

    const obtenerContextoCursorMonedaArgentina = (valor, posicion) => {
        const valorTexto = String(valor || "");
        const posicionCursor = posicion ?? valorTexto.length;
        const indiceSeparador = obtenerIndiceSeparadorDecimal(valorTexto);

        if (indiceSeparador >= 0 && posicionCursor > indiceSeparador) {
            return {
                seccion: "decimal",
                digitos: contarDigitos(
                    valorTexto.slice(indiceSeparador + 1, posicionCursor)
                ),
            };
        }

        const limiteEntero = indiceSeparador >= 0
            ? Math.min(posicionCursor, indiceSeparador)
            : posicionCursor;

        return {
            seccion: "entera",
            digitos: contarDigitos(valorTexto.slice(0, limiteEntero)),
        };
    };

    const obtenerPosicionPorDigitosEnteros = (valor, cantidadDigitos) => {
        const valorTexto = String(valor || "");
        const indiceComa = valorTexto.indexOf(",");
        const limite = indiceComa >= 0 ? indiceComa : valorTexto.length;

        if (cantidadDigitos <= 0) {
            return valorTexto.startsWith("-") ? 1 : 0;
        }

        let digitosVistos = 0;

        for (let indice = 0; indice < limite; indice += 1) {
            if (/\d/.test(valorTexto[indice])) {
                digitosVistos += 1;
            }

            if (digitosVistos >= cantidadDigitos) {
                return indice + 1;
            }
        }

        return limite;
    };

    const obtenerPosicionPorDigitosDecimales = (valor, cantidadDigitos) => {
        const indiceComa = String(valor || "").indexOf(",");

        if (indiceComa < 0) {
            return String(valor || "").length;
        }

        return Math.min(indiceComa + 1 + cantidadDigitos, indiceComa + 3);
    };

    const posicionarCursorMonedaArgentina = (input, contextoCursor) => {
        if (typeof input.setSelectionRange !== "function") {
            return;
        }

        const posicion = contextoCursor.seccion === "decimal"
            ? obtenerPosicionPorDigitosDecimales(input.value, contextoCursor.digitos)
            : obtenerPosicionPorDigitosEnteros(input.value, contextoCursor.digitos);

        input.setSelectionRange(posicion, posicion);
    };

    const formatearMonedaArgentinaEnVivo = (input) => {
        const valorOriginal = input.value;
        const posicionOriginal = input.selectionStart ?? valorOriginal.length;
        const contextoCursor = obtenerContextoCursorMonedaArgentina(
            valorOriginal,
            posicionOriginal
        );
        const partes = normalizarPartesMonedaArgentina(valorOriginal);
        const valorFormateado = formatearMonedaArgentinaCentavos(partes);

        if (valorFormateado !== valorOriginal) {
            input.value = valorFormateado;
        }

        posicionarCursorMonedaArgentina(input, contextoCursor);
    };

    const obtenerInputCotizacionArgentinaDesdeEvento = (evento) => {
        if (!(evento.target instanceof Element)) {
            return null;
        }

        return evento.target.closest(SELECTOR_COTIZACION_ARGENTINA);
    };

    const obtenerDecimalesDesdeEscala = (escala) => {
        const escalaNumero = Number.parseInt(String(escala || ""), 10);

        if (!Number.isFinite(escalaNumero) || escalaNumero <= 0) {
            return 0;
        }

        return Math.max(0, String(escalaNumero).length - 1);
    };

    const obtenerIndiceSeparadorDecimalCotizacion = (valor) => {
        const valorTexto = String(valor || "");
        const indiceComa = valorTexto.indexOf(",");

        if (indiceComa >= 0) {
            return indiceComa;
        }

        const indicesPunto = obtenerIndices(valorTexto, ".");

        if (indicesPunto.length === 0) {
            return -1;
        }

        if (indicesPunto.length > 1) {
            return -1;
        }

        const indicePunto = indicesPunto[0];
        const digitosAntes = valorTexto
            .slice(0, indicePunto)
            .replace(/\D/g, "");
        const digitosDespues = valorTexto
            .slice(indicePunto + 1)
            .replace(/\D/g, "");

        if (
            digitosDespues.length === 3 &&
            digitosAntes.length >= 1 &&
            digitosAntes.length <= 3
        ) {
            return -1;
        }

        return indicePunto;
    };

    const normalizarPartesCotizacionArgentina = (valor, escala) => {
        const valorTexto = String(valor || "").trim();

        if (!valorTexto) {
            return {
                parteEntera: "",
                parteDecimal: "",
                decimales: obtenerDecimalesDesdeEscala(escala),
            };
        }

        const valorSinEspacios = valorTexto.replace(/\s/g, "");

        if (valorSinEspacios.startsWith("-")) {
            return null;
        }

        if (!/^\+?[\d.,]*$/.test(valorSinEspacios)) {
            return null;
        }

        if ((valorSinEspacios.match(/,/g) || []).length > 1) {
            return null;
        }

        const valorSinSigno = valorSinEspacios.replace(/^\+/, "");
        const decimales = obtenerDecimalesDesdeEscala(escala);
        const indiceSeparador = obtenerIndiceSeparadorDecimalCotizacion(
            valorSinSigno
        );

        if (indiceSeparador < 0) {
            return {
                parteEntera: valorSinSigno.replace(/\D/g, ""),
                parteDecimal: "",
                decimales,
            };
        }

        return {
            parteEntera: valorSinSigno
                .slice(0, indiceSeparador)
                .replace(/\D/g, ""),
            parteDecimal: valorSinSigno
                .slice(indiceSeparador + 1)
                .replace(/\D/g, "")
                .slice(0, decimales),
            decimales,
        };
    };

    const decimalArAEnteroEscala = (valor, escala) => {
        const escalaNumero = Number.parseInt(String(escala || ""), 10);
        const partes = normalizarPartesCotizacionArgentina(valor, escalaNumero);

        if (!partes) {
            return null;
        }

        if (!partes.parteEntera && !partes.parteDecimal) {
            return 0;
        }

        const enteros = Number.parseInt(partes.parteEntera || "0", 10);
        const decimales = Number.parseInt(
            String(partes.parteDecimal || "")
                .padEnd(partes.decimales, "0")
                .slice(0, partes.decimales) || "0",
            10
        );

        return (enteros * escalaNumero) + decimales;
    };

    const cotizacionArA1000000 = (valor) => (
        decimalArAEnteroEscala(valor, 1000000)
    );

    const formatearCotizacionArgentinaEscala = (valor, escala) => {
        const partes = normalizarPartesCotizacionArgentina(valor, escala);

        if (!partes) {
            return String(valor || "");
        }

        if (!partes.parteEntera && !partes.parteDecimal) {
            return "";
        }

        const parteEntera = formatearMilesArgentinos(partes.parteEntera);
        const parteDecimal = String(partes.parteDecimal || "")
            .slice(0, partes.decimales)
            .padEnd(partes.decimales, "0");

        return `${parteEntera},${parteDecimal}`;
    };

    const obtenerContextoCursorCotizacionArgentina = (
        valor,
        posicion,
        escala
    ) => {
        const valorTexto = String(valor || "");
        const posicionCursor = posicion ?? valorTexto.length;
        const indiceSeparador = obtenerIndiceSeparadorDecimalCotizacion(
            valorTexto
        );

        if (indiceSeparador >= 0 && posicionCursor > indiceSeparador) {
            return {
                seccion: "decimal",
                digitos: contarDigitos(
                    valorTexto.slice(indiceSeparador + 1, posicionCursor)
                ),
                decimales: obtenerDecimalesDesdeEscala(escala),
            };
        }

        const limiteEntero = indiceSeparador >= 0
            ? Math.min(posicionCursor, indiceSeparador)
            : posicionCursor;

        return {
            seccion: "entera",
            digitos: contarDigitos(valorTexto.slice(0, limiteEntero)),
            decimales: obtenerDecimalesDesdeEscala(escala),
        };
    };

    const obtenerPosicionPorDigitosDecimalesEscala = (
        valor,
        cantidadDigitos,
        decimales
    ) => {
        const indiceComa = String(valor || "").indexOf(",");

        if (indiceComa < 0) {
            return String(valor || "").length;
        }

        return Math.min(
            indiceComa + 1 + cantidadDigitos,
            indiceComa + 1 + decimales
        );
    };

    const posicionarCursorCotizacionArgentina = (input, contextoCursor) => {
        if (typeof input.setSelectionRange !== "function") {
            return;
        }

        const posicion = contextoCursor.seccion === "decimal"
            ? obtenerPosicionPorDigitosDecimalesEscala(
                input.value,
                contextoCursor.digitos,
                contextoCursor.decimales
            )
            : obtenerPosicionPorDigitosEnteros(
                input.value,
                contextoCursor.digitos
            );

        input.setSelectionRange(posicion, posicion);
    };

    const formatearCotizacionArgentinaEnVivo = (input) => {
        const valorOriginal = input.value;
        const escala = input.dataset.cotizacionAr || "1000000";
        const posicionOriginal = input.selectionStart ?? valorOriginal.length;
        const contextoCursor = obtenerContextoCursorCotizacionArgentina(
            valorOriginal,
            posicionOriginal,
            escala
        );
        const valorFormateado = formatearCotizacionArgentinaEscala(
            valorOriginal,
            escala
        );

        if (valorFormateado !== valorOriginal) {
            input.value = valorFormateado;
        }

        posicionarCursorCotizacionArgentina(input, contextoCursor);
    };

    const activarDecimalCotizacionArgentina = (input) => {
        const escala = input.dataset.cotizacionAr || "1000000";
        const partes = normalizarPartesCotizacionArgentina(input.value, escala);
        const partesConEnteroInicial = {
            ...(partes || {
                parteEntera: "",
                parteDecimal: "",
                decimales: obtenerDecimalesDesdeEscala(escala),
            }),
            parteEntera: partes && partes.parteEntera ? partes.parteEntera : "0",
        };

        input.value = formatearCotizacionArgentinaEscala(
            `${partesConEnteroInicial.parteEntera},${partesConEnteroInicial.parteDecimal}`,
            escala
        );

        const indiceComa = input.value.indexOf(",");

        if (indiceComa >= 0 && typeof input.setSelectionRange === "function") {
            input.setSelectionRange(indiceComa + 1, indiceComa + 1);
        }

        input.dispatchEvent(new Event("input", { bubbles: true }));
    };

    const manejarKeydownCotizacionArgentina = (evento) => {
        const input = obtenerInputCotizacionArgentinaDesdeEvento(evento);

        if (!input || evento.ctrlKey || evento.altKey || evento.metaKey) {
            return;
        }

        if (!esSeparadorDecimalArgentino(evento)) {
            return;
        }

        evento.preventDefault();
        activarDecimalCotizacionArgentina(input);
    };

    const manejarBeforeInputCotizacionArgentina = (evento) => {
        const input = obtenerInputCotizacionArgentinaDesdeEvento(evento);

        if (
            !input ||
            evento.inputType !== "insertText" ||
            !esSeparadorDecimalArgentino(evento)
        ) {
            return;
        }

        evento.preventDefault();
        activarDecimalCotizacionArgentina(input);
    };

    const manejarInputCotizacionArgentina = (evento) => {
        const input = obtenerInputCotizacionArgentinaDesdeEvento(evento);

        if (!input) {
            return;
        }

        formatearCotizacionArgentinaEnVivo(input);
    };

    const manejarPasteCotizacionArgentina = (evento) => {
        const input = obtenerInputCotizacionArgentinaDesdeEvento(evento);

        if (!input) {
            return;
        }

        setTimeout(() => formatearCotizacionArgentinaEnVivo(input), 0);
    };

    const inicializarCotizacionesArgentinas = () => {
        document
            .querySelectorAll(SELECTOR_COTIZACION_ARGENTINA)
            .forEach((input) => {
                if (input.value.trim()) {
                    formatearCotizacionArgentinaEnVivo(input);
                }
            });
    };

    window.NeriSoftNumeroArgentino = {
        ...(window.NeriSoftNumeroArgentino || {}),
        decimalArAEnteroEscala,
        cotizacionArA1000000,
    };

    const activarDecimalMonedaArgentina = (input) => {
        const partes = normalizarPartesMonedaArgentina(input.value);
        const partesConEnteroInicial = {
            ...partes,
            parteEntera: partes.parteEntera || "0",
        };

        input.value = formatearMonedaArgentinaCentavos(partesConEnteroInicial);

        const indiceComa = input.value.indexOf(",");

        if (indiceComa >= 0 && typeof input.setSelectionRange === "function") {
            input.setSelectionRange(indiceComa + 1, indiceComa + 1);
        }

        input.dispatchEvent(new Event("input", { bubbles: true }));
    };

    const manejarKeydownMonedaArgentina = (evento) => {
        const input = obtenerInputMonedaArgentinaDesdeEvento(evento);

        if (!input || evento.ctrlKey || evento.altKey || evento.metaKey) {
            return;
        }

        if (!esSeparadorDecimalArgentino(evento)) {
            return;
        }

        evento.preventDefault();
        activarDecimalMonedaArgentina(input);
    };

    const manejarBeforeInputMonedaArgentina = (evento) => {
        const input = obtenerInputMonedaArgentinaDesdeEvento(evento);

        if (
            !input ||
            evento.inputType !== "insertText" ||
            !esSeparadorDecimalArgentino(evento)
        ) {
            return;
        }

        evento.preventDefault();
        activarDecimalMonedaArgentina(input);
    };

    const manejarInputMonedaArgentina = (evento) => {
        const input = obtenerInputMonedaArgentinaDesdeEvento(evento);

        if (!input) {
            return;
        }

        formatearMonedaArgentinaEnVivo(input);
    };

    const manejarPasteMonedaArgentina = (evento) => {
        const input = obtenerInputMonedaArgentinaDesdeEvento(evento);

        if (!input) {
            return;
        }

        setTimeout(() => formatearMonedaArgentinaEnVivo(input), 0);
    };

    const inicializarMonedasArgentinas = () => {
        document
            .querySelectorAll(SELECTOR_MONEDA_ARGENTINA_CENTAVOS)
            .forEach((input) => {
                if (input.value.trim()) {
                    formatearMonedaArgentinaEnVivo(input);
                }
            });
    };

    document.addEventListener("keydown", manejarKeydownCotizacionArgentina);
    document.addEventListener("keydown", manejarKeydownMonedaArgentina);
    document.addEventListener("beforeinput", manejarBeforeInputCotizacionArgentina);
    document.addEventListener("beforeinput", manejarBeforeInputMonedaArgentina);
    document.addEventListener("input", manejarInputCotizacionArgentina);
    document.addEventListener("input", manejarInputMonedaArgentina);
    document.addEventListener("paste", manejarPasteCotizacionArgentina);
    document.addEventListener("paste", manejarPasteMonedaArgentina);

    document.addEventListener("DOMContentLoaded", () => {
        document
            .querySelectorAll(SELECTOR_DECIMAL_ARGENTINO)
            .forEach(inicializarDecimalArgentino);

        inicializarCotizacionesArgentinas();
        inicializarMonedasArgentinas();
    });
})();
