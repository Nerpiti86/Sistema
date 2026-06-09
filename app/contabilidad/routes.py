from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.contabilidad.cuentas_contables_service import (
    actualizar_cuenta_contable_desde_formulario,
    crear_cuenta_contable_desde_formulario,
    obtener_contexto_detalle_cuenta_contable,
    obtener_contexto_listado_cuentas_contables,
)

from app.contabilidad.ejercicios_contables_service import (
    actualizar_ejercicio_contable_desde_formulario,
    crear_ejercicio_contable_desde_formulario,
    obtener_contexto_detalle_ejercicio_contable,
    obtener_contexto_listado_ejercicios_contables,
)

bp = Blueprint(
    "contabilidad",
    __name__,
    url_prefix="/contabilidad",
    template_folder="templates",
)


@bp.get("/")
def index():
    return render_template(
        "contabilidad/index.html",
        page_title="Contabilidad",
    )



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



@bp.get("/ejercicios-contables/")
def ver_listado_ejercicios_contables():
    contexto_ejercicios_contables = obtener_contexto_listado_ejercicios_contables()

    return render_template(
        "contabilidad/ejercicios_contables.html",
        page_title="Ejercicios contables",
        **contexto_ejercicios_contables,
    )


@bp.get("/ejercicios-contables/nuevo/")
def ver_formulario_crear_ejercicio_contable():
    """
    Muestra formulario de alta de ejercicios_contables.

    Esta route no ejecuta SQL directo. Solo prepara contexto visual minimo
    para el template de alta.
    """
    return render_template(
        "contabilidad/ejercicios_contables_form.html",
        page_title="Crear ejercicio contable",
        ejercicio_contable_form={
            "codigo": "",
            "nombre": "",
            "fecha_desde": "",
            "fecha_hasta": "",
            "estado": "ABIERTO",
            "fase_cierre": "ABIERTO",
            "activo": False,
            "bloqueado": False,
            "es_primer_ejercicio": False,
            "observaciones_cierre": "",
        },
        estados_ejercicio_contable=("ABIERTO", "CERRADO"),
        fases_cierre_ejercicio_contable=("ABIERTO", "EN_CIERRE", "BLOQUEADO"),
    )

@bp.post("/ejercicios-contables/nuevo/")
def crear_ejercicio_contable():
    """
    Crea un ejercicio contable desde POST y vuelve al listado.

    Esta route no ejecuta SQL directo. La normalizacion queda en service y la
    persistencia queda en repository.
    """
    try:
        crear_ejercicio_contable_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))

    flash("Ejercicio contable creado correctamente.", "success")
    return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))


@bp.get("/ejercicios-contables/<codigo>/editar/")
def ver_formulario_editar_ejercicio_contable(codigo):
    """
    Muestra formulario de edicion de un ejercicio contable.

    Esta route no ejecuta SQL directo. Obtiene el ejercicio desde service y
    renderiza el mismo form que usa el alta, en modo edicion.
    """
    try:
        contexto_detalle = obtener_contexto_detalle_ejercicio_contable(codigo)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))

    ejercicio_contable = contexto_detalle["ejercicio_contable"]

    return render_template(
        "contabilidad/ejercicios_contables_form.html",
        page_title=f"Editar ejercicio contable {ejercicio_contable['codigo']}",
        ejercicio_contable_form={
            "codigo": ejercicio_contable["codigo"],
            "nombre": ejercicio_contable["nombre"],
            "fecha_desde": ejercicio_contable["fecha_desde_argentina"],
            "fecha_hasta": ejercicio_contable["fecha_hasta_argentina"],
            "estado": ejercicio_contable["estado_codigo"],
            "fase_cierre": ejercicio_contable["fase_cierre_codigo"],
            "activo": ejercicio_contable["es_activo"],
            "bloqueado": ejercicio_contable["esta_bloqueado"],
            "es_primer_ejercicio": ejercicio_contable["es_primer_ejercicio_bool"],
            "observaciones_cierre": ejercicio_contable["observaciones_cierre"] or "",
        },
        estados_ejercicio_contable=("ABIERTO", "CERRADO"),
        fases_cierre_ejercicio_contable=("ABIERTO", "EN_CIERRE", "BLOQUEADO"),
        form_section_id="ec-form-editar",
        form_titulo=f"Editar ejercicio contable {ejercicio_contable['codigo']}",
        form_descripcion="Edicion de campos mutables de ejercicios_contables.",
        form_data_action="editar_ejercicio_contable",
        form_action_url=url_for(
            "contabilidad.actualizar_ejercicio_contable",
            codigo=ejercicio_contable["codigo"],
        ),
        form_submit_label="Guardar cambios",
        form_cancelar_url=url_for(
            "contabilidad.ver_detalle_ejercicio_contable",
            codigo=ejercicio_contable["codigo"],
        ),
        codigo_solo_lectura=True,
    )


@bp.post("/ejercicios-contables/<codigo>/editar/")
def actualizar_ejercicio_contable(codigo):
    """
    Actualiza un ejercicio contable y vuelve al detalle.

    Esta route no ejecuta SQL directo. La normalizacion queda en service y la
    persistencia queda en repository.
    """
    try:
        ejercicio_contable_actualizado = actualizar_ejercicio_contable_desde_formulario(
            codigo,
            request.form,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(
            url_for("contabilidad.ver_formulario_editar_ejercicio_contable", codigo=codigo)
        )

    flash("Ejercicio contable actualizado correctamente.", "success")
    return redirect(
        url_for(
            "contabilidad.ver_detalle_ejercicio_contable",
            codigo=ejercicio_contable_actualizado["codigo"],
        )
    )

@bp.get("/ejercicios-contables/<codigo>/")
def ver_detalle_ejercicio_contable(codigo):
    """
    Muestra detalle de un ejercicio contable.

    Esta route no ejecuta SQL directo. Pide contexto al service y renderiza una
    pantalla de solo lectura.
    """
    try:
        contexto_detalle = obtener_contexto_detalle_ejercicio_contable(codigo)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_ejercicios_contables"))

    ejercicio_contable = contexto_detalle["ejercicio_contable"]

    return render_template(
        "contabilidad/ejercicios_contables_detalle.html",
        page_title=f"Ejercicio contable {ejercicio_contable['codigo']}",
        **contexto_detalle,
    )
