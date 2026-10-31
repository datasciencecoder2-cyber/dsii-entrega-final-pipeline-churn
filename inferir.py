"""Inferencia despues de entrenar: no reentrena ni reimputa manualmente."""
import json
from pathlib import Path
import joblib
import pandas as pd
from src.config import ROOT, MODEL_DIR, FEATURES


def main():
    model_file = MODEL_DIR / 'churn_pipeline.joblib'
    if not model_file.is_file():
        raise FileNotFoundError('Ejecute primero: py main.py --source demo --clean')
    # joblib/pickle solo de artefactos propios y confiables; no descargar modelos extraños.
    pipeline = joblib.load(model_file)
    muestras = json.loads((ROOT / 'datos' / 'ejemplos_inferencia.json').read_text(encoding='utf-8'))
    X = pd.DataFrame(muestras)[FEATURES]
    resultados = pipeline.predict(X)
    proba = pipeline.predict_proba(X)[:,1]
    for n, (categoria, prob) in enumerate(zip(resultados, proba), start=1):
        print(f'Cliente nuevo {n}: churn_predicho={categoria}, probabilidad={prob:.3f}')
    print('INFERENCIA: OK')


if __name__ == '__main__':
    main()
