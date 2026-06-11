import re
from pathlib import Path

from app import create_app
from app.config import TestConfig
from app.contabilidad.asientos_contables_service import crear_asiento_contable_borrador
from app.db import apply_migrations, get_db


def _insertar_ejercicio_contable_pantalla_para_asientos(db) -> int:
    db.execute(
        """
        INSERT INTO ejercicios_contables (
            codigo,
            nombre,
            fecha_desde,
            fecha_hasta,
            estado,
            activo,
            fase_cierre,
            bloqueado,
            es_primer_ejercicio,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EJ2026",
            "Ejercicio 2026",
            "2026-01-01",
            "2026-12-31",
            "ABIERTO",
            1,
            "ABIERTO",
            0,
            1,
            "2026-01-01 10:00:00",
        ),
    )

    return int(db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def _insertar_cuenta_contable_pantalla_para_asientos(db, cuenta: str) -> str:
    db.execute(
        """
        INSERT INTO cuentas_contables (
            cuenta,
            descripcion,
            saldo_habitual,
            naturaleza,
            imputable,
            monetaria,
            creado_en
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cuenta,
            f"Cuenta pantalla {cuenta}",
            "DEBE",
            "PATRIMONIAL",
            1,
            1,
            "2026-01-01 10:00:00",
        ),
    )

    return cuenta


def test_pantalla_asientos_contables_responde_ok_sin_datos():
    """
    Valida pantalla minima de listado sin asientos cargados.

    El HTML usa IDs cortos y data-* para trazabilidad tecnica:
    tabla SQL, consulta y campo.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/asientos-contables/")

    assert response.status_code == 200
    assert b"Asientos contables" in response.data
    assert b"No hay asientos contables cargados" in response.data
    assert b'id="as-listado"' in response.data
    assert b'id="as-tabla"' in response.data
    assert b'id="as-mensaje-sin-datos"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-query="listar_asientos_contables"' in response.data


def test_pantalla_asientos_contables_muestra_asiento_con_ids_y_formato_argentino():
    """
    Valida fila de asientos_contables con ID corto y fecha argentina.

    La pantalla no muestra fecha ISO cruda ni importes enteros en centavos.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _insertar_ejercicio_contable_pantalla_para_asientos(db)
        cuenta_debe = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.999",
        )
        cuenta_haber = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.998",
        )

        asiento = crear_asiento_contable_borrador(
            {
                "ejercicio_id": ejercicio_id,
                "fecha": "2026-06-10",
                "descripcion": "Asiento pantalla",
            },
            [
                {
                    "cuenta_contable_codigo": cuenta_debe,
                    "nominal_debe_centavos": 100000,
                    "debe_centavos": 100000,
                },
                {
                    "cuenta_contable_codigo": cuenta_haber,
                    "nominal_haber_centavos": 100000,
                    "haber_centavos": 100000,
                },
            ],
        )

        response = client.get("/contabilidad/asientos-contables/")

    assert response.status_code == 200
    assert b"Asiento pantalla" in response.data
    assert f'id="as-row-{asiento["id"]}"'.encode() in response.data
    assert f'data-row-id="{asiento["id"]}"'.encode() in response.data
    assert b"10/06/2026" in response.data
    assert b"2026-06-10" not in response.data
    assert b"Borrador" in response.data
    assert b"ARS/ARS" in response.data
    assert b"1,000000" in response.data
    assert b"1.000,00" in response.data
    assert f"/contabilidad/asientos-contables/{asiento['id']}/".encode() in response.data
    assert f'id="as-detalle-{asiento["id"]}"'.encode() in response.data
    assert b'data-action="ver_detalle_asiento_contable"' in response.data
    html = response.data.decode("utf-8")
    assert re.search(r">\\s*100000\\s*<", html) is None


