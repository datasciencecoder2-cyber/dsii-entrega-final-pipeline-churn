@echo off
setlocal
cd /d "%~dp0"

echo [1/5] Creando entorno virtual (si hace falta)...
if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
    if errorlevel 1 goto :fail
)

echo [2/5] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [3/5] Ejecutando pipeline INTEGRAL desde cero...
".venv\Scripts\python.exe" main.py --source demo --clean
if errorlevel 1 goto :fail

echo [4/5] Probando inferencia con modelo entrenado...
".venv\Scripts\python.exe" inferir.py
if errorlevel 1 goto :fail

echo [5/5] Ejecutando pruebas automatizadas...
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto :fail

echo.
echo TODO CORRECTO: revise que NO haya tests skipped.
echo Si hay pruebas omitidas, revise requirements.txt y repita.
exit /b 0

:fail
echo.
echo ERROR: no publique la entrega hasta corregir el fallo.
exit /b 1
