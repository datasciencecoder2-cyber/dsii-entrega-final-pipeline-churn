# Publicación en GitHub: pasos recomendados

1. Crear repositorio público `dsii-entrega-final-pipeline-churn` (o nombre equivalente). Seleccionar plantilla Python para `.gitignore` **solo si no se sube el incluido**; no crear otro distinto accidentalmente.
2. Descomprimir ZIP; subir al **nivel raíz** del repositorio todos los archivos y subcarpetas que están dentro de `DSII_Entrega_Final_Pipeline_Churn`. GitHub web permite arrastrar la estructura; chequear que `main.py` quede en raíz.
3. Revisar que existan `.gitignore` y `.env.example`. **No** subir `.env`, `analytics.db`, `modelos/` ni `datos/raw/`.
4. Comprobar que README se muestre en la portada y contenga el comando de instalación y ejecución.
5. Validar en Windows con `py -m pip install -r requirements.txt`, `py main.py --source demo --clean`, `py inferir.py`, `py -m unittest discover -s tests -v`.
6. Copiar salida real a `evidencia/salida_final.txt` (sin credenciales ni información privada).
7. Opcional: incorporar cambios por commits separados: `feat: integrar API y ETL`, `feat: persistencia SQLite y modelo`, `test: validar flujo final`, `docs: reproducibilidad y resultados`.
8. En Coderhouse pegar URL pública del repositorio, no el ZIP ni el enlace a Drive. Hacerlo recién después de revisar que toda la cadena corra sin errores y **sin pruebas omitidas**.
