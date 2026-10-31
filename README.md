# Data Science II — Proyecto integrador final

## De la API a un modelo predictivo: abandono de clientes (Churn)

**Problema de negocio:** una empresa de telecomunicaciones necesita identificar clientes que podrían abandonar el servicio. El proyecto estima `Churn` (1 = sí, 0 = no) usando atributos contractuales, facturación y servicios disponibles. El resultado puede orientar **revisiones de retención**, pero **no** se usa para tomar decisiones automáticas sobre personas.

**Arquitectura realmente integrada:**

```text
API HTTP (demo / GitHub Contents API para CSV IBM)
            │ GET con requests + validación de esquema
            ▼
datos/raw/telco_ingesta.csv
            │ pl.scan_csv() + limpieza, tipado, duplicados
            ▼
datos/procesados/telco_normalizado.parquet
            │ DuckDB SQL SELECT leyendo Parquet
            ▼
datos/procesados/telco_features.parquet
            │ SQLAlchemy 2.0 + transacción + SQLite
            ▼
salidas/analytics.db → tabla clientes_churn
            │ consulta ORM (sin CSV secundario)
            ▼
Scikit-Learn Pipeline + ColumnTransformer
            │ split estratificado 80/20 ANTES de fit
            │ GridSearchCV 3-fold sobre train, scoring F1
            ▼
modelos/churn_pipeline.joblib
salidas/metricas.json + predicciones_ejemplo.csv
```

### Fuentes y distinción importante

