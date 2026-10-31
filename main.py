"""Punto unico de entrada: API HTTP -> Polars -> DuckDB -> SQLite -> ML."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from src.config import (ROOT, DB_PATH, CSV_RAW, PARQUET_CLEAN, PARQUET_FEATURES,
                        OUTPUT_DIR, MODEL_DIR, ensure_dirs)


def ejecutar(source: str = 'demo', clean: bool = False) -> dict:
    # Carga diferida: mostrar un error claro si faltan dependencias.
    try:
        from src.ingesta import ingerir
        from src.transformaciones import transformar
        from src.persistencia import guardar
        from src.entrenamiento import entrenar_db
    except ImportError as exc:
        raise RuntimeError('Dependencia no disponible. Instale: py -m pip install -r requirements.txt') from exc

    if clean:
        for path in [OUTPUT_DIR, MODEL_DIR, CSV_RAW.parent, PARQUET_CLEAN.parent]:
            if path.exists():
                shutil.rmtree(path)
    ensure_dirs()
    print('01/04 INGESTA — API HTTP')
    ingesta = ingerir(source)
    print(f"  fuente={source}, registros={ingesta['filas_api']}")
    print('02/04 ETL — Polars lazy + DuckDB + Parquet')
    rows, transformacion = transformar()
    print(f"  limpios={transformacion['filas_finales']}, invalidos={transformacion['filas_invalidas']}")
    print('03/04 SQLALCHEMY 2 — Persistencia SQLite')
    persistencia = guardar(rows)
    print(f"  filas_db={persistencia['filas_sqlite']}")
    print('04/04 SCIKIT-LEARN — Pipeline + GridSearchCV')
    metricas = entrenar_db()
    resultado = {'fuente': ingesta, 'etl': transformacion,
                 'persistencia': persistencia, 'modelo': metricas}
    (OUTPUT_DIR / 'reporte_integrador.json').write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False) + '\n', encoding='utf-8'
    )
    for key, val in metricas['metricas_test'].items():
        if key != 'matriz_confusion':
            print(f'  TEST {key}: {val}')
    print('  Matriz confusion:', metricas['metricas_test']['matriz_confusion'])
    print('ENTREGA FINAL — PIPELINE COMPLETO: OK')
    return resultado


def main():
    parser = argparse.ArgumentParser(description='Proyecto integrador DSII: clasificacion Churn')
    parser.add_argument('--source', choices=['demo','github'],
                        default=os.getenv('DATA_SOURCE','demo'),
                        help='demo=API HTTP local simulada; github=API publica IBM')
    parser.add_argument('--clean', action='store_true',
                        help='Eliminar salidas, DB y modelos antes del proceso completo')
    args = parser.parse_args()
    try:
        ejecutar(args.source, args.clean)
    except Exception as exc:
        print(f'PIPELINE FALLIDO: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
