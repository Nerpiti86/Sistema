import sqlite3
import subprocess
import sys
from pathlib import Path


def test_script_auditoria_ventas_detecta_confirmada_sin_asiento(tmp_path):
    """
    Contrato: una venta confirmada no puede quedar sin asiento.

    Este test protege la auditoria de consistencia usada antes de reparar datos.
    """
    db_path = tmp_path / "auditoria.sqlite"
    db = sqlite3.connect(db_path)

    db.executescript(
        """
        CREATE TABLE ventas_comprobantes (
            id INTEGER PRIMARY KEY,
            tipo_comprobante TEXT,
            letra TEXT,
            punto_venta INTEGER,
            numero INTEGER,
            estado TEXT,
            asiento_id INTEGER
        );

        CREATE TABLE asientos_contables (
            id INTEGER PRIMARY KEY,
            ejercicio_id INTEGER,
            numero_asiento INTEGER,
            estado TEXT,
            confirmado_en TEXT
        );

        CREATE TABLE asientos_contables_detalle (
            id INTEGER PRIMARY KEY,
            asiento_id INTEGER,
            debe_centavos INTEGER,
            haber_centavos INTEGER
        );

        CREATE TABLE clientes_cuenta_corriente_movimientos (
            id INTEGER PRIMARY KEY,
            origen_tipo TEXT,
            origen_id INTEGER,
            estado TEXT,
            asiento_id INTEGER
        );

        INSERT INTO ventas_comprobantes (
            id, tipo_comprobante, letra, punto_venta, numero, estado, asiento_id
        )
        VALUES (1, 'FACTURA', 'C', 1, 1, 'CONFIRMADO', NULL);
        """
    )
    db.commit()
    db.close()

    resultado = subprocess.run(
        [
            sys.executable,
            "scripts/auditar_consistencia_ventas.py",
            str(db_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert resultado.returncode == 1
    assert "VENTAS CONFIRMADAS SIN ASIENTO" in resultado.stdout
    assert "Hallazgos: 2" in resultado.stdout


def test_script_auditoria_ventas_sin_hallazgos(tmp_path):
    """
    Contrato: una venta confirmada consistente tiene asiento y cuenta corriente.

    Este test verifica el caso feliz minimo de la auditoria.
    """
    db_path = tmp_path / "auditoria_ok.sqlite"
    db = sqlite3.connect(db_path)

    db.executescript(
        """
        CREATE TABLE ventas_comprobantes (
            id INTEGER PRIMARY KEY,
            tipo_comprobante TEXT,
            letra TEXT,
            punto_venta INTEGER,
            numero INTEGER,
            estado TEXT,
            asiento_id INTEGER
        );

        CREATE TABLE asientos_contables (
            id INTEGER PRIMARY KEY,
            ejercicio_id INTEGER,
            numero_asiento INTEGER,
            estado TEXT,
            confirmado_en TEXT
        );

        CREATE TABLE asientos_contables_detalle (
            id INTEGER PRIMARY KEY,
            asiento_id INTEGER,
            debe_centavos INTEGER,
            haber_centavos INTEGER
        );

        CREATE TABLE clientes_cuenta_corriente_movimientos (
            id INTEGER PRIMARY KEY,
            origen_tipo TEXT,
            origen_id INTEGER,
            estado TEXT,
            asiento_id INTEGER
        );

        INSERT INTO ventas_comprobantes (
            id, tipo_comprobante, letra, punto_venta, numero, estado, asiento_id
        )
        VALUES (1, 'FACTURA', 'C', 1, 1, 'CONFIRMADO', 10);

        INSERT INTO asientos_contables (
            id, ejercicio_id, numero_asiento, estado, confirmado_en
        )
        VALUES (10, 1, 1, 'CONFIRMADO', '2026-01-01 10:00:00');

        INSERT INTO asientos_contables_detalle (
            id, asiento_id, debe_centavos, haber_centavos
        )
        VALUES
            (1, 10, 100000, 0),
            (2, 10, 0, 100000);

        INSERT INTO clientes_cuenta_corriente_movimientos (
            id, origen_tipo, origen_id, estado, asiento_id
        )
        VALUES (1, 'VENTA_COMPROBANTE', 1, 'CONFIRMADO', 10);
        """
    )
    db.commit()
    db.close()

    resultado = subprocess.run(
        [
            sys.executable,
            "scripts/auditar_consistencia_ventas.py",
            str(db_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert resultado.returncode == 0
    assert "Hallazgos: 0" in resultado.stdout