- **Modo `demo` (por defecto, sin Internet):** 850 observaciones **sintéticas**, generadas de manera determinista. Un servidor HTTP de demostración local expone `/api/clientes` y `requests` consume realmente su JSON vía GET. El objetivo es validar el recorrido entero, incluso sin conectividad. **No son datos IBM ni muestran desempeño real de producción.**
- **Modo `github` (Internet requerido):** `requests` consume la [GitHub Contents REST API](https://docs.github.com/en/rest/repos/contents) que entrega el archivo público [Telco Customer Churn del repositorio IBM](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv). Los registros reales de ejemplo pasan por exactamente las mismas fases. La tasa, número de filas y métricas pueden variar en función del origen.
- El código **no** descarga ni expone información de cuentas personales del usuario. GitHub permite consultas sin token con límites; `GITHUB_TOKEN` en `.env` es **opcional**.

**Atajo para Windows:** ejecutar `VALIDAR_TODO.cmd` desde la carpeta principal crea `.venv` si hace falta, instala dependencias, ejecuta el pipeline limpio, realiza inferencia y corre los tests. Deben quedar todos `ok` y sin `skipped`.

## 1. Requisitos

- **Python 3.12+** (también pensado para Python 3.14 en Windows), pip y conexión a Internet únicamente para descargar dependencias y ejecutar el modo público.
- Git no es obligatorio para ejecutar, pero sí para publicar en el repositorio final.
- `requirements.txt` contiene Polars, DuckDB, SQLAlchemy 2, Scikit-Learn, Pandas, PyArrow, requests y python-dotenv.

**Windows PowerShell** (desde la raíz del repositorio):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**Linux / macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

El `.env` contiene configuración, jamás debe subirse. En el ejemplo, el token queda vacío porque la API es pública. Si no se usa `.env`, el programa usa `demo` por defecto.

## 2. Ejecución completa, desde cero

**Windows** (1 solo comando de ejecución):

```powershell
.\.venv\Scripts\python.exe main.py --source demo --clean
```

**Linux / macOS:**

```bash
.venv/bin/python main.py --source demo --clean
```

Este comando elimina exclusivamente resultados generados dentro del proyecto, vuelve a consultar la API local, transforma con Polars y DuckDB, crea SQLite, lee la base con SQLAlchemy y entrena + evalúa el modelo con `GridSearchCV`. La salida termina en `ENTREGA FINAL — PIPELINE COMPLETO: OK` si todas las etapas pasan.

**Para usar los datos IBM a través de una API pública:**

```powershell
.\.venv\Scripts\python.exe main.py --source github --clean
```

Si GitHub devuelve `403` (límite), `404`, falla la red o cambia su esquema, **el comando falla de manera explícita**; no sustituye silenciosamente datos simulados. Podés seguir probando offline con `--source demo --clean`. En cada ejecución se **reemplaza el snapshot SQLite dentro de una transacción** para no mezclar los dos orígenes.

**Verificar inferencia a clientes nuevos:**

```powershell
.\.venv\Scripts\python.exe inferir.py
```

La inferencia usa el mismo objeto entrenado, incluyendo las imputaciones y OneHotEncoder. Los ejemplos están en `datos/ejemplos_inferencia.json`. **No** ejecutar `joblib.load` con artefactos desconocidos o no confiables.

## 3. Probar y auditar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas verifican: fuente HTTP, reproducibilidad de datos demo, contrato CSV, mapeo ORM 2.0, entrenamiento y métricas, consulta DuckDB/Polars, Parquet, integridad/idempotencia y **test integral desde API HTTP hasta inferencia**. Las pruebas dependientes de Polars y DuckDB requieren todas las dependencias instaladas: si faltan, `unittest` las marca como `skipped`, no como aprobadas.

**Validación de portabilidad:** cloná o copiá el repositorio a otra carpeta, sin copiar `salidas/`, `modelos/` o `datos/raw/`, repetí instalación y ejecutá `main.py --source demo --clean`, luego `inferir.py` y los tests. Las rutas son relativas a la ubicación del archivo, no al directorio desde donde se invoca el comando.

## 4. Evaluación del modelo

- **Tarea:** clasificación supervisada binaria.
- **Variables objetivo:** `Churn`; **variables X:** tenure, cargos, contrato, Internet, soporte, seguridad, modalidad de pago, etc. **`customer_id` nunca se utiliza como feature**.
- **Train/Test:** 80/20, estratificado, semilla 42.
- **Preprocesamiento:** imputación de mediana + escalado (numéricas); imputación frecuente + codificación OneHot de categorías, tolerando valores desconocidos.
- **GridSearchCV:** 3 folds estratificados dentro de entrenamiento; compara `C=[0.1,1.0]` y `class_weight=[None,'balanced']` de regresión logística. Optimiza F1. **El test no interviene en el ajuste.**
- **Métricas:** accuracy, precision, recall, F1, ROC-AUC, matriz de confusión, baseline de clase mayoritaria, score CV y diferencia F1 train/test.

**Dónde ver los resultados numéricos:** al ejecutar, `salidas/metricas.json` contiene la tabla final real de esa corrida. No incluimos métricas ficticias en el README. En churn, **recall** limita el costo de no identificar un futuro abandono (falso negativo), mientras que **precision** evita contactos innecesarios; por eso se reportan ambas y se optimiza F1 como compromiso inicial, no como regla universal. Una tasa alta de acierto por sí sola no demuestra eficacia si el target está desbalanceado.

**Interpretación:** una diferencia grande de F1 entre entrenamiento y prueba sugiere posible sobreajuste; una diferencia pequeña no garantiza generalización ante cambios reales en la población. La muestra pública de IBM no incluye una marca temporal longitudinal para esta tarea, de modo que este holdout aleatorio evalúa el ejemplo **académico**, no deriva una validación temporal de producción. Correlación y asociación predictiva no implican causalidad.

## 5. Estructura del proyecto

```text
.
├── .env.example            # Configuracion sin secretos
├── VALIDAR_TODO.cmd        # Instalacion, E2E y tests con un comando Windows
├── .gitignore              # Excluye DB, cache, env y modelos generados
├── main.py                 # Orquestador extremo a extremo
├── inferir.py              # Prediccion con modelo entrenado
├── generar_demo.py         # Regeneracion opcional de muestra sintetica
├── requirements.txt
├── datos/
│   ├── demo_clientes.csv   # SOLO datos sinteticos reproducibles
│   └── ejemplos_inferencia.json
├── src/
│   ├── config.py           # Rutas y esquema
│   ├── ingesta.py          # requests GET API local/API GitHub
│   ├── demo.py             # Generador de fixture
│   ├── transformaciones.py # Polars y DuckDB
│   ├── modelos.py          # DeclarativeBase, Mapped, mapped_column
│   ├── persistencia.py     # Transaccion de reemplazo de snapshot
│   └── entrenamiento.py   # Pipeline + GridSearchCV + evaluacion
├── tests/                  # unittest + prueba de integracion completa
├── docs/                   # Diccionario, decisiones y validacion
└── evidencia/              # Comprobaciones disponibles al armar el paquete
```

**No se versionan:** bases SQLite, modelos `.joblib`, archivos Parquet/CSV intermedios, tokens, entornos virtuales ni caches. Se generan a partir de `main.py`. Los datos demo sí se versionan porque son pequeños, sintéticos y verificables.

## 6. Limitaciones y uso responsable

- **No** es un sistema productivo de retención: carece de calibración económica, monitoreo de drift, validación temporal e integración de permisos de usuarios reales.
- El CSV público es un dataset de enseñanza; sus variables pueden diferir de una empresa real. Debe auditarse representatividad, posibles sesgos, derechos de uso y frescura antes de aplicarlo a un negocio.
- Los números en `demo` son ejemplos de ingeniería sobre datos **inventados**; no son evidencia de desempeño sobre clientes reales.
- Para decisiones costosas de marketing y retención se requiere política de contacto, evaluación por segmentos, validación externa y análisis de impacto.

**Entrega final:** repositorio público, clonable y autoexplicativo, cuya ingesta alimenta directamente el procesamiento, la persistencia y el entrenamiento. Se recomienda subir los archivos descomprimidos, no el ZIP como archivo único.
