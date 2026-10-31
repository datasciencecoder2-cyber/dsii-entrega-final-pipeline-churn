"""Persistencia transaccional e idempotente en SQLite via SQLAlchemy 2."""
from pathlib import Path
from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .config import DB_PATH
from .modelos import Base, ClienteChurn


def get_engine(db_path: Path = DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # URL SQLite portable con pathlib y sin credenciales.
    return create_engine(f'sqlite:///{db_path.as_posix()}', future=True)


def guardar(features, db_path: Path = DB_PATH) -> dict:
    engine = get_engine(db_path)
    try:
        Base.metadata.create_all(engine)
        records = features.to_dicts()
        if not records:
            raise ValueError('No hay datos para persistir')
        allowed = {col.name for col in ClienteChurn.__table__.columns}
        if any(set(row) != allowed for row in records):
            raise ValueError('El esquema transformado no coincide con el ORM')
        # Una transaccion: ante cualquier error se revierte todo.
        with Session(engine) as session, session.begin():
            # Se reemplaza el snapshot completo dentro de UNA transaccion;
            # evita mezclar fuentes demo/IBM y permite rollback ante error.
            session.execute(delete(ClienteChurn))
            # Lotes pequenos compatibles incluso con SQLite compilado a 999 variables.
            for offset in range(0, len(records), 50):
                lote = records[offset:offset + 50]
                stmt = sqlite_insert(ClienteChurn).values(lote)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['customer_id'],
                    set_={col: stmt.excluded[col] for col in allowed if col != 'customer_id'}
                )
                session.execute(stmt)
        with Session(engine) as session:
            n = session.scalar(select(func.count()).select_from(ClienteChurn))
        if n != len(records):
            raise AssertionError(f'SQLite tiene {n} filas y se esperaban {len(records)}')
        return {'filas_sqlite': int(n), 'archivo': str(db_path)}
    finally:
        engine.dispose()
