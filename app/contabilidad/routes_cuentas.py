from flask import flash, jsonify, redirect, render_template, request, url_for

from app.contabilidad.asientos_contables_service import (
    crear_asiento_contable_borrador,
    obtener_contexto_detalle_asiento_contable,
    obtener_contexto_listado_asientos_contables,
    obtener_contexto_nuevo_asiento_contable,
    obtener_contexto_nuevo_asiento_contable_desde_formulario,
    preparar_asiento_contable_borrador_desde_formulario,
)
from app.contabilidad.coeficientes_inflacion_service import (
    generar_coeficientes_inflacion_ejercicio,
    guardar_indice_inflacion_desde_formulario,
    obtener_contexto_indices_inflacion,
)
from app.contabilidad.cuentas_contables_service import (
    actualizar_cuenta_contable_desde_formulario,
    crear_cuenta_contable_desde_formulario,
    obtener_disponibilidad_cuenta_contable,
    obtener_contexto_detalle_cuenta_contable,
    obtener_contexto_listado_cuentas_contables,
    obtener_lookup_cuentas_contables_imputables,
)
from app.contabilidad.ejercicios_contables_service import (
    actualizar_ejercicio_contable_desde_formulario,
    crear_ejercicio_contable_desde_formulario,
    obtener_contexto_detalle_ejercicio_contable,
    obtener_contexto_listado_ejercicios_contables,
)
from app.contabilidad.blueprint import bp


@bp.get("/cuentas-contables/")
def ver_listado_cuentas_contables():
    """
    Muestra listado de cuentas contables.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service de cuentas_contables.
    """
    contexto_cuentas_contables = obtener_contexto_listado_cuentas_contables()

    return render_template(
        "contabilidad/cuentas_contables.html",
        page_title="Cuentas contables",
        **contexto_cuentas_contables,
    )


@bp.get("/cuentas-contables/nueva/")
def ver_formulario_nueva_cuenta_contable():
    """
    Muestra formulario de alta de cuentas contables.

    Esta route no ejecuta SQL directo. El POST delega validacion y persistencia
    al service de cuentas_contables.
    """
    return render_template(
        "contabilidad/cuentas_contables_form.html",
        page_title="Nueva cuenta contable",
        modo_formulario="alta",
        cuenta_contable={},
        action_url=url_for("contabilidad.crear_cuenta_contable_nueva"),
    )


@bp.post("/cuentas-contables/nueva/")
def crear_cuenta_contable_nueva():
    """
    Crea una cuenta contable desde formulario.

    Esta route no ejecuta SQL directo. El service normaliza datos de pantalla y
    delega persistencia al repository.
    """
    try:
        cuenta_contable = crear_cuenta_contable_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return (
            render_template(
                "contabilidad/cuentas_contables_form.html",
                page_title="Nueva cuenta contable",
                modo_formulario="alta",
                cuenta_contable=request.form,
                action_url=url_for("contabilidad.crear_cuenta_contable_nueva"),
            ),
            400,
        )

    flash("Cuenta contable creada correctamente.", "success")
    return redirect(
        url_for(
            "contabilidad.ver_listado_cuentas_contables",
            cuenta=cuenta_contable["cuenta"],
        )
    )


