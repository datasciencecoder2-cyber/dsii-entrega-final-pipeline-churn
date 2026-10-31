"""ETL real: Polars lazy scan -> limpieza -> DuckDB SQL -> Parquet."""
from pathlib import Path
import polars as pl
import duckdb

from .config import CSV_RAW, PARQUET_CLEAN, PARQUET_FEATURES, FIELDS

CATEGORICAS = [
    'gender', 'Partner', 'Dependents', 'PhoneService', 'MultipleLines',
    'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
    'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
    'PaperlessBilling', 'PaymentMethod'
]


def transformar(raw: Path = CSV_RAW, cleaned: Path = PARQUET_CLEAN,
                features: Path = PARQUET_FEATURES) -> tuple[pl.DataFrame, dict]:
    raw, cleaned, features = Path(raw), Path(cleaned), Path(features)
    if not raw.is_file():
        raise FileNotFoundError(f'No existe CSV de entrada: {raw}')

    # Todas las columnas entran como texto. Cast explicito para evitar inferencias debiles.
    lazy = pl.scan_csv(str(raw), infer_schema=False, null_values=['', ' ', 'NULL'])
    missing = set(FIELDS) - set(lazy.collect_schema().names())
    if missing:
        raise ValueError(f'Columnas necesarias faltantes: {sorted(missing)}')
    lazy = lazy.select([pl.col(x).cast(pl.String).str.strip_chars().alias(x) for x in FIELDS])
    lazy = lazy.with_columns(
        pl.col('SeniorCitizen').cast(pl.Int32, strict=False),
        pl.col('tenure').cast(pl.Int32, strict=False),
        pl.col('MonthlyCharges').cast(pl.Float64, strict=False),
        pl.col('TotalCharges').cast(pl.Float64, strict=False),
        pl.col('Churn').str.to_lowercase().alias('Churn'),
        *[pl.col(c).fill_null('Unknown') for c in CATEGORICAS]
    )
    total_entrada = lazy.select(pl.len()).collect().item()
    lazy = lazy.filter(
        (pl.col('customerID').is_not_null()) & (pl.col('customerID') != '') &
        pl.col('Churn').is_in(['yes', 'no']) &
        (pl.col('tenure').is_not_null()) & (pl.col('tenure') >= 0) &
        (pl.col('MonthlyCharges').is_not_null()) & (pl.col('MonthlyCharges') >= 0) &
        (pl.col('TotalCharges').is_null() | (pl.col('TotalCharges') >= 0))
    )
    valid = lazy.collect()
    # Si un ID tiene versiones diferentes, abortamos: elegir una ocultaria error de datos.
    dedup = {}
    duplicados = 0
    for row in valid.to_dicts():
        customer_id = row['customerID']
        if customer_id in dedup:
            if row != dedup[customer_id]:
                raise ValueError(f'Conflicto de registros para customerID={customer_id}')
            duplicados += 1
        else:
            dedup[customer_id] = row
    if not dedup:
        raise ValueError('Sin registros validos para ML')
    unique = pl.DataFrame(list(dedup.values()), schema=valid.schema)
    cleaned.parent.mkdir(parents=True, exist_ok=True)
    features.parent.mkdir(parents=True, exist_ok=True)
    unique.write_parquet(cleaned, compression='zstd')

    # DuckDB consulta el fichero Parquet directamente sin DB persistente intermedia.
    with duckdb.connect(database=':memory:') as conn:
        conn.read_parquet(str(cleaned)).create_view('clientes_limpios', replace=True)
        resultado = conn.sql("""
            SELECT
                "customerID" AS customer_id,
                CAST("SeniorCitizen" AS INTEGER) AS senior_citizen,
                CAST(tenure AS INTEGER) AS tenure,
                CAST("MonthlyCharges" AS DOUBLE) AS monthly_charges,
                CAST("TotalCharges" AS DOUBLE) AS total_charges,
                CASE WHEN tenure > 0 AND "TotalCharges" IS NOT NULL
                     THEN "TotalCharges" / tenure ELSE NULL END AS avg_monthly_paid,
                "Contract" AS contract,
                "InternetService" AS internet_service,
                "PaymentMethod" AS payment_method,
                "TechSupport" AS tech_support,
                "PaperlessBilling" AS paperless_billing,
                "OnlineSecurity" AS online_security,
                CASE WHEN "Churn" = 'yes' THEN 1 ELSE 0 END AS churn
            FROM clientes_limpios
            ORDER BY customer_id
        """).pl()
    if resultado.height != unique.height or resultado['customer_id'].n_unique() != unique.height:
        raise AssertionError('Inconsistencia de integridad tras procesamiento DuckDB')
    if resultado['churn'].n_unique() != 2:
        raise ValueError('No se pueden entrenar 2 clases: revise la fuente')
    resultado.write_parquet(features, compression='zstd')
    return resultado, {
        'filas_crudas': total_entrada,
        'filas_invalidas': total_entrada - valid.height,
        'duplicados_exactos': duplicados,
        'filas_finales': resultado.height,
        'churn_positivos': int(resultado['churn'].sum()),
        'sin_cargo_total': resultado['total_charges'].null_count(),
        'salida_parquet': str(features.name),
    }
