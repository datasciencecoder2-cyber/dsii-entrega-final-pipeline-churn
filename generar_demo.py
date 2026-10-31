"""Genera fixture SIMULADA, no confundir con muestras reales IBM."""
from src.config import ROOT
from src.demo import generar

if __name__ == '__main__':
    f = ROOT / 'datos' / 'demo_clientes.csv'
    generar(f, n=850, seed=2026)
    print(f'Demo reproducible: {f}')
