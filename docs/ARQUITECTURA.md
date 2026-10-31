# Arquitectura y decisiones técnicas

## Contrato de datos

La salida de `src/ingesta.py` es un CSV UTF-8 con 21 columnas validadas: esto es el **contrato de entrada** entre API HTTP y procesamiento.

Polars lee `CSV` en modo lazy (`scan_csv`), elimina entradas no válidas, fuerza tipos numéricos, normaliza texto y detecta conflictos de `customerID`: duplicados idénticos se deduplican; discrepancias sobre la misma clave detienen el proceso para evitar un entrenamiento inconsistente.

La salida se escribe como Parquet columnar. DuckDB **lee ese Parquet directamente** para construir una tabla de features (13 columnas) y una variable adicional `avg_monthly_paid`. No se crea una base DuckDB persistente. El conjunto procesado alimenta SQLAlchemy, no se fabrican CSV paralelos desconectados.

## Persistencia

SQLAlchemy 2.0 expone una entidad `ClienteChurn` con restricciones `CHECK`, PK de cliente y tipado declarativo. El snapshot es **reemplazado atómicamente** en SQLite en lotes de 50, para soportar tanto la demo como un origen distinto sin conservar registros antiguos. Una falla dentro de la transacción revierte la carga; reejecutar deja el mismo número de registros para un origen invariable.

## Machine Learning

Una consulta de SQLAlchemy lee la tabla `clientes_churn`; `Churn` se separa como target, `customer_id` queda fuera. **La transformación de los datos para modelado ocurre únicamente dentro de Pipeline**; `GridSearchCV` estima el mejor candidato en los folds de `X_train`. El test permanece reservado hasta el final. Se exporta un artefacto confiable de `joblib`, no para distribuir como código arbitrario.

## Riesgos y límites

Los datos IBM son un ejemplo público archivado y los 850 registros demo son simulados. Los datos de retención no incluyen seguimiento cronológico completo de churn ni auditoría de cohortes. El protocolo random holdout corresponde a una evaluación ilustrativa, no a un despliegue real. El modelo no justifica causalidad ni decisiones de exclusión automática.
