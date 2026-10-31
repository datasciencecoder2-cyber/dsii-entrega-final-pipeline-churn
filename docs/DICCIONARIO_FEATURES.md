# Diccionario de datos y features

| Columna en SQLite | Tipo | Uso | Tratamiento |
|---|---|---|---|
| customer_id | texto PK | Identificador; **no entra al modelo** | Obligatorio, trim, unicidad |
| senior_citizen | entero (0/1) | Feature demográfica | Cast, imputación posterior si falta |
| tenure | entero >=0 | Antigüedad (meses) | Cast, descarta inválidos |
| monthly_charges | decimal >=0 | Cargo mensual | Cast, descarta inválidos |
| total_charges | decimal nullable | Gasto total registrado | Cast; puede faltar, imputa mediana solo en TRAIN |
| avg_monthly_paid | decimal nullable | Gasto acumulado / meses si tenure > 0 | Cálculo SQL DuckDB; imputa mediana solo en TRAIN |
| contract | texto | Tipo de contrato | Imputación frecuente + OneHot |
| internet_service | texto | Servicio de Internet | Imputación frecuente + OneHot |
| payment_method | texto | Medio de pago | Imputación frecuente + OneHot |
| tech_support | texto | Soporte contratado | Imputación frecuente + OneHot |
| paperless_billing | texto | Facturación digital | Imputación frecuente + OneHot |
| online_security | texto | Seguridad adicional | Imputación frecuente + OneHot |
| churn | entero 0/1 | **TARGET** | Yes=1, No=0; no entra en X |

Se evita usar el identificador como predictora. La imputación de características aprendidas se ajusta únicamente en la porción de entrenamiento para impedir fuga de información del test.
