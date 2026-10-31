"""Generacion determinista de datos SINTETICOS solo para la prueba offline."""
from pathlib import Path
import csv
import math
import random
from .config import FIELDS


def generar(file: Path, n: int = 850, seed: int = 2026) -> None:
    rnd = random.Random(seed)
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for i in range(n):
            tenure = rnd.randint(0, 72)
            contract = rnd.choices(['Month-to-month','One year','Two year'], weights=[.56,.26,.18])[0]
            internet = rnd.choice(['DSL','Fiber optic','No'])
            tech = rnd.choice(['Yes','No','No internet service'])
            security = rnd.choice(['Yes','No','No internet service'])
            pay = rnd.choice(['Electronic check','Mailed check',
                              'Bank transfer (automatic)','Credit card (automatic)'])
            senior = int(rnd.random()<.17)
            monthly = round(rnd.uniform(20,110), 2)
            total = round(tenure * monthly * rnd.uniform(.94,1.06),2)
            score = (-.95 + 1.15*(contract=='Month-to-month')
                     - .028*tenure + .65*(internet=='Fiber optic')
                     + .35*(pay=='Electronic check')
                     + .35*(tech!='Yes') + .28*(security!='Yes')
                     + .012*(monthly-65) + .28*senior)
            prob = 1/(1+math.exp(-score))
            churn = 'Yes' if rnd.random()<prob else 'No'
            rows = {
                'customerID':f'DEMO-{i:06d}',
                'gender':rnd.choice(['Male','Female']),
                'SeniorCitizen':senior,
                'Partner':rnd.choice(['Yes','No']),
                'Dependents':rnd.choice(['Yes','No']),
                'tenure':tenure,
                'PhoneService':rnd.choice(['Yes','No']),
                'MultipleLines':rnd.choice(['Yes','No','No phone service']),
                'InternetService':internet,
                'OnlineSecurity':security,
                'OnlineBackup':rnd.choice(['Yes','No']),
                'DeviceProtection':rnd.choice(['Yes','No']),
                'TechSupport':tech,
                'StreamingTV':rnd.choice(['Yes','No']),
                'StreamingMovies':rnd.choice(['Yes','No']),
                'Contract':contract,
                'PaperlessBilling':rnd.choice(['Yes','No']),
                'PaymentMethod':pay,
                'MonthlyCharges':monthly,
                'TotalCharges': '' if tenure==0 else total,
                'Churn':churn,
            }
            writer.writerow(rows)
