(() => {
    "use strict";

    const SELECTOR = "select[data-ns-select]";
    const CLASE_NATIVA = "ns-select-native";

    let selectAbierto = null;

    const normalizarTexto = (texto) => (
        String(texto || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim()
    );

    const obtenerOpciones = (select) => (
        Array.from(select.options).map((option, indice) => ({
            indice,
            value: option.value,
            text: option.textContent.trim(),
            disabled: option.disabled,
            selected: option.selected,
        }))
    );

    const obtenerTextoSeleccionado = (select) => {
        const option = select.options[select.selectedIndex];

        if (!option || option.value === "") {
            return select.dataset.nsSelectPlaceholder || "Seleccionar...";
        }

        return option.textContent.trim();
    };

    const crearElemento = (tag, clase, texto = "") => {
        const elemento = document.createElement(tag);
        elemento.className = clase;

        if (texto) {
            elemento.textContent = texto;
        }

        return elemento;
    };

    const cerrarSelect = (estado) => {
        estado.panel.hidden = true;
        estado.control.setAttribute("aria-expanded", "false");

        if (selectAbierto === estado) {
            selectAbierto = null;
        }
    };

    const pintarEtiqueta = (estado) => {
        const texto = obtenerTextoSeleccionado(estado.select);
        const esPlaceholder = (
            !estado.select.value ||
            texto === (estado.select.dataset.nsSelectPlaceholder || "Seleccionar...")
        );

        estado.label.textContent = texto;
        estado.label.classList.toggle("ns-select__placeholder", esPlaceholder);
    };

    const seleccionarOpcion = (estado, indice) => {
        const option = estado.select.options[indice];

        if (!option || option.disabled) {
            return;
        }

        estado.select.selectedIndex = indice;
        estado.select.dispatchEvent(new Event("change", { bubbles: true }));
        pintarEtiqueta(estado);
        cerrarSelect(estado);
        estado.control.focus();
    };

    const pintarOpciones = (estado) => {
        const filtro = estado.search ? normalizarTexto(estado.search.value) : "";
        const opciones = obtenerOpciones(estado.select);
        let cantidadVisible = 0;

        estado.options.replaceChildren();

        opciones.forEach((option) => {
            if (option.disabled) {
                return;
            }

            if (filtro && !normalizarTexto(option.text).includes(filtro)) {
                return;
            }

            const boton = crearElemento("button", "ns-select__option", option.text);
            boton.type = "button";
            boton.dataset.nsSelectOptionIndex = String(option.indice);
            boton.setAttribute("role", "option");
            boton.setAttribute("aria-selected", option.selected ? "true" : "false");

            if (option.selected) {
                boton.classList.add("ns-select__option--selected");
            }

            estado.options.appendChild(boton);
            cantidadVisible += 1;
        });

        if (cantidadVisible === 0) {
            estado.options.appendChild(
                crearElemento("div", "ns-select__empty", "Sin resultados")
            );
        }
    };

    const abrirSelect = (estado) => {
        if (selectAbierto && selectAbierto !== estado) {
            cerrarSelect(selectAbierto);
        }

        estado.panel.hidden = false;
        estado.control.setAttribute("aria-expanded", "true");
        selectAbierto = estado;
        pintarOpciones(estado);

        if (estado.search) {
            estado.search.value = "";
            estado.search.focus();
        }
    };

    const alternarSelect = (estado) => {
        if (estado.panel.hidden) {
            abrirSelect(estado);
            return;
        }

        cerrarSelect(estado);
    };

    const construirSelect = (select) => {
        const modo = select.dataset.nsSelect;
        const contenedor = crearElemento("div", "ns-select");
        const control = crearElemento("button", "ns-select__control");
        const label = crearElemento("span", "ns-select__label");
        const arrow = crearElemento("span", "ns-select__arrow", "▼");
        const panel = crearElemento("div", "ns-select__panel");
        const options = crearElemento("div", "ns-select__options");
        let search = null;

        control.type = "button";
        control.setAttribute("aria-haspopup", "listbox");
        control.setAttribute("aria-expanded", "false");

        panel.hidden = true;
        panel.setAttribute("role", "listbox");

        control.appendChild(label);
        control.appendChild(arrow);

        if (modo === "search") {
            search = crearElemento("input", "ns-select__search");
            search.type = "search";
            search.placeholder = select.dataset.nsSelectSearchPlaceholder || "Buscar...";
            search.autocomplete = "off";
            panel.appendChild(search);
        }

        panel.appendChild(options);

        select.parentNode.insertBefore(contenedor, select);
        contenedor.appendChild(select);
        contenedor.appendChild(control);
        contenedor.appendChild(panel);

        select.classList.add(CLASE_NATIVA);
        select.tabIndex = -1;

        const estado = {
            select,
            contenedor,
            control,
            label,
            panel,
            options,
            search,
        };

        pintarEtiqueta(estado);

        control.addEventListener("click", () => alternarSelect(estado));

        control.addEventListener("keydown", (evento) => {
            if (evento.key === "Enter" || evento.key === " ") {
                evento.preventDefault();
                alternarSelect(estado);
            }

            if (evento.key === "Escape") {
                cerrarSelect(estado);
            }
        });

        panel.addEventListener("mousedown", (evento) => {
            evento.preventDefault();
        });

        options.addEventListener("click", (evento) => {
            const boton = evento.target.closest("[data-ns-select-option-index]");

            if (!boton) {
                return;
            }

            seleccionarOpcion(estado, Number(boton.dataset.nsSelectOptionIndex));
        });

        if (search) {
            search.addEventListener("input", () => pintarOpciones(estado));

            search.addEventListener("keydown", (evento) => {
                if (evento.key === "Escape") {
                    cerrarSelect(estado);
                    control.focus();
                }
            });
        }

        select.addEventListener("change", () => {
            pintarEtiqueta(estado);
            pintarOpciones(estado);
        });
    };

    document.addEventListener("click", (evento) => {
        if (selectAbierto && !selectAbierto.contenedor.contains(evento.target)) {
            cerrarSelect(selectAbierto);
        }
    });

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(SELECTOR).forEach((select) => {
            if (select.dataset.nsSelectInicializado === "1") {
                return;
            }

            select.dataset.nsSelectInicializado = "1";
            construirSelect(select);
        });
    });
})();
