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

@bp.post("/ejercicios-contables/<codigo>/coeficientes-inflacion/generar/")
def generar_coeficientes_inflacion_para_ejercicio(codigo):
    """
    Genera o recalcula coeficientes de inflacion del ejercicio contable.

    Esta route no ejecuta SQL directo. La validacion, el calculo entero y la
    persistencia del snapshot quedan delegados al service.
    """
    try:
        generar_coeficientes_inflacion_ejercicio(codigo)
    except ValueError as exc:
        flash(str(exc), "danger")
    else:
        flash("Coeficientes de inflacion generados correctamente.", "success")

    return redirect(
        url_for(
            "contabilidad.ver_detalle_ejercicio_contable",
            codigo=codigo,
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