def test_pantalla_contabilidad_tiene_acceso_corto_a_asientos_contables():
    """
    Valida acceso desde contabilidad con ID corto.

    La trazabilidad de tabla/accion queda en data-table y data-action.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/contabilidad/")

    assert response.status_code == 200
    assert b"Asientos contables" in response.data
    assert b"/contabilidad/asientos-contables/" in response.data
    assert b'id="as-acceso"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-action="ver_listado_asientos_contables"' in response.data


def test_pantalla_detalle_asiento_contable_muestra_cabecera_y_renglones():
    """
    Valida detalle de asiento con cabecera y renglones formateados.

    La route mantiene el contrato de solo lectura: no expone POST ni acciones de
    confirmacion/anulacion en esta etapa.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _insertar_ejercicio_contable_pantalla_para_asientos(db)
        cuenta_debe = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.999",
        )
        cuenta_haber = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.998",
        )

        asiento = crear_asiento_contable_borrador(
            {
                "ejercicio_id": ejercicio_id,
                "fecha": "2026-06-10",
                "descripcion": "Asiento detalle",
            },
            [
                {
                    "cuenta_contable_codigo": cuenta_debe,
                    "descripcion": "Renglon debe",
                    "nominal_debe_centavos": 100000,
                    "debe_centavos": 100000,
                },
                {
                    "cuenta_contable_codigo": cuenta_haber,
                    "descripcion": "Renglon haber",
                    "nominal_haber_centavos": 100000,
                    "haber_centavos": 100000,
                },
            ],
        )

        response = client.get(f"/contabilidad/asientos-contables/{asiento['id']}/")

    assert response.status_code == 200
    assert b"Asiento contable" in response.data
    assert b"Asiento detalle" in response.data
    assert f'id="as-detalle"'.encode() in response.data
    assert f'data-row-id="{asiento["id"]}"'.encode() in response.data
    assert b'id="as-detalle-card"' in response.data
    assert b'id="as-detalle-tabla"' in response.data
    assert b'id="as-detalle-cantidad-renglones"' in response.data
    assert b"10/06/2026" in response.data
    assert b"2026-06-10" not in response.data
    assert b"1.1.01.01.999" in response.data
    assert b"1.1.01.01.998" in response.data
    assert b"Renglon debe" in response.data
    assert b"Renglon haber" in response.data
    assert b"1.000,00" in response.data
    assert b'id="as-volver-listado"' in response.data
    assert b"/contabilidad/asientos-contables/" in response.data


def test_pantalla_detalle_asiento_inexistente_redirige_al_listado():
    """
    Valida manejo de asiento inexistente sin exponer error tecnico.

    La route delega la validacion al service y vuelve al listado.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/asientos-contables/999999/")

    assert response.status_code == 302
    assert "/contabilidad/asientos-contables/" in response.headers["Location"]



def test_pantalla_nuevo_asiento_contable_muestra_formulario_borrador():
    """
    Valida pantalla GET de alta inicial de asiento borrador.

    La pantalla no persiste datos ni expone POST; solo prepara cabecera base
    con IDs cortos y data-* para trazabilidad tecnica.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    assert response.status_code == 200
    assert b"Nuevo asiento contable" in response.data
    assert b'id="as-nuevo-form"' in response.data
    assert b'id="as-form"' in response.data
    assert b'id="as-guardar"' in response.data
    assert b'data-table="asientos_contables"' in response.data
    assert b'data-action="crear_asiento_contable_borrador"' in response.data
    assert b'method="post"' in response.data
    assert b'id="as-ejercicio-id"' in response.data
    assert b'id="as-fecha"' in response.data
    assert b'data-datepicker="fecha-argentina"' in response.data
    assert b'placeholder="DD/MM/AAAA"' in response.data
    assert b'id="as-descripcion-input"' in response.data
    assert b'value="MANUAL"' in response.data
    assert b'value="BORRADOR"' in response.data
    assert b'value="ARS"' in response.data
    assert b'id="as-cotizacion-tipo"' in response.data
    assert b'data-ns-select="normal"' in response.data
    assert b'CIERRE - Cotizacion de cierre' in response.data
    assert b"Ejercicio 2026" in response.data
    assert b"01/01/2026" in response.data
    assert b"31/12/2026" in response.data
    assert b'id="as-guardar"' in response.data
    assert b'type="submit"' in response.data
    assert b'id="as-nuevo-volver"' in response.data
    assert b'id="as-cancelar"' in response.data
    assert b"/contabilidad/asientos-contables/" in response.data


