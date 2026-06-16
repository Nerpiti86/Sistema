(() => {
    "use strict";

    const SELECTOR_FECHA = '[data-datepicker="fecha-argentina"]';
    const SELECTOR_PERIODO = '[data-datepicker="periodo-argentino"]';
    const MESES = [
        "ENERO",
        "FEBRERO",
        "MARZO",
        "ABRIL",
        "MAYO",
        "JUNIO",
        "JULIO",
        "AGOSTO",
        "SEPTIEMBRE",
        "OCTUBRE",
        "NOVIEMBRE",
        "DICIEMBRE",
    ];
    const DIAS_SEMANA = ["L", "M", "M", "J", "V", "S", "D"];

    let datePickerAbierto = null;

    const completarDosDigitos = (valor) => String(valor).padStart(2, "0");

    const capitalizar = (valor) => (
        String(valor || "").charAt(0).toUpperCase() +
        String(valor || "").slice(1)
    );

    const formatearFechaArgentina = (fecha) => (
        `${completarDosDigitos(fecha.getDate())}/` +
        `${completarDosDigitos(fecha.getMonth() + 1)}/` +
        `${fecha.getFullYear()}`
    );

    const formatearPeriodoArgentino = (anio, mes) => (
        `${completarDosDigitos(mes + 1)}/${anio}`
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

    const obtenerPeriodoDesdeValor = (valor) => {
        const partes = String(valor || "").trim().match(/^(\d{2})\/(\d{4})$/);

        if (!partes) {
            return null;
        }

        const mes = Number(partes[1]);
        const anio = Number(partes[2]);

        if (mes < 1 || mes > 12) {
            return null;
        }

        return {
            anio,
            mes: mes - 1,
        };
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

    const normalizarEntradaPeriodoArgentino = (valor) => {
        const digitos = String(valor || "").replace(/\D/g, "").slice(0, 6);
        const partes = [];

        if (digitos.length > 0) {
            partes.push(digitos.slice(0, 2));
        }

        if (digitos.length > 2) {
            partes.push(digitos.slice(2, 6));
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

    const crearIcono = (nombreIcono) => {
        const icono = document.createElement("i");
        icono.className = `ti ti-${nombreIcono}`;
        icono.setAttribute("aria-hidden", "true");
        return icono;
    };

    const construirPanelBase = (input, etiquetaPanel, claseGrilla) => {
        const contenedor = document.createElement("div");
        contenedor.className = "ns-date-field";

        input.parentNode.insertBefore(contenedor, input);
        contenedor.appendChild(input);

        const botonIcono = document.createElement("button");
        botonIcono.type = "button";
        botonIcono.className = "ns-date-field__button";
        botonIcono.setAttribute("aria-label", etiquetaPanel);
        botonIcono.appendChild(crearIcono("calendar"));
        contenedor.appendChild(botonIcono);

        const panel = document.createElement("div");
        panel.className = "ns-date-picker";
        panel.hidden = true;
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-label", etiquetaPanel);

        const header = document.createElement("div");
        header.className = "ns-date-picker__header";

        const botonAnterior = crearBoton(String.fromCharCode(8249), "ns-date-picker__nav", "anterior");
        const titulo = document.createElement("p");
        titulo.className = "ns-date-picker__title";
        const botonSiguiente = crearBoton(String.fromCharCode(8250), "ns-date-picker__nav", "siguiente");

        header.appendChild(botonAnterior);
        header.appendChild(titulo);
        header.appendChild(botonSiguiente);

        const grilla = document.createElement("div");
        grilla.className = claseGrilla;

        const footer = document.createElement("div");
        footer.className = "ns-date-picker__footer";

        panel.appendChild(header);
        panel.appendChild(grilla);
        panel.appendChild(footer);
        contenedor.appendChild(panel);

        return {
            contenedor,
            input,
            botonIcono,
            panel,
            titulo,
            grilla,
            footer,
        };
    };

    const construirDatePicker = (input) => {
        const estado = construirPanelBase(
            input,
            "Selector de fecha",
            "ns-date-picker__grid"
        );

        const botonHoy = crearBoton("Hoy", "btn btn-sm btn-outline-primary", "hoy");
        const botonLimpiar = crearBoton(
            "Limpiar",
            "btn btn-sm btn-outline-secondary",
            "limpiar"
        );

        estado.footer.appendChild(botonHoy);
        estado.footer.appendChild(botonLimpiar);

        return estado;
    };

    const construirPeriodoPicker = (input) => {
        const estado = construirPanelBase(
            input,
            "Selector de periodo",
            "ns-date-picker__month-grid"
        );

        estado.panel.classList.add("ns-date-picker--periodo");

        const botonActual = crearBoton(
            "Actual",
            "btn btn-sm btn-outline-primary",
            "actual"
        );
        const botonLimpiar = crearBoton(
            "Limpiar",
            "btn btn-sm btn-outline-secondary",
            "limpiar"
        );

        estado.footer.appendChild(botonActual);
        estado.footer.appendChild(botonLimpiar);

        return estado;
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

    const periodosMismoMes = (periodoA, periodoB) => (
        periodoA &&
        periodoB &&
        periodoA.anio === periodoB.anio &&
        periodoA.mes === periodoB.mes
    );

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

    const pintarPeriodos = (estado) => {
        const periodoSeleccionado = obtenerPeriodoDesdeValor(estado.input.value);
        const hoy = new Date();
        const periodoActual = {
            anio: hoy.getFullYear(),
            mes: hoy.getMonth(),
        };

        estado.titulo.textContent = String(estado.anioVisible);
        estado.grilla.replaceChildren();

        MESES.forEach((mes, indiceMes) => {
            const periodo = {
                anio: estado.anioVisible,
                mes: indiceMes,
            };
            const botonMes = document.createElement("button");
            botonMes.type = "button";
            botonMes.className = "ns-date-picker__month";
            botonMes.textContent = capitalizar(mes);
            botonMes.dataset.datepickerPeriodo = formatearPeriodoArgentino(
                estado.anioVisible,
                indiceMes
            );

            if (periodosMismoMes(periodo, periodoSeleccionado)) {
                botonMes.classList.add("ns-date-picker__month--selected");
            }

            if (periodosMismoMes(periodo, periodoActual)) {
                botonMes.classList.add("ns-date-picker__month--current");
            }

            estado.grilla.appendChild(botonMes);
        });
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

    const abrirPeriodoPicker = (estado) => {
        if (datePickerAbierto && datePickerAbierto !== estado) {
            cerrarDatePicker(datePickerAbierto);
        }

        const periodoActual = obtenerPeriodoDesdeValor(estado.input.value);
        const hoy = new Date();

        estado.anioVisible = periodoActual ? periodoActual.anio : hoy.getFullYear();
        estado.panel.hidden = false;
        datePickerAbierto = estado;
        pintarPeriodos(estado);
    };

    const seleccionarFecha = (estado, valorFecha) => {
        estado.input.value = valorFecha;
        estado.input.dispatchEvent(new Event("change", { bubbles: true }));
        cerrarDatePicker(estado);
    };

    const seleccionarPeriodo = (estado, valorPeriodo) => {
        estado.input.value = valorPeriodo;
        estado.input.dispatchEvent(new Event("change", { bubbles: true }));
        cerrarDatePicker(estado);
    };

    const manejarClickPanelFecha = (estado, evento) => {
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

    const manejarClickPanelPeriodo = (estado, evento) => {
        const accion = evento.target.dataset.datepickerAction;
        const periodo = evento.target.dataset.datepickerPeriodo;

        if (periodo) {
            seleccionarPeriodo(estado, periodo);
            return;
        }

        if (accion === "anterior") {
            estado.anioVisible -= 1;
            pintarPeriodos(estado);
            return;
        }

        if (accion === "siguiente") {
            estado.anioVisible += 1;
            pintarPeriodos(estado);
            return;
        }

        if (accion === "actual") {
            const hoy = new Date();
            seleccionarPeriodo(
                estado,
                formatearPeriodoArgentino(hoy.getFullYear(), hoy.getMonth())
            );
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
        estado.botonIcono.addEventListener("click", () => abrirDatePicker(estado));

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
            manejarClickPanelFecha(estado, evento);
        });
    };

    const inicializarInputPeriodoArgentino = (input) => {
        if (input.dataset.datepickerInicializado === "1") {
            return;
        }

        input.dataset.datepickerInicializado = "1";
        input.autocomplete = "off";

        const estado = construirPeriodoPicker(input);
        const periodoInicial = obtenerPeriodoDesdeValor(input.value);
        const hoy = new Date();

        estado.anioVisible = periodoInicial ? periodoInicial.anio : hoy.getFullYear();

        input.addEventListener("focus", () => abrirPeriodoPicker(estado));
        input.addEventListener("click", () => abrirPeriodoPicker(estado));
        estado.botonIcono.addEventListener("click", () => abrirPeriodoPicker(estado));

        input.addEventListener("input", () => {
            input.value = normalizarEntradaPeriodoArgentino(input.value);
            abrirPeriodoPicker(estado);
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
            manejarClickPanelPeriodo(estado, evento);
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
            .querySelectorAll(SELECTOR_FECHA)
            .forEach(inicializarInputFechaArgentina);

        document
            .querySelectorAll(SELECTOR_PERIODO)
            .forEach(inicializarInputPeriodoArgentino);
    });
})();
