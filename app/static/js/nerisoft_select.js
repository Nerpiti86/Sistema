(() => {
    "use strict";

    const SELECTOR = "select[data-ns-select]";
    const CLASE_NATIVA = "ns-select-native";
    const CLASE_ABIERTO = "ns-select--open";
    const CLASE_ACTIVA = "ns-select__option--active";
    const CLASE_SELECCIONADA = "ns-select__option--selected";
    const TECLAS_NAVEGACION = ["ArrowDown", "ArrowUp", "Home", "End"];

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

    const obtenerBotonesVisibles = (estado) => (
        Array.from(estado.options.querySelectorAll("[data-ns-select-option-index]"))
    );

    const obtenerIndiceSeleccionadoVisible = (estado) => {
        const botones = obtenerBotonesVisibles(estado);
        const seleccionado = botones.find((boton) => (
            Number(boton.dataset.nsSelectOptionIndex) === estado.select.selectedIndex
        ));

        if (seleccionado) {
            return botones.indexOf(seleccionado);
        }

        return botones.length > 0 ? 0 : -1;
    };

    const marcarOpcionActiva = (estado, indiceVisible) => {
        const botones = obtenerBotonesVisibles(estado);

        if (botones.length === 0) {
            estado.indiceActivo = -1;
            estado.control.removeAttribute("aria-activedescendant");
            return;
        }

        const indiceSeguro = Math.max(0, Math.min(indiceVisible, botones.length - 1));
        estado.indiceActivo = indiceSeguro;

        botones.forEach((boton, indice) => {
            const activa = indice === indiceSeguro;
            boton.classList.toggle(CLASE_ACTIVA, activa);

            if (activa) {
                estado.control.setAttribute("aria-activedescendant", boton.id);
                boton.scrollIntoView({ block: "nearest" });
            }
        });
    };

    const cerrarSelect = (estado) => {
        estado.panel.hidden = true;
        estado.contenedor.classList.remove(CLASE_ABIERTO);
        estado.control.setAttribute("aria-expanded", "false");
        estado.control.removeAttribute("aria-activedescendant");

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

    const seleccionarOpcionActiva = (estado) => {
        const botones = obtenerBotonesVisibles(estado);
        const boton = botones[estado.indiceActivo];

        if (!boton) {
            return;
        }

        seleccionarOpcion(estado, Number(boton.dataset.nsSelectOptionIndex));
    };

    const pintarOpciones = (estado) => {
        const filtro = estado.search
            ? normalizarTexto(estado.search.value)
            : normalizarTexto(estado.busquedaRapida || "");
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
            boton.id = `${estado.select.id || "ns-select"}-option-${option.indice}`;
            boton.dataset.nsSelectOptionIndex = String(option.indice);
            boton.setAttribute("role", "option");
            boton.setAttribute("aria-selected", option.selected ? "true" : "false");

            if (option.selected) {
                boton.classList.add(CLASE_SELECCIONADA);
            }

            estado.options.appendChild(boton);
            cantidadVisible += 1;
        });

        if (cantidadVisible === 0) {
            estado.options.appendChild(
                crearElemento("div", "ns-select__empty", "Sin resultados")
            );
            marcarOpcionActiva(estado, -1);
            return;
        }

        marcarOpcionActiva(estado, obtenerIndiceSeleccionadoVisible(estado));
    };

    const abrirSelect = (estado) => {
        if (selectAbierto && selectAbierto !== estado) {
            cerrarSelect(selectAbierto);
        }

        estado.panel.hidden = false;
        estado.contenedor.classList.add(CLASE_ABIERTO);
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

    const moverOpcionActiva = (estado, direccion) => {
        const botones = obtenerBotonesVisibles(estado);

        if (botones.length === 0) {
            return;
        }

        const indiceBase = estado.indiceActivo < 0 ? 0 : estado.indiceActivo;
        const siguiente = direccion === "abajo" ? indiceBase + 1 : indiceBase - 1;

        marcarOpcionActiva(
            estado,
            Math.max(0, Math.min(siguiente, botones.length - 1))
        );
    };

    const irAlExtremo = (estado, extremo) => {
        const botones = obtenerBotonesVisibles(estado);

        if (botones.length === 0) {
            return;
        }

        marcarOpcionActiva(estado, extremo === "inicio" ? 0 : botones.length - 1);
    };

    const manejarNavegacion = (estado, evento) => {
        if (TECLAS_NAVEGACION.includes(evento.key)) {
            evento.preventDefault();

            if (estado.panel.hidden) {
                abrirSelect(estado);
            }

            if (evento.key === "ArrowDown") {
                moverOpcionActiva(estado, "abajo");
            }

            if (evento.key === "ArrowUp") {
                moverOpcionActiva(estado, "arriba");
            }

            if (evento.key === "Home") {
                irAlExtremo(estado, "inicio");
            }

            if (evento.key === "End") {
                irAlExtremo(estado, "fin");
            }

            return true;
        }

        if (evento.key === "Enter") {
            evento.preventDefault();

            if (estado.panel.hidden) {
                abrirSelect(estado);
                return true;
            }

            seleccionarOpcionActiva(estado);
            return true;
        }

        if (evento.key === "Escape") {
            cerrarSelect(estado);
            estado.control.focus();
            return true;
        }

        return false;
    };

    const buscarPorTecladoRapido = (estado, evento) => {
        if (
            estado.search ||
            evento.key.length !== 1 ||
            evento.ctrlKey ||
            evento.altKey ||
            evento.metaKey
        ) {
            return false;
        }

        evento.preventDefault();

        window.clearTimeout(estado.busquedaRapidaTimer);
        estado.busquedaRapida = `${estado.busquedaRapida || ""}${evento.key}`;
        estado.busquedaRapidaTimer = window.setTimeout(() => {
            estado.busquedaRapida = "";

            if (!estado.search && !estado.panel.hidden) {
                pintarOpciones(estado);
            }
        }, 1000);

        if (estado.panel.hidden) {
            abrirSelect(estado);
        } else {
            pintarOpciones(estado);
        }

        const textoBuscado = normalizarTexto(estado.busquedaRapida);
        const botones = obtenerBotonesVisibles(estado);
        const indiceEncontrado = botones.findIndex((boton) => (
            normalizarTexto(boton.textContent).startsWith(textoBuscado)
        ));

        if (indiceEncontrado >= 0) {
            marcarOpcionActiva(estado, indiceEncontrado);
            return true;
        }

        return false;
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
            indiceActivo: -1,
            busquedaRapida: "",
            busquedaRapidaTimer: null,
        };

        pintarEtiqueta(estado);

        control.addEventListener("click", () => alternarSelect(estado));

        control.addEventListener("keydown", (evento) => {
            if (manejarNavegacion(estado, evento)) {
                return;
            }

            if (evento.key === " ") {
                evento.preventDefault();
                alternarSelect(estado);
                return;
            }

            buscarPorTecladoRapido(estado, evento);
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

        options.addEventListener("mousemove", (evento) => {
            const boton = evento.target.closest("[data-ns-select-option-index]");

            if (!boton) {
                return;
            }

            const botones = obtenerBotonesVisibles(estado);
            marcarOpcionActiva(estado, botones.indexOf(boton));
        });

        if (search) {
            search.addEventListener("input", () => pintarOpciones(estado));

            search.addEventListener("keydown", (evento) => {
                if (manejarNavegacion(estado, evento)) {
                    return;
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