def test_pantalla_nuevo_asiento_contable_sin_ejercicio_activo_informa_contexto():
    """
    Valida manejo visual cuando no hay ejercicio activo para cargar asientos.

    El formulario GET responde sin error tecnico y muestra observacion de
    contexto sin crear registros.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/asientos-contables/nuevo/")

    assert response.status_code == 200
    assert b"Sin ejercicio contable activo" in response.data
    assert b'id="as-nuevo-mensaje-contexto"' in response.data
    assert b'id="as-nuevo-ejercicio-codigo"' in response.data
    assert b'id="as-form"' in response.data
    assert b'id="as-guardar"' in response.data
    assert b"disabled" in response.data


def test_pantalla_asientos_contables_tiene_acceso_a_nuevo_asiento():
    """
    Valida acceso desde listado hacia formulario GET de nuevo asiento.

    El link queda identificado con ID corto y data-action estable.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        response = client.get("/contabilidad/asientos-contables/")

    assert response.status_code == 200
    assert b'id="as-nuevo"' in response.data
    assert b"/contabilidad/asientos-contables/nuevo/" in response.data
    assert b'data-action="ver_formulario_nuevo_asiento_contable"' in response.data



def test_pantalla_nuevo_asiento_contable_muestra_renglones_base():
    """
    Valida renglones base del formulario GET de nuevo asiento.

    La pantalla mantiene persistencia deshabilitada y solo expone campos
    estables para cuenta, descripcion, moneda, cotizacion, debe y haber.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    assert response.status_code == 200
    assert b'id="as-renglones"' in response.data
    assert b'id="as-det-tabla"' in response.data
    assert b'id="as-det-renglones"' in response.data
    assert b'data-role="asiento-renglones"' in response.data
    assert b'id="as-det-row-0"' in response.data
    assert b'id="as-det-row-1"' in response.data
    assert b'data-row-index="0"' in response.data
    assert b'data-row-index="1"' in response.data

    for indice in (0, 1):
        assert f'id="as-det-{indice}-cuenta"'.encode() in response.data
        assert f'id="as-det-{indice}-descripcion"'.encode() in response.data
        assert f'id="as-det-{indice}-moneda"'.encode() in response.data
        assert f'id="as-det-{indice}-cotizacion"'.encode() in response.data
        assert f'id="as-det-{indice}-debe"'.encode() in response.data
        assert f'id="as-det-{indice}-haber"'.encode() in response.data

    assert b'data-table="asientos_contables_detalle"' in response.data
    assert b'data-field="cuenta_contable_codigo"' in response.data
    assert b'data-field="debe_centavos"' in response.data
    assert b'data-field="haber_centavos"' in response.data
    assert b'value="ARS"' in response.data
    assert b'value="1,000000"' in response.data
    assert b'id="as-guardar"' in response.data
    assert b'type="submit"' in response.data



def test_pantalla_nuevo_asiento_contable_separa_totales_de_tabla():
    """
    Valida separacion visual entre tabla de renglones y cards de totales.

    La pantalla mantiene la tabla dentro del bloque Renglones, pero los totales
    Debe/Haber/Diferencia deben tener aire propio respecto de la tabla.
    """
    contenido = Path(
        "app/contabilidad/templates/contabilidad/asientos_contables_nuevo.html"
    ).read_text(encoding="utf-8")

    assert 'id="as-totales"' in contenido
    assert 'class="row g-2 justify-content-end mt-3 pt-2 mb-2"' in contenido


def test_pantalla_post_nuevo_asiento_contable_crea_borrador_y_redirige_detalle():
    """
    Valida POST de nuevo asiento contable.

    La route no ejecuta SQL directo: delega parser, reglas y persistencia al
    service, luego redirige al detalle del borrador creado.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _insertar_ejercicio_contable_pantalla_para_asientos(db)
        cuenta_debe = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.999",
        )
        cuenta_haber = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "4.1.01.01.999",
        )

        response = client.post(
            "/contabilidad/asientos-contables/nuevo/",
            data={
                "ejercicio_id": str(ejercicio_id),
                "fecha": "2026-06-10",
                "descripcion": "Asiento desde POST",
                "tipo": "MANUAL",
                "moneda_origen_codigo": "ARS",
                "moneda_destino_codigo": "ARS",
                "cotizacion_tipo": "CIERRE",
                "detalles[0][cuenta_contable_codigo]": cuenta_debe,
                "detalles[0][descripcion]": "Renglon debe POST",
                "detalles[0][moneda_codigo]": "ARS",
                "detalles[0][cotizacion_1000000]": "1,000000",
                "detalles[0][debe_centavos]": "1.000,00",
                "detalles[0][haber_centavos]": "",
                "detalles[1][cuenta_contable_codigo]": cuenta_haber,
                "detalles[1][descripcion]": "Renglon haber POST",
                "detalles[1][moneda_codigo]": "ARS",
                "detalles[1][cotizacion_1000000]": "1,000000",
                "detalles[1][debe_centavos]": "",
                "detalles[1][haber_centavos]": "1.000,00",
            },
        )

        asiento = db.execute(
            """
            SELECT id, numero_asiento, estado, descripcion
            FROM asientos_contables
            WHERE descripcion = ?
            """,
            ("Asiento desde POST",),
        ).fetchone()

    assert response.status_code == 302
    assert asiento is not None
    assert asiento["estado"] == "BORRADOR"
    assert asiento["numero_asiento"] is None
    assert (
        f"/contabilidad/asientos-contables/{asiento['id']}/"
        in response.headers["Location"]
    )


