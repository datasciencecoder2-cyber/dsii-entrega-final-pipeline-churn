# Validación y evidencias de la entrega final

## Checklist exigido

| Criterio Coderhouse | Evidencia técnica |
|---|---|
| Integración completa, 35% | `main.py` encadena `ingerir` -> `transformar` -> `guardar` -> `entrenar_db` sin interrupción manual |
| Calidad del código, 22% | Paquete `src/` modular, control de tipos, rechazo de datos incongruentes, errores HTTP, tests |
| Persistencia/portabilidad, 18% | `Mapped`, `mapped_column`, SQLite en transacción, rutas pathlib, `.env.example`, `requirements.txt` |
| Documentación/reproducibilidad, 15% | README con comandos, fuentes, supuestos, diccionario y verificación limpia |
| Evaluación del modelo, 10% | `GridSearchCV`, holdout sin fuga, cuatro métricas + ROC-AUC, matriz y baseline |

## Verificación de una instalación NUEVA

1. Clonar/extraer en carpeta nueva; confirmar que **no** hay `.db`, `.joblib`, CSV o Parquet intermedios.
2. Crear entorno e instalar `requirements.txt` según README.
3. `py main.py --source demo --clean`. Debe imprimir `ENTREGA FINAL — PIPELINE COMPLETO: OK`.
4. `py inferir.py`. Debe imprimir `INFERENCIA: OK`.
5. `py -m unittest discover -s tests -v`. Todas las pruebas deben estar `ok` y **ninguna** `skipped` si instalaste correctamente las dependencias.
6. Repetir el paso 3 **sin** `--clean`: debe conservar la cantidad de filas y no duplicar registros.
7. Opcional, con Internet: `py main.py --source github --clean`; comparar las métricas del dataset IBM con las de la demo y documentar cambios.

## Estado de validación definitiva (31/10/2026)

El proyecto se ejecutó **desde cero en Windows con Python 3.14 y todas las dependencias instaladas** mediante `VALIDAR_TODO.cmd`. Resultado reportado por el estudiante:

- Ingesta mediante API HTTP: **OK**, 850 observaciones sintéticas de demostración.
- Polars lazy + DuckDB + Parquet: **OK**, 850 registros limpios, 0 inválidos.
- SQLAlchemy 2.0 + SQLite: **OK**, 850 filas persistidas.
- Scikit-Learn + GridSearchCV: **OK**. En test: accuracy 0.6412, precision 0.5696, recall 0.625, F1 0.5960 y ROC-AUC 0.6834.
- Inferencia de dos clientes nuevos: **OK**.
- Pruebas automatizadas: **14/14 OK, sin pruebas omitidas** (`Ran 14 tests in 2.828s`).

La evidencia real se conserva en `evidencia/salida_final.txt`. **Las métricas anteriores proceden del modo `demo` sintético: no son métricas de producción.**