@bp.get("/cuentas-contables/<cuenta_contable_codigo>/editar/")
def ver_formulario_editar_cuenta_contable(cuenta_contable_codigo):
    """
    Muestra formulario de edicion de una cuenta contable.

    Esta route no ejecuta SQL directo. Obtiene contexto desde service y
    reutiliza el formulario de cuentas_contables en modo edicion.
    """
    try:
        contexto_detalle = obtener_contexto_detalle_cuenta_contable(
            cuenta_contable_codigo
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_cuentas_contables"))

    cuenta_contable = contexto_detalle["cuenta_contable"]

    return render_template(
        "contabilidad/cuentas_contables_form.html",
        page_title=f"Editar cuenta contable {cuenta_contable['cuenta']}",
        modo_formulario="edicion",
        cuenta_contable=cuenta_contable,
        action_url=url_for(
            "contabilidad.actualizar_cuenta_contable_existente",
            cuenta_contable_codigo=cuenta_contable["cuenta"],
        ),
        form_titulo=f"Editar cuenta contable {cuenta_contable['cuenta']}",
        form_descripcion="Edicion de campos mutables de cuentas_contables.",
        form_data_action="editar_cuenta_contable",
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for(
            "contabilidad.ver_listado_cuentas_contables",
            cuenta=cuenta_contable["cuenta"],
        ),
        cuenta_solo_lectura=True,
    )


@bp.post("/cuentas-contables/<cuenta_contable_codigo>/editar/")
def actualizar_cuenta_contable_existente(cuenta_contable_codigo):
    """
    Actualiza una cuenta contable desde formulario.

    Esta route no ejecuta SQL directo. La normalizacion queda en service y la
    persistencia queda en repository.
    """
    try:
        cuenta_contable = actualizar_cuenta_contable_desde_formulario(
            cuenta_contable_codigo,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        cuenta_contable_form = {
            campo: request.form.get(campo, "")
            for campo in request.form.keys()
        }
        cuenta_contable_form["cuenta"] = cuenta_contable_codigo

        return (
            render_template(
                "contabilidad/cuentas_contables_form.html",
                page_title=f"Editar cuenta contable {cuenta_contable_codigo}",
                modo_formulario="edicion",
                cuenta_contable=cuenta_contable_form,
                action_url=url_for(
                    "contabilidad.actualizar_cuenta_contable_existente",
                    cuenta_contable_codigo=cuenta_contable_codigo,
                ),
                form_titulo=f"Editar cuenta contable {cuenta_contable_codigo}",
                form_descripcion="Edicion de campos mutables de cuentas_contables.",
                form_data_action="editar_cuenta_contable",
                form_submit_label="Guardar cambios",
                form_cancelar_url=url_for(
                    "contabilidad.ver_listado_cuentas_contables",
                    cuenta=cuenta_contable_codigo,
                ),
                cuenta_solo_lectura=True,
            ),
            400,
        )

    flash("Cuenta contable actualizada correctamente.", "success")
    return redirect(
        url_for(
            "contabilidad.ver_listado_cuentas_contables",
            cuenta=cuenta_contable["cuenta"],
        )
    )



@bp.get("/cuentas-contables/disponibilidad/<cuenta_contable_codigo>/")
def validar_disponibilidad_cuenta_contable(cuenta_contable_codigo):
    """
    Devuelve disponibilidad de codigo de cuenta contable para validacion al vuelo.

    Esta route no ejecuta SQL directo. Consulta por service y responde JSON para
    que el formulario de alta informe si la cuenta ya esta ocupada.
    """
    try:
        disponibilidad_cuenta_contable = obtener_disponibilidad_cuenta_contable(
            cuenta_contable_codigo
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "cuenta": cuenta_contable_codigo,
                    "disponible": False,
                    "ocupada": False,
                    "descripcion": "",
                    "mensaje": str(exc),
                }
            ),
            400,
        )

    return jsonify(disponibilidad_cuenta_contable)



@bp.get("/cuentas-contables/imputables/buscar/")
def buscar_cuentas_contables_imputables_json():
    """
    Devuelve cuentas imputables para autocomplete de asientos contables.

    Esta route no ejecuta SQL directo. Consulta al service y responde JSON.
    """
    termino_busqueda = request.args.get("q", "")
    limite = request.args.get("limite", 10)

    try:
        lookup_cuentas = obtener_lookup_cuentas_contables_imputables(
            termino_busqueda,
            limite,
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "q": str(termino_busqueda or "").strip(),
                    "cantidad": 0,
                    "resultados": [],
                    "mensaje": str(exc),
                }
            ),
            400,
        )

    return jsonify(lookup_cuentas)


@bp.get("/cuentas-contables/lookup-sumarizadora/<cuenta_contable_codigo>/")
def buscar_cuenta_contable_para_sumarizadora(cuenta_contable_codigo):
    """
    Devuelve descripcion de cuenta contable para lookup de sumarizadora.

    Esta route no ejecuta SQL directo. Consulta por service y responde JSON
    para completar el campo visual descripcion_sumarizadora.
    """
    try:
        contexto_detalle = obtener_contexto_detalle_cuenta_contable(
            cuenta_contable_codigo
        )
    except ValueError:
        return (
            jsonify(
                {
                    "encontrada": False,
                    "cuenta": cuenta_contable_codigo,
                    "descripcion": "",
                }
            ),
            404,
        )

    cuenta_contable = contexto_detalle["cuenta_contable"]

    return jsonify(
        {
            "encontrada": True,
            "cuenta": cuenta_contable["cuenta"],
            "descripcion": cuenta_contable["descripcion"],
        }
    )