def test_pantalla_post_nuevo_asiento_contable_fx_calcula_ars_en_backend():
    """
    Valida POST FX desde formulario.

    La route recibe importes nominales por renglon; el service busca cotizacion
    y guarda el equivalente ARS contable sin que la pantalla envie Debe/Haber ARS.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _insertar_ejercicio_contable_pantalla_para_asientos(db)
        cuenta_usd = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "1.1.01.01.999",
        )
        cuenta_capital = _insertar_cuenta_contable_pantalla_para_asientos(
            db,
            "3.1.01.01.999",
        )

        db.execute(
            """
            INSERT INTO monedas_cotizaciones (
                moneda_origen_codigo,
                moneda_destino_codigo,
                fecha,
                tipo,
                cotizacion_1000000,
                fuente,
                creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "USD",
                "ARS",
                "2026-06-10",
                "CIERRE",
                1250500000,
                "Manual test",
                "2026-06-10 10:00:00",
            ),
        )

        response = client.post(
            "/contabilidad/asientos-contables/nuevo/",
            data={
                "ejercicio_id": str(ejercicio_id),
                "fecha": "2026-06-10",
                "descripcion": "Asiento FX desde POST",
                "tipo": "MANUAL",
                "moneda_origen_codigo": "ARS",
                "moneda_destino_codigo": "ARS",
                "cotizacion_tipo": "CIERRE",
                "detalles[0][cuenta_contable_codigo]": cuenta_usd,
                "detalles[0][descripcion]": "Caja USD",
                "detalles[0][moneda_codigo]": "USD",
                "detalles[0][cotizacion_1000000]": "1250,5",
                "detalles[0][debe_centavos]": "100,00",
                "detalles[0][haber_centavos]": "",
                "detalles[1][cuenta_contable_codigo]": cuenta_capital,
                "detalles[1][descripcion]": "Capital ARS",
                "detalles[1][moneda_codigo]": "ARS",
                "detalles[1][debe_centavos]": "",
                "detalles[1][haber_centavos]": "125.050,00",
            },
        )

        asiento = db.execute(
            """
            SELECT id,
                   moneda_origen_codigo,
                   moneda_destino_codigo,
                   cotizacion_1000000
            FROM asientos_contables
            WHERE descripcion = ?
            """,
            ("Asiento FX desde POST",),
        ).fetchone()

        detalles = db.execute(
            """
            SELECT moneda_codigo,
                   cotizacion_1000000,
                   nominal_debe_centavos,
                   nominal_haber_centavos,
                   debe_centavos,
                   haber_centavos
            FROM asientos_contables_detalle
            WHERE asiento_id = ?
            ORDER BY renglon
            """,
            (asiento["id"],),
        ).fetchall()

    assert response.status_code == 302
    assert asiento["moneda_origen_codigo"] == "ARS"
    assert asiento["moneda_destino_codigo"] == "ARS"
    assert asiento["cotizacion_1000000"] == 1000000

    assert detalles[0]["moneda_codigo"] == "USD"
    assert detalles[0]["cotizacion_1000000"] == 1250500000
    assert detalles[0]["nominal_debe_centavos"] == 10000
    assert detalles[0]["debe_centavos"] == 12505000

    assert detalles[1]["moneda_codigo"] == "ARS"
    assert detalles[1]["nominal_haber_centavos"] == 12505000
    assert detalles[1]["haber_centavos"] == 12505000


