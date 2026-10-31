import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session
from src.config import FEATURES
from src.demo import generar
from src.modelos import Base, ClienteChurn
from src.persistencia import get_engine
from src.entrenamiento import entrenar_desde_frame


class TestPersistenciaML(unittest.TestCase):
    def test_04_orm_declarative_y_tabla(self):
        with tempfile.TemporaryDirectory() as d:
            engine=get_engine(Path(d)/'prueba.db')
            Base.metadata.create_all(engine)
            self.assertIn('clientes_churn',inspect(engine).get_table_names())
            engine.dispose()

    def test_05_entrenamiento_sin_fuga_y_archivos(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'fixture.csv'
            generar(p, 250, 104)
            df = pd.read_csv(p, dtype={'customerID':'string'})
            frame = pd.DataFrame({
                'senior_citizen':df['SeniorCitizen'], 'tenure':df['tenure'],
                'monthly_charges':df['MonthlyCharges'], 'total_charges':df['TotalCharges'],
                'avg_monthly_paid':df['TotalCharges']/df['tenure'].replace(0, float('nan')),
                'contract':df['Contract'], 'internet_service':df['InternetService'],
                'payment_method':df['PaymentMethod'], 'tech_support':df['TechSupport'],
                'paperless_billing':df['PaperlessBilling'], 'online_security':df['OnlineSecurity'],
                'churn':(df['Churn']=='Yes').astype(int)
            })
            r = entrenar_desde_frame(frame, Path(d)/'models', Path(d)/'outputs')
            self.assertEqual(r['train'],200)
            self.assertEqual(r['test'],50)
            self.assertGreaterEqual(r['metricas_test']['f1'],0)
            self.assertLessEqual(r['metricas_test']['f1'],1)
            self.assertTrue((Path(d)/'models'/'churn_pipeline.joblib').exists())
            self.assertTrue((Path(d)/'outputs'/'metricas.json').exists())

    def test_11_pipeline_ignora_categoria_desconocida(self):
        from src.entrenamiento import crear_pipeline
        from src.config import FEATURES
        import numpy as np
        from sklearn.model_selection import train_test_split
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'demo.csv';generar(p,220,101)
            raw=pd.read_csv(p)
            x = pd.DataFrame({
                'senior_citizen':raw.SeniorCitizen,'tenure':raw.tenure,
                'monthly_charges':raw.MonthlyCharges,'total_charges':raw.TotalCharges,
                'avg_monthly_paid':raw.TotalCharges/raw.tenure.replace(0,np.nan),
                'contract':raw.Contract,'internet_service':raw.InternetService,
                'payment_method':raw.PaymentMethod,'tech_support':raw.TechSupport,
                'paperless_billing':raw.PaperlessBilling,'online_security':raw.OnlineSecurity,
            })
            pipe=crear_pipeline()
            pipe.fit(x,(raw.Churn=='Yes').astype(int))
            new=x.head(1).copy()
            new.loc[new.index[0],'contract']='Contrato nunca visto'
            self.assertEqual(len(pipe.predict(new)),1)

    def test_12_mapeo_id_es_pk_y_restricciones(self):
        from sqlalchemy import inspect
        with tempfile.TemporaryDirectory() as d:
            engine=get_engine(Path(d)/'schema.db')
            Base.metadata.create_all(engine)
            schema=inspect(engine)
            pk=schema.get_pk_constraint('clientes_churn')
            self.assertIn('customer_id',pk['constrained_columns'])
            checks=[c['name'] for c in schema.get_check_constraints('clientes_churn')]
            self.assertIn('ck_churn_binario',checks)
            engine.dispose()
