"""Configuracion portatil con rutas ancladas al proyecto, nunca al cwd."""
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DATA_DIR = ROOT / 'datos'
OUTPUT_DIR = ROOT / 'salidas'
MODEL_DIR = ROOT / 'modelos'
DB_PATH = OUTPUT_DIR / 'analytics.db'
CSV_RAW = DATA_DIR / 'raw' / 'telco_ingesta.csv'
PARQUET_CLEAN = DATA_DIR / 'procesados' / 'telco_normalizado.parquet'
PARQUET_FEATURES = DATA_DIR / 'procesados' / 'telco_features.parquet'
API_GITHUB = 'https://api.github.com/repos/IBM/telco-customer-churn-on-icp4d/contents/data/Telco-Customer-Churn.csv'
SOURCE_URL = 'https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv'
TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '25'))

FIELDS = [
    'customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents',
    'tenure', 'PhoneService', 'MultipleLines', 'InternetService',
    'OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport',
    'StreamingTV', 'StreamingMovies', 'Contract', 'PaperlessBilling',
    'PaymentMethod', 'MonthlyCharges', 'TotalCharges', 'Churn'
]

NUMERIC_FEATURES = [
    'senior_citizen', 'tenure', 'monthly_charges',
    'total_charges', 'avg_monthly_paid'
]
CATEGORICAL_FEATURES = [
    'contract', 'internet_service', 'payment_method',
    'tech_support', 'paperless_billing', 'online_security'
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def ensure_dirs():
    for path in [OUTPUT_DIR, MODEL_DIR, CSV_RAW.parent, PARQUET_CLEAN.parent]:
        path.mkdir(parents=True, exist_ok=True)