def test_pantalla_post_nuevo_asiento_contable_con_error_retorna_formulario():
    """
    Valida error de POST sin exponer excepcion tecnica.

    Ante formulario invalido, la route vuelve a renderizar el alta y conserva
    datos ingresados para correccion del usuario.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        ejercicio_id = _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.post(
            "/contabilidad/asientos-contables/nuevo/",
            data={
                "ejercicio_id": str(ejercicio_id),
                "fecha": "",
                "descripcion": "Asiento sin fecha",
                "tipo": "MANUAL",
                "moneda_origen_codigo": "ARS",
                "moneda_destino_codigo": "ARS",
                "cotizacion_tipo": "CIERRE",
                "detalles[0][cuenta_contable_codigo]": "1.1.01.01.999",
                "detalles[0][debe_centavos]": "1.000,00",
            },
        )

    assert response.status_code == 400
    assert b"La fecha del asiento es obligatoria" in response.data
    assert b'id="as-form"' in response.data
    assert b'value="Asiento sin fecha"' in response.data
    assert b'id="as-guardar"' in response.data



def test_pantalla_nuevo_asiento_contable_tooltip_y_columnas_renglones():
    """
    Valida housekeeping visual de cotizacion y columnas de renglones.

    La ayuda de cotizacion no ocupa espacio fijo y la tabla reserva mas ancho
    para descripciones de cuenta/renglon.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    assert response.status_code == 200
    assert b'id="as-cotizacion-ayuda"' in response.data
    assert b'class="badge rounded-pill text-bg-secondary"' in response.data
    assert (
        'title="Define el criterio por defecto para buscar cotización en renglones con moneda distinta de ARS."'.encode("utf-8")
        in response.data
    )
    assert b'id="as-det-col-nombre-cuenta"' in response.data
    assert b'id="as-det-col-debe-nominal"' in response.data
    assert b'id="as-det-col-haber-nominal"' in response.data
    assert b'id="as-det-col-debe-ars"' in response.data
    assert b'id="as-det-col-haber-ars"' in response.data
    assert b'id="as-det-col-moneda"' in response.data
    assert b'style="table-layout: fixed;"' in response.data
    assert b'id="as-det-0-moneda"' in response.data
    assert b'data-role="asiento-moneda-renglon"' in response.data
    assert b'Debe nominal' in response.data
    assert b'Haber nominal' in response.data
    assert b'Debe ARS' in response.data
    assert b'Haber ARS' in response.data



