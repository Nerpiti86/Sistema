from collections.abc import Callable
from contextlib import nullcontext
from typing import TypeVar

from app.db import get_db

T = TypeVar("T")


def contexto_escritura(db):
    """
    Devuelve contexto de escritura sin commitear si ya hay transaccion activa.

    Permite que repositories sigan funcionando solos, pero no corten una
    transaccion de negocio abierta por un orquestador.
    """
    if db.in_transaction:
        return nullcontext()

    return db


def ejecutar_en_transaccion(operacion: Callable[[], T]) -> T:
    """
    Ejecuta una operacion de negocio como unidad atomica.
    """
    db = get_db()

    if db.in_transaction:
        savepoint = "nerisoft_operacion_negocio"
        db.execute(f"SAVEPOINT {savepoint}")
        try:
            resultado = operacion()
        except Exception:
            db.execute(f"ROLLBACK TO {savepoint}")
            db.execute(f"RELEASE {savepoint}")
            raise

        db.execute(f"RELEASE {savepoint}")
        return resultado

    db.execute("BEGIN")
    try:
        resultado = operacion()
    except Exception:
        db.rollback()
        raise

    db.commit()
    return resultado
