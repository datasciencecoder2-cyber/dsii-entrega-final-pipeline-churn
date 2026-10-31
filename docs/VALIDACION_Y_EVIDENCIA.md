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

## Estado de verificación del paquete inicial

La generación de archivos, compilación de Python, API HTTP local, mapeo ORM y entrenamiento ML se comprobaron en entorno de autoría. **No estaba disponible Polars ni DuckDB para completar allí la prueba de integración real**; sus pruebas están incluidas y deben correrse luego de instalar dependencias en el equipo final. Esta distinción es esencial antes de presentar un proyecto con 2 intentos de aprobación.

Cuando ejecutes en tu equipo con todas las dependencias, guardá el registro real en `evidencia/salida_final.txt` y subilo al repositorio (no copiar ejemplos inventados).