def test_pantalla_nuevo_asiento_contable_expone_lookup_cuentas_imputables():
    """
    Valida contrato HTML para lookup frontend de cuentas imputables.

    El renglon de asiento debe buscar cuentas imputables y completar el nombre
    de cuenta sin mostrar un campo Detalle como columna principal.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'data-lookup="asientos-cuentas-imputables"' in html
    assert 'data-lookup-url="/contabilidad/cuentas-contables/imputables/buscar/"' in html
    assert 'data-lookup-result="as-det-0-cuenta-nombre"' in html
    assert 'id="as-det-0-cuenta-opciones"' in html
    assert 'id="as-det-0-cuenta-nombre"' in html
    assert 'data-field="cuenta_contable_descripcion"' in html
    assert ">Nombre cuenta<" in html
    assert 'name="detalles[0][descripcion]"' in html
    assert 'type="hidden"' in html
    assert "js/asientos_contables_nuevo_lookup_cuentas.js" in html



def test_pantalla_nuevo_asiento_contable_expone_controles_renglones_dinamicos():
    """
    Valida contrato HTML para agregar y quitar renglones.

    La pantalla debe exponer data-hooks estables sin cambiar el POST de
    detalles[n][...] existente.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="as-det-renglones"' in html
    assert 'data-role="asiento-renglones"' in html
    assert 'data-role="asiento-renglon"' in html
    assert 'id="as-det-agregar-renglon"' in html
    assert 'data-action="agregar-renglon"' in html
    assert 'data-action="quitar-renglon"' in html
    assert 'name="detalles[0][cuenta_contable_codigo]"' in html
    assert 'name="detalles[1][cuenta_contable_codigo]"' in html
    assert 'id="as-det-0-cuenta-opciones"' in html
    assert 'id="as-det-1-cuenta-opciones"' in html



def test_pantalla_nuevo_asiento_contable_quitar_renglon_en_columna_accion():
    """
    Valida que quitar renglon quede en columna propia.

    El boton de quitar no debe ocupar espacio debajo de Cuenta; queda al final
    del renglon como accion visual compacta.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="as-det-col-accion"' in html
    assert 'data-field="accion"' in html
    assert 'class="text-center text-nowrap">Acción</th>' in html
    assert 'class="btn btn-outline-danger btn-sm px-2"' in html
    assert 'title="Quitar renglón"' in html
    assert 'id="as-det-renglones" data-role="asiento-renglones">' in html
    assert 'id="as-det-renglones" data-role="asiento-renglones" id=' not in html



def test_pantalla_nuevo_asiento_contable_expone_contador_renglones():
    """
    Valida badge de cantidad de renglones.

    El contador visible debe tener data-hook para que el JS actualice la
    cantidad al agregar o quitar renglones.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="as-renglones-cantidad"' in html
    assert 'data-role="asiento-renglones-cantidad"' in html


def test_pantalla_nuevo_asiento_limpia_html_cuenta_y_nombre_cuenta():
    """
    Valida housekeeping HTML de renglones del nuevo asiento.

    El hidden descripcion conserva el contrato POST junto a Cuenta, mientras
    Nombre cuenta queda como campo visual readonly sin inputs tecnicos mezclados.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200

    inicio_cuenta = html.index('<td data-field="cuenta_contable_codigo">')
    fin_cuenta = html.index("</td>", inicio_cuenta)
    bloque_cuenta = html[inicio_cuenta:fin_cuenta]

    assert 'id="as-det-0-cuenta"' in bloque_cuenta
    assert 'id="as-det-0-descripcion"' in bloque_cuenta
    assert 'name="detalles[0][descripcion]"' in bloque_cuenta
    assert 'type="hidden"' in bloque_cuenta
    assert 'id="as-det-0-cuenta-opciones"' in bloque_cuenta

    inicio_nombre = html.index('<td data-field="cuenta_contable_descripcion">')
    fin_nombre = html.index("</td>", inicio_nombre)
    bloque_nombre = html[inicio_nombre:fin_nombre]

    assert 'id="as-det-0-cuenta-nombre"' in bloque_nombre
    assert 'readonly' in bloque_nombre
    assert 'type="hidden"' not in bloque_nombre
    assert 'name="detalles[0][descripcion]"' not in bloque_nombre

    assert "Agregue o quite renglones según sea necesario." in html
    assert "La persistencia se habilitara en un paso posterior." not in html


def test_pantalla_nuevo_asiento_contable_expone_nominal_y_ars_calculado():
    """
    Valida contrato visual de carga nominal y calculo ARS.

    La carga del usuario queda en Debe/Haber nominal, mientras Debe/Haber ARS
    queda readonly para representar el importe contable sobre el que opera
    contabilidad.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200

    assert 'data-field="nominal_debe_centavos"' in html
    assert 'data-field="nominal_haber_centavos"' in html
    assert 'data-field="debe_ars_centavos"' in html
    assert 'data-field="haber_ars_centavos"' in html

    assert 'id="as-det-0-debe"' in html
    assert 'name="detalles[0][debe_centavos]"' in html
    assert 'data-post-field="debe_centavos"' in html
    assert 'aria-label="Debe nominal del renglón 1"' in html

    assert 'id="as-det-0-haber"' in html
    assert 'name="detalles[0][haber_centavos]"' in html
    assert 'data-post-field="haber_centavos"' in html
    assert 'aria-label="Haber nominal del renglón 1"' in html

    assert 'id="as-det-0-debe-ars"' in html
    assert 'data-role="asiento-debe-ars"' in html
    assert 'aria-label="Debe ARS calculado del renglón 1"' in html

    assert 'id="as-det-0-haber-ars"' in html
    assert 'data-role="asiento-haber-ars"' in html
    assert 'aria-label="Haber ARS calculado del renglón 1"' in html

    assert 'name="detalles[0][debe_ars_centavos]"' not in html
    assert 'name="detalles[0][haber_ars_centavos]"' not in html


