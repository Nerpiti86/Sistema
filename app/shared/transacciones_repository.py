from collections.abc import Callable
from contextlib import contextmanager
from itertools import count
from typing import TypeVar

from app.db import get_db

T = TypeVar("T")

_savepoint_counter = count(1)


@contextmanager
def contexto_escritura(db):
    """
    Contexto de escritura para repositories.

    Si no hay transaccion abierta, usa el context manager nativo de sqlite.
    Si ya hay transaccion abierta, usa SAVEPOINT para conservar atomicidad del
    repository sin cortar la transaccion de negocio externa.
    """
    if not db.in_transaction:
        with db:
            yield
        return

    savepoint = f"nerisoft_repository_{next(_savepoint_counter)}"
    db.execute(f"SAVEPOINT {savepoint}")

    try:
        yield
    except Exception:
        db.execute(f"ROLLBACK TO {savepoint}")
        db.execute(f"RELEASE {savepoint}")
        raise

    db.execute(f"RELEASE {savepoint}")


def ejecutar_en_transaccion(operacion: Callable[[], T]) -> T:
    """
    Ejecuta una operacion de negocio como unidad atomica.
    """
    db = get_db()

    if db.in_transaction:
        savepoint = f"nerisoft_operacion_negocio_{next(_savepoint_counter)}"
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
