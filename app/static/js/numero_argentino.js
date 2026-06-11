(() => {
    "use strict";

    const SELECTOR_DECIMAL_ARGENTINO = 'input[data-decimal="argentino"]';
    const SELECTOR_MONEDA_ARGENTINA_CENTAVOS =
        'input[data-money-ar="centavos"]';

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

    const activarDecimalMonedaArgentina = (input) => {
        const partes = normalizarPartesMonedaArgentina(input.value);

        input.value = formatearMonedaArgentinaCentavos(partes);

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

    document.addEventListener("keydown", manejarKeydownMonedaArgentina);
    document.addEventListener("beforeinput", manejarBeforeInputMonedaArgentina);
    document.addEventListener("input", manejarInputMonedaArgentina);
    document.addEventListener("paste", manejarPasteMonedaArgentina);

    document.addEventListener("DOMContentLoaded", () => {
        document
            .querySelectorAll(SELECTOR_DECIMAL_ARGENTINO)
            .forEach(inicializarDecimalArgentino);

        inicializarMonedasArgentinas();
    });
})();
