"""Entrenamiento sobre SQLite, split antes de fit, GridSearchCV solo en train."""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (DB_PATH, OUTPUT_DIR, MODEL_DIR, NUMERIC_FEATURES,
                     CATEGORICAL_FEATURES, FEATURES)
from .modelos import ClienteChurn
from .persistencia import get_engine


def leer_sqlite(db_path: Path = DB_PATH) -> pd.DataFrame:
    if not Path(db_path).is_file():
        raise FileNotFoundError(f'Primero ejecute el ETL. No hay DB: {db_path}')
    engine = get_engine(db_path)
    try:
        with Session(engine) as session:
            rows = session.scalars(select(ClienteChurn).order_by(ClienteChurn.customer_id)).all()
            data = [{field: getattr(row, field) for field in FEATURES} | {'churn':row.churn}
                    for row in rows]
        return pd.DataFrame(data)
    finally:
        engine.dispose()


def crear_pipeline():
    numeric = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    categorical = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore')),
    ])
    preprocessor = ColumnTransformer([
        ('num', numeric, NUMERIC_FEATURES),
        ('cat', categorical, CATEGORICAL_FEATURES)
    ])
    return Pipeline([
        ('preprocess', preprocessor),
        ('model', LogisticRegression(max_iter=1600, solver='liblinear', random_state=42))
    ])


def metrificar(y_true, y_pred, proba):
    return {
        'accuracy': round(float(accuracy_score(y_true, y_pred)), 4),
        'precision': round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        'recall': round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        'f1': round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        'roc_auc': round(float(roc_auc_score(y_true, proba)), 4),
        'matriz_confusion': confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    }


def entrenar_desde_frame(frame: pd.DataFrame, modelos: Path = MODEL_DIR,
                         salidas: Path = OUTPUT_DIR) -> dict:
    if not set(FEATURES + ['churn']).issubset(frame.columns):
        raise ValueError('Faltan features o target en los datos de SQLite')
    if len(frame) < 100 or frame['churn'].nunique() != 2:
        raise ValueError('Se requieren >=100 observaciones y ambas clases')
    if frame['churn'].value_counts().min() < 12:
        raise ValueError('Clase minoritaria demasiado chica para CV 3-fold')
    X = frame[FEATURES].copy()
    y = frame['churn'].astype(int).copy()
    # Nunca fit previo al split: imputacion, escala, OHE y GridSearchCV dentro de train.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    grid = GridSearchCV(
        estimator=crear_pipeline(),
        param_grid={
            'model__C': [0.1, 1.0],
            'model__class_weight': [None, 'balanced']
        },
        scoring='f1',
        cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
        n_jobs=1,
        refit=True,
        error_score='raise'
    )
    grid.fit(X_train, y_train)
    pipeline = grid.best_estimator_
    p_train = pipeline.predict(X_train)
    p_test = pipeline.predict(X_test)
    proba_train = pipeline.predict_proba(X_train)[:, 1]
    proba_test = pipeline.predict_proba(X_test)[:, 1]
    baseline = DummyClassifier(strategy='most_frequent').fit(X_train, y_train)
    baseline_pred = baseline.predict(X_test)
    train_metrics = metrificar(y_train, p_train, proba_train)
    test_metrics = metrificar(y_test, p_test, proba_test)
    report = {
        'problema': 'Clasificacion binaria de abandono telco (Churn = Yes)',
        'filas': len(frame), 'train': len(X_train), 'test': len(X_test),
        'tasa_churn_train': round(float(y_train.mean()),4),
        'tasa_churn_test': round(float(y_test.mean()),4),
        'criterio_busqueda_cv': 'F1',
        'mejor_score_cv_train': round(float(grid.best_score_), 4),
        'mejores_hiperparametros': grid.best_params_,
        'metricas_train': train_metrics,
        'metricas_test': test_metrics,
        'baseline_test': {
            'accuracy': round(float(accuracy_score(y_test, baseline_pred)),4),
            'f1': round(float(f1_score(y_test, baseline_pred, zero_division=0)),4)
        },
        'gap_f1_train_menos_test': round(train_metrics['f1'] - test_metrics['f1'],4),
        'nota': 'Dataset demostrativo simulado si source=demo. No inferir causalidad. '
                'La evaluacion usa un holdout fijo no visto durante GridSearchCV.'
    }
    modelos.mkdir(parents=True, exist_ok=True)
    salidas.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, modelos / 'churn_pipeline.joblib')
    (salidas / 'metricas.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    pred = X_test.head(12).copy()
    pred['churn_real'] = y_test.head(12).values
    pred['churn_predicho'] = p_test[:12]
    pred['probabilidad_churn'] = np.round(proba_test[:12], 4)
    pred.to_csv(salidas / 'predicciones_ejemplo.csv', index=False)
    return report


def entrenar_db(db_path: Path = DB_PATH) -> dict:
    return entrenar_desde_frame(leer_sqlite(db_path))
