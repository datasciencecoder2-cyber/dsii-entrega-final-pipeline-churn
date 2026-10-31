import csv
import tempfile
import unittest
from pathlib import Path
import requests
from src.config import FIELDS
from src.demo import generar
from src.ingesta import servidor_demo, validar_csv


class TestDemoAPI(unittest.TestCase):
    def test_01_demo_es_determinista(self):
        with tempfile.TemporaryDirectory() as d:
            x, y = Path(d)/'x.csv', Path(d)/'y.csv'
            generar(x, 100, 8); generar(y, 100, 8)
            self.assertEqual(x.read_bytes(), y.read_bytes())
            self.assertEqual(len(list(csv.DictReader(x.read_text(encoding='utf-8').splitlines()))), 100)

    def test_02_api_http_real_contesta_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'datos.csv'; generar(p, 100, 9)
            with servidor_demo(p) as url:
                r = requests.get(url, timeout=10)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(len(r.json()['registros']), 100)
                self.assertEqual(requests.get(url+'/error',timeout=10).status_code,404)

    def test_03_esquema_csv_validado(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'datos.csv'; generar(p, 100, 9)
            self.assertEqual(validar_csv(p.read_bytes())[1], 100)
            with self.assertRaises(ValueError): validar_csv(b'id,a\n1,2\n')

    def test_09_api_no_acepta_csv_demasiado_corto(self):
        from io import StringIO
        buf=StringIO()
        writer=csv.DictWriter(buf,fieldnames=FIELDS)
        writer.writeheader();writer.writerow({field:'x' for field in FIELDS})
        with self.assertRaisesRegex(ValueError, 'suficientes'):
            validar_csv(buf.getvalue().encode('utf-8'))

    def test_10_fixture_no_tiene_ids_repetidos(self):
        from src.config import ROOT
        path = ROOT / 'datos' / 'demo_clientes.csv'
        records = list(csv.DictReader(path.read_text(encoding='utf-8').splitlines()))
        ids = [rec['customerID'] for rec in records]
        self.assertEqual(len(ids),850)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(set(rec['Churn'] for rec in records),{'Yes','No'})
