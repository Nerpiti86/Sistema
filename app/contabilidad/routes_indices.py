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


@bp.get("/indices-inflacion/")
def ver_indices_inflacion():
    """
    Muestra carga y listado de indices de inflacion.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service de coeficientes_inflacion.
    """
    contexto_indices_inflacion = obtener_contexto_indices_inflacion()

    return render_template(
        "contabilidad/indices_inflacion.html",
        page_title="Indices de inflacion",
        **contexto_indices_inflacion,
    )


@bp.post("/indices-inflacion/")
def guardar_indice_inflacion_mensual():
    """
    Guarda un indice mensual de inflacion desde formulario.

    Esta route no ejecuta SQL directo. La normalizacion de formato argentino y
    la persistencia quedan delegadas al service.
    """
    try:
        indice_inflacion = guardar_indice_inflacion_desde_formulario(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        contexto_indices_inflacion = obtener_contexto_indices_inflacion()
        contexto_indices_inflacion["indice_inflacion_form"] = {
            "periodo": request.form.get("periodo", ""),
            "indice": request.form.get("indice", ""),
        }

        return (
            render_template(
                "contabilidad/indices_inflacion.html",
                page_title="Indices de inflacion",
                **contexto_indices_inflacion,
            ),
            400,
        )

    flash("Indice de inflacion guardado correctamente.", "success")
    return redirect(
        url_for(
            "contabilidad.ver_indices_inflacion",
            periodo=indice_inflacion["periodo_yyyymm"],
        )
    )
