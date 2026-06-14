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


@bp.get("/asientos-contables/")
def ver_listado_asientos_contables():
    """
    Muestra listado inicial de asientos contables.

    Esta route no ejecuta SQL directo. El contexto de pantalla queda delegado
    al service de asientos_contables.
    """
    contexto_asientos_contables = obtener_contexto_listado_asientos_contables()

    return render_template(
        "contabilidad/asientos_contables.html",
        page_title="Asientos contables",
        **contexto_asientos_contables,
    )


@bp.get("/asientos-contables/nuevo/")
def ver_formulario_nuevo_asiento_contable():
    """
    Muestra formulario inicial de nuevo asiento contable borrador.

    Esta route no ejecuta SQL directo. Solo renderiza contexto de pantalla
    preparado por el service; la persistencia se habilitara en otro paso.
    """
    contexto_nuevo = obtener_contexto_nuevo_asiento_contable()
    contexto_nuevo["form_action_url"] = url_for(
        "contabilidad.crear_asiento_contable_nuevo"
    )

    return render_template(
        "contabilidad/asientos_contables_nuevo.html",
        page_title="Nuevo asiento contable",
        **contexto_nuevo,
    )


@bp.post("/asientos-contables/nuevo/")
def crear_asiento_contable_nuevo():
    """
    Crea asiento contable manual en estado borrador desde formulario.

    Esta route no ejecuta SQL directo. El parser, validacion de negocio y
    persistencia quedan delegados al service de asientos contables.
    """
    try:
        datos_asiento, detalles_asiento = (
            preparar_asiento_contable_borrador_desde_formulario(request.form)
        )
        asiento_contable = crear_asiento_contable_borrador(
            datos_asiento,
            detalles_asiento,
        )
    except ValueError as exc:
        flash(str(exc), "danger")
        contexto_nuevo = obtener_contexto_nuevo_asiento_contable_desde_formulario(
            request.form
        )
        contexto_nuevo["form_action_url"] = url_for(
            "contabilidad.crear_asiento_contable_nuevo"
        )

        return (
            render_template(
                "contabilidad/asientos_contables_nuevo.html",
                page_title="Nuevo asiento contable",
                **contexto_nuevo,
            ),
            400,
        )

    flash("Asiento contable borrador creado correctamente.", "success")
    return redirect(
        url_for(
            "contabilidad.ver_detalle_asiento_contable",
            asiento_id=asiento_contable["id"],
        )
    )


@bp.get("/asientos-contables/<int:asiento_id>/")
def ver_detalle_asiento_contable(asiento_id):
    """
    Muestra detalle de un asiento contable.

    Esta route no ejecuta SQL directo. Pide contexto al service y renderiza una
    pantalla de solo lectura.
    """
    try:
        contexto_detalle = obtener_contexto_detalle_asiento_contable(asiento_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("contabilidad.ver_listado_asientos_contables"))

    asiento_contable = contexto_detalle["asiento_contable"]

    return render_template(
        "contabilidad/asientos_contables_detalle.html",
        page_title=f"Asiento contable {asiento_contable['id']}",
        **contexto_detalle,
    )
