import sqlite3
import sys
from pathlib import Path


def conectar(db_path: str) -> sqlite3.Connection:
    conexion = sqlite3.connect(db_path)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def ejecutar_consulta(db: sqlite3.Connection, titulo: str, sql: str) -> int:
    filas = db.execute(sql).fetchall()

    print()
    print("=" * 80)
    print(titulo)
    print("=" * 80)

    if not filas:
        print("OK")
        return 0

    for fila in filas:
        print(dict(fila))

    return len(filas)


def auditar(db_path: str) -> int:
    if not Path(db_path).exists():
        print(f"ERROR: no existe la base indicada: {db_path}")
        return 2

    db = conectar(db_path)

    total_hallazgos = 0

    total_hallazgos += ejecutar_consulta(
        db,
        "VENTAS CONFIRMADAS SIN ASIENTO",
        """
        SELECT id, tipo_comprobante, letra, punto_venta, numero, estado, asiento_id
        FROM ventas_comprobantes
        WHERE estado = 'CONFIRMADO'
          AND asiento_id IS NULL
        ORDER BY id
        """,
    )

    total_hallazgos += ejecutar_consulta(
        db,
        "VENTAS CONFIRMADAS CON ASIENTO INEXISTENTE",
        """
        SELECT vc.id, vc.tipo_comprobante, vc.letra, vc.punto_venta, vc.numero, vc.asiento_id
        FROM ventas_comprobantes vc
        LEFT JOIN asientos_contables ac ON ac.id = vc.asiento_id
        WHERE vc.estado = 'CONFIRMADO'
          AND vc.asiento_id IS NOT NULL
          AND ac.id IS NULL
        ORDER BY vc.id
        """,
    )

    total_hallazgos += ejecutar_consulta(
        db,
        "VENTAS CONFIRMADAS CON ASIENTO NO CONFIRMADO O SIN NUMERO",
        """
        SELECT
            vc.id AS venta_id,
            vc.tipo_comprobante,
            vc.letra,
            vc.punto_venta,
            vc.numero,
            vc.asiento_id,
            ac.estado AS asiento_estado,
            ac.numero_asiento,
            ac.confirmado_en
        FROM ventas_comprobantes vc
        JOIN asientos_contables ac ON ac.id = vc.asiento_id
        WHERE vc.estado = 'CONFIRMADO'
          AND (
              ac.estado <> 'CONFIRMADO'
              OR ac.numero_asiento IS NULL
              OR ac.confirmado_en IS NULL
          )
        ORDER BY vc.id
        """,
    )

    total_hallazgos += ejecutar_consulta(
        db,
        "VENTAS CONFIRMADAS SIN MOVIMIENTO DE CUENTA CORRIENTE",
        """
        SELECT vc.id, vc.tipo_comprobante, vc.letra, vc.punto_venta, vc.numero, vc.asiento_id
        FROM ventas_comprobantes vc
        LEFT JOIN clientes_cuenta_corriente_movimientos ccm
          ON ccm.origen_tipo = 'VENTA_COMPROBANTE'
         AND ccm.origen_id = vc.id
         AND ccm.estado = 'CONFIRMADO'
        WHERE vc.estado = 'CONFIRMADO'
          AND ccm.id IS NULL
        ORDER BY vc.id
        """,
    )

    total_hallazgos += ejecutar_consulta(
        db,
        "VENTAS CONFIRMADAS CON MAS DE UN MOVIMIENTO DE CUENTA CORRIENTE",
        """
        SELECT
            vc.id,
            vc.tipo_comprobante,
            vc.letra,
            vc.punto_venta,
            vc.numero,
            COUNT(ccm.id) AS cantidad_movimientos
        FROM ventas_comprobantes vc
        JOIN clientes_cuenta_corriente_movimientos ccm
          ON ccm.origen_tipo = 'VENTA_COMPROBANTE'
         AND ccm.origen_id = vc.id
         AND ccm.estado = 'CONFIRMADO'
        WHERE vc.estado = 'CONFIRMADO'
        GROUP BY vc.id
        HAVING COUNT(ccm.id) <> 1
        ORDER BY vc.id
        """,
    )

    total_hallazgos += ejecutar_consulta(
        db,
        "MOVIMIENTOS DE CUENTA CORRIENTE DE VENTA SIN ASIENTO O CON ASIENTO DISTINTO",
        """
        SELECT
            ccm.id AS movimiento_id,
            ccm.origen_id AS venta_id,
            ccm.asiento_id AS movimiento_asiento_id,
            vc.asiento_id AS venta_asiento_id
        FROM clientes_cuenta_corriente_movimientos ccm
        JOIN ventas_comprobantes vc ON vc.id = ccm.origen_id
        WHERE ccm.origen_tipo = 'VENTA_COMPROBANTE'
          AND ccm.estado = 'CONFIRMADO'
          AND (
              ccm.asiento_id IS NULL
              OR vc.asiento_id IS NULL
              OR ccm.asiento_id <> vc.asiento_id
          )
        ORDER BY ccm.id
        """,
    )

    total_hallazgos += ejecutar_consulta(
        db,
        "ASIENTOS DESBALANCEADOS",
        """
        SELECT
            ac.id AS asiento_id,
            ac.ejercicio_id,
            ac.numero_asiento,
            ac.estado,
            SUM(acd.debe_centavos) AS total_debe,
            SUM(acd.haber_centavos) AS total_haber
        FROM asientos_contables ac
        JOIN asientos_contables_detalle acd ON acd.asiento_id = ac.id
        GROUP BY ac.id
        HAVING SUM(acd.debe_centavos) <> SUM(acd.haber_centavos)
        ORDER BY ac.id
        """,
    )

    print()
    print("=" * 80)
    print("RESULTADO")
    print("=" * 80)
    print(f"Hallazgos: {total_hallazgos}")

    return 1 if total_hallazgos else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python scripts/auditar_consistencia_ventas.py RUTA_BASE.sqlite")
        sys.exit(2)

    sys.exit(auditar(sys.argv[1]))