def test_pantalla_nuevo_asiento_contable_moneda_por_renglon_editable():
    """
    Valida que la moneda operativa se defina por renglon.

    La cabecera queda fija en ARS como moneda contable, mientras cada renglon
    expone un select editable para moneda nominal.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    assert response.status_code == 200

    assert "Moneda contable" in html
    assert 'id="as-moneda-origen"' in html
    assert 'name="moneda_origen_codigo"' in html
    assert 'value="ARS"' in html

    inicio_moneda = html.index('id="as-det-0-moneda"')
    inicio_td = html.rfind("<td", 0, inicio_moneda)
    fin_td = html.index("</td>", inicio_moneda)
    bloque_moneda = html[inicio_td:fin_td]

    assert "<select" in bloque_moneda
    assert 'data-field="moneda_codigo"' in bloque_moneda
    assert 'data-role="asiento-moneda-renglon"' in bloque_moneda
    assert 'name="detalles[0][moneda_codigo]"' in bloque_moneda
    assert 'value="ARS"' in bloque_moneda
    assert 'value="USD"' in bloque_moneda
    assert 'value="EUR"' in bloque_moneda
    assert "readonly" not in bloque_moneda
    assert "maxlength" not in bloque_moneda

    assert "Cotización por defecto" in html
    assert (
        "Define el criterio por defecto para buscar cotización en renglones "
        "con moneda distinta de ARS."
    ) in html


def test_pantalla_nuevo_asiento_cotizacion_renglon_manual_y_posteable():
    """
    Valida que la cotizacion del renglon se cargue manualmente.

    El formulario envia cotizacion_1000000 para que el service recalcule ARS
    desde nominal sin depender de una cotizacion precargada en otra pantalla.
    """
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        apply_migrations()
        db = get_db()
        _insertar_ejercicio_contable_pantalla_para_asientos(db)

        response = client.get("/contabilidad/asientos-contables/nuevo/")

    html = response.get_data(as_text=True)

    inicio_cotizacion = html.index('id="as-det-0-cotizacion"')
    inicio_td = html.rfind("<td", 0, inicio_cotizacion)
    fin_td = html.index("</td>", inicio_cotizacion)
    bloque_cotizacion = html[inicio_td:fin_td]

    assert response.status_code == 200
    assert 'data-field="cotizacion_1000000"' in bloque_cotizacion
    assert 'inputmode="decimal"' in bloque_cotizacion
    assert 'name="detalles[0][cotizacion_1000000]"' in bloque_cotizacion
    assert 'readonly' not in bloque_cotizacion
