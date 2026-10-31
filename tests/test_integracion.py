import importlib.util
import tempfile
import unittest
from pathlib import Path
from src.config import ROOT

FULL_STACK = all(importlib.util.find_spec(name) for name in ('polars','duckdb','pyarrow'))


@unittest.skipUnless(FULL_STACK, 'Instale requirements.txt para habilitar integracion Polars/DuckDB')
class TestIntegracion(unittest.TestCase):
    def test_06_etl_real_y_estructura(self):
        from src.transformaciones import transformar
        with tempfile.TemporaryDirectory() as d:
            tmp=Path(d)
            df, rep = transformar(ROOT/'datos'/'demo_clientes.csv', tmp/'a.parquet',tmp/'b.parquet')
            self.assertEqual(df.height,850)
            self.assertEqual(df['customer_id'].n_unique(),850)
            self.assertTrue((tmp/'b.parquet').is_file())
            self.assertEqual(rep['filas_invalidas'],0)

    def test_07_persistencia_idempotente_y_ml_desde_db(self):
        from sqlalchemy import select,func
        from sqlalchemy.orm import Session
        from src.transformaciones import transformar
        from src.persistencia import guardar, get_engine
        from src.entrenamiento import leer_sqlite, entrenar_desde_frame
        from src.modelos import ClienteChurn
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            df,_=transformar(ROOT/'datos'/'demo_clientes.csv',p/'a.parquet',p/'b.parquet')
            guardar(df,p/'test.db')
            guardar(df,p/'test.db')
            # Windows impide eliminar la base temporal si el pool conserva una conexion abierta.
            # Cerrar la Session no cierra el Engine: liberamos explicitamente su pool.
            engine = get_engine(p/'test.db')
            try:
                with Session(engine) as session:
                    self.assertEqual(
                        session.scalar(select(func.count()).select_from(ClienteChurn)), 850
                    )
            finally:
                engine.dispose()
            frame=leer_sqlite(p/'test.db')
            self.assertEqual(len(frame),850)
            r=entrenar_desde_frame(frame, p/'models', p/'results')
            self.assertEqual(r['filas'],850)
            self.assertGreater(r['metricas_test']['f1'],0)

    def test_08_pipeline_api_real_http_etl_bd_y_modelo(self):
        from src.ingesta import servidor_demo, validar_csv
        from src.transformaciones import transformar
        from src.persistencia import guardar
        from src.entrenamiento import entrenar_desde_frame, leer_sqlite
        import requests
        import joblib
        with tempfile.TemporaryDirectory() as d:
            tmp=Path(d)
            with servidor_demo(ROOT/'datos'/'demo_clientes.csv') as url:
                resp=requests.get(url, timeout=15)
                resp.raise_for_status()
                import csv,io
                from src.config import FIELDS
                txt=io.StringIO()
                writer=csv.DictWriter(txt,fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(resp.json()['registros'])
                csvbytes=txt.getvalue().encode('utf-8')
            self.assertEqual(validar_csv(csvbytes)[1],850)
            raw=tmp/'raw.csv';raw.write_bytes(csvbytes)
            processed, q=transformar(raw, tmp/'clean.parquet',tmp/'features.parquet')
            self.assertEqual(q['filas_finales'],850)
            rep=guardar(processed, tmp/'final.db')
            self.assertEqual(rep['filas_sqlite'],850)
            fr=leer_sqlite(tmp/'final.db')
            metrics=entrenar_desde_frame(fr,tmp/'models',tmp/'outputs')
            model=joblib.load(tmp/'models'/'churn_pipeline.joblib')
            self.assertEqual(len(model.predict(fr.drop(columns='churn').head(3))),3)
            self.assertEqual(metrics['test'],170)

    def test_13_conflicto_de_id_no_se_oculta(self):
        from src.transformaciones import transformar
        import csv
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);src=ROOT/'datos'/'demo_clientes.csv'
            rows=list(csv.DictReader(src.read_text(encoding='utf-8').splitlines()))
            conflict=rows[0].copy();conflict['MonthlyCharges']='999.99'
            rows.append(conflict)
            inp=p/'conflict.csv'
            with inp.open('w',newline='',encoding='utf-8') as fh:
                writer=csv.DictWriter(fh,fieldnames=rows[0].keys())
                writer.writeheader();writer.writerows(rows)
            with self.assertRaisesRegex(ValueError,'Conflicto'):
                transformar(inp,p/'c.parquet',p/'f.parquet')

    def test_14_cambio_de_fuente_no_contamina_sqlite(self):
        from src.transformaciones import transformar
        from src.persistencia import guardar
        from src.demo import generar
        with tempfile.TemporaryDirectory() as d:
            tmp=Path(d)
            df,_=transformar(ROOT/'datos'/'demo_clientes.csv',tmp/'a.parquet',tmp/'b.parquet')
            guardar(df,tmp/'source.db')
            generador=tmp/'other.csv';generar(generador,150,123)
            new,_=transformar(generador,tmp/'a2.parquet',tmp/'b2.parquet')
            report=guardar(new,tmp/'source.db')
            self.assertEqual(report['filas_sqlite'],150)
