(() => {
    "use strict";

    const SELECTOR = '[data-datepicker="fecha-argentina"]';
    const MESES = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ];
    const DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"];

    let datePickerAbierto = null;

    const completarDosDigitos = (valor) => String(valor).padStart(2, "0");

    const formatearFechaArgentina = (fecha) => (
        `${completarDosDigitos(fecha.getDate())}/` +
        `${completarDosDigitos(fecha.getMonth() + 1)}/` +
        `${fecha.getFullYear()}`
    );

    const obtenerFechaDesdeValor = (valor) => {
        const partes = String(valor || "").trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);

        if (!partes) {
            return null;
        }

        const dia = Number(partes[1]);
        const mes = Number(partes[2]);
        const anio = Number(partes[3]);
        const fecha = new Date(anio, mes - 1, dia);

        if (
            fecha.getFullYear() !== anio ||
            fecha.getMonth() !== mes - 1 ||
            fecha.getDate() !== dia
        ) {
            return null;
        }

        return fecha;
    };

    const normalizarEntradaFechaArgentina = (valor) => {
        const digitos = String(valor || "").replace(/\D/g, "").slice(0, 8);
        const partes = [];

        if (digitos.length > 0) {
            partes.push(digitos.slice(0, 2));
        }

        if (digitos.length > 2) {
            partes.push(digitos.slice(2, 4));
        }

        if (digitos.length > 4) {
            partes.push(digitos.slice(4, 8));
        }

        return partes.filter(Boolean).join("/");
    };

    const crearBoton = (texto, clase, accion) => {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = clase;
        boton.textContent = texto;

        if (accion) {
            boton.dataset.datepickerAction = accion;
        }

        return boton;
    };

    const obtenerInicioCalendario = (anio, mes) => {
        const primerDiaMes = new Date(anio, mes, 1);
        const diaSemanaLunesPrimero = (primerDiaMes.getDay() + 6) % 7;
        const inicio = new Date(anio, mes, 1);
        inicio.setDate(inicio.getDate() - diaSemanaLunesPrimero);

        return inicio;
    };

    const fechasMismoDia = (fechaA, fechaB) => (
        fechaA &&
        fechaB &&
        fechaA.getFullYear() === fechaB.getFullYear() &&
        fechaA.getMonth() === fechaB.getMonth() &&
        fechaA.getDate() === fechaB.getDate()
    );

    const construirDatePicker = (input) => {
        const contenedor = document.createElement("div");
        contenedor.className = "ns-date-field";

        input.parentNode.insertBefore(contenedor, input);
        contenedor.appendChild(input);

        const panel = document.createElement("div");
        panel.className = "ns-date-picker";
        panel.hidden = true;
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-label", "Selector de fecha");

        const header = document.createElement("div");
        header.className = "ns-date-picker__header";

        const botonAnterior = crearBoton("‹", "ns-date-picker__nav", "anterior");
        const titulo = document.createElement("p");
        titulo.className = "ns-date-picker__title";
        const botonSiguiente = crearBoton("›", "ns-date-picker__nav", "siguiente");

        header.appendChild(botonAnterior);
        header.appendChild(titulo);
        header.appendChild(botonSiguiente);

        const grilla = document.createElement("div");
        grilla.className = "ns-date-picker__grid";

        const footer = document.createElement("div");
        footer.className = "ns-date-picker__footer";

        const botonHoy = crearBoton("Hoy", "btn btn-sm btn-outline-primary", "hoy");
        const botonLimpiar = crearBoton(
            "Limpiar",
            "btn btn-sm btn-outline-secondary",
            "limpiar"
        );

        footer.appendChild(botonHoy);
        footer.appendChild(botonLimpiar);

        panel.appendChild(header);
        panel.appendChild(grilla);
        panel.appendChild(footer);
        contenedor.appendChild(panel);

        return {
            contenedor,
            input,
            panel,
            titulo,
            grilla,
        };
    };

    const pintarCalendario = (estado) => {
        const fechaSeleccionada = obtenerFechaDesdeValor(estado.input.value);
        const hoy = new Date();

        estado.titulo.textContent = `${MESES[estado.mesVisible]} ${estado.anioVisible}`;
        estado.grilla.replaceChildren();

        DIAS_SEMANA.forEach((dia) => {
            const celda = document.createElement("div");
            celda.className = "ns-date-picker__weekday";
            celda.textContent = dia;
            estado.grilla.appendChild(celda);
        });

        const fechaCursor = obtenerInicioCalendario(
            estado.anioVisible,
            estado.mesVisible
        );

        for (let indice = 0; indice < 42; indice += 1) {
            const fechaDia = new Date(fechaCursor);
            fechaDia.setDate(fechaCursor.getDate() + indice);

            const botonDia = document.createElement("button");
            botonDia.type = "button";
            botonDia.className = "ns-date-picker__day";
            botonDia.textContent = String(fechaDia.getDate());
            botonDia.dataset.datepickerDate = formatearFechaArgentina(fechaDia);

            if (fechaDia.getMonth() !== estado.mesVisible) {
                botonDia.classList.add("ns-date-picker__day--outside");
            }

            if (fechasMismoDia(fechaDia, fechaSeleccionada)) {
                botonDia.classList.add("ns-date-picker__day--selected");
            }

            if (fechasMismoDia(fechaDia, hoy)) {
                botonDia.classList.add("ns-date-picker__day--today");
            }

            estado.grilla.appendChild(botonDia);
        }
    };

    const cerrarDatePicker = (estado) => {
        estado.panel.hidden = true;

        if (datePickerAbierto === estado) {
            datePickerAbierto = null;
        }
    };

    const abrirDatePicker = (estado) => {
        if (datePickerAbierto && datePickerAbierto !== estado) {
            cerrarDatePicker(datePickerAbierto);
        }

        const fechaActual = obtenerFechaDesdeValor(estado.input.value) || new Date();
        estado.anioVisible = fechaActual.getFullYear();
        estado.mesVisible = fechaActual.getMonth();
        estado.panel.hidden = false;
        datePickerAbierto = estado;
        pintarCalendario(estado);
    };

    const seleccionarFecha = (estado, valorFecha) => {
        estado.input.value = valorFecha;
        estado.input.dispatchEvent(new Event("change", { bubbles: true }));
        cerrarDatePicker(estado);
    };

    const manejarClickPanel = (estado, evento) => {
        const accion = evento.target.dataset.datepickerAction;
        const fecha = evento.target.dataset.datepickerDate;

        if (fecha) {
            seleccionarFecha(estado, fecha);
            return;
        }

        if (accion === "anterior") {
            estado.mesVisible -= 1;

            if (estado.mesVisible < 0) {
                estado.mesVisible = 11;
                estado.anioVisible -= 1;
            }

            pintarCalendario(estado);
            return;
        }

        if (accion === "siguiente") {
            estado.mesVisible += 1;

            if (estado.mesVisible > 11) {
                estado.mesVisible = 0;
                estado.anioVisible += 1;
            }

            pintarCalendario(estado);
            return;
        }

        if (accion === "hoy") {
            seleccionarFecha(estado, formatearFechaArgentina(new Date()));
            return;
        }

        if (accion === "limpiar") {
            estado.input.value = "";
            estado.input.dispatchEvent(new Event("change", { bubbles: true }));
            cerrarDatePicker(estado);
        }
    };

    const inicializarInputFechaArgentina = (input) => {
        if (input.dataset.datepickerInicializado === "1") {
            return;
        }

        input.dataset.datepickerInicializado = "1";
        input.autocomplete = "off";

        const estado = construirDatePicker(input);
        const fechaInicial = obtenerFechaDesdeValor(input.value) || new Date();

        estado.anioVisible = fechaInicial.getFullYear();
        estado.mesVisible = fechaInicial.getMonth();

        input.addEventListener("focus", () => abrirDatePicker(estado));
        input.addEventListener("click", () => abrirDatePicker(estado));

        input.addEventListener("input", () => {
            input.value = normalizarEntradaFechaArgentina(input.value);
            abrirDatePicker(estado);
        });

        input.addEventListener("keydown", (evento) => {
            if (evento.key === "Escape") {
                cerrarDatePicker(estado);
            }
        });

        estado.panel.addEventListener("mousedown", (evento) => {
            evento.preventDefault();
        });

        estado.panel.addEventListener("click", (evento) => {
            manejarClickPanel(estado, evento);
        });
    };

    document.addEventListener("click", (evento) => {
        if (
            datePickerAbierto &&
            !datePickerAbierto.contenedor.contains(evento.target)
        ) {
            cerrarDatePicker(datePickerAbierto);
        }
    });

    document.addEventListener("DOMContentLoaded", () => {
        document
            .querySelectorAll(SELECTOR)
            .forEach(inicializarInputFechaArgentina);
    });
})();
