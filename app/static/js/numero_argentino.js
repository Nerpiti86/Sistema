(() => {
    "use strict";

    const SELECTOR_DECIMAL_ARGENTINO = 'input[data-decimal="argentino"]';

    const esPuntoDecimal = (evento) => (
        evento.key === "." ||
        evento.code === "NumpadDecimal" ||
        evento.data === "."
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

    document.addEventListener("DOMContentLoaded", () => {
        document
            .querySelectorAll(SELECTOR_DECIMAL_ARGENTINO)
            .forEach(inicializarDecimalArgentino);
    });
})();
