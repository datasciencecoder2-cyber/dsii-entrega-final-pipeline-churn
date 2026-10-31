"""Ingesta reproducible: API HTTP local demo o GitHub Contents API publica."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import base64
import csv
import io
import json
import os
import threading
import requests

from .config import API_GITHUB, CSV_RAW, DATA_DIR, FIELDS, TIMEOUT, ensure_dirs


def validar_csv(payload: bytes) -> tuple[str, int]:
    """Rechaza entradas vacias, binarios, columnas ausentes o sin registros."""
    try:
        content = payload.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('CSV recibido no es UTF-8') from exc
    reader = csv.DictReader(io.StringIO(content))
    missing = set(FIELDS) - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f'Esquema CSV incompleto: {sorted(missing)}')
    count = sum(1 for _ in reader)
    if count < 30:
        raise ValueError(f'No hay suficientes observaciones para clasificacion: {count}')
    return content, count


class _DemoHandler(BaseHTTPRequestHandler):
    # Las filas provienen del CSV incluido; el consumidor realiza GET HTTP real.
    fixture: Path = DATA_DIR / 'demo_clientes.csv'

    def do_GET(self):
        if self.path != '/api/clientes':
            self.send_error(404, 'Recurso inexistente')
            return
        with self.fixture.open(encoding='utf-8', newline='') as fp:
            rows = list(csv.DictReader(fp))
        raw = json.dumps({'registros': rows, 'fuente': 'SIMULACION'}, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


@contextmanager
def servidor_demo(fixture: Path | None = None):
    class Handler(_DemoHandler):
        pass
    if fixture is not None:
        Handler.fixture = Path(fixture)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/api/clientes'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def descargar_demo() -> bytes:
    with servidor_demo() as url:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        obj = resp.json()
        rows = obj.get('registros')
        if not isinstance(rows, list) or not rows:
            raise ValueError('La API demo no devolvio registros')
        buff = io.StringIO()
        writer = csv.DictWriter(buff, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in FIELDS})
        return buff.getvalue().encode('utf-8')


def descargar_github() -> bytes:
    """GitHub REST Contents entrega base64, o download_url para ficheros grandes."""
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'dsii-pipeline-integrador'}
    token = os.getenv('GITHUB_TOKEN', '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    resp = requests.get(API_GITHUB, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()
    encoded = payload.get('content')
    if payload.get('encoding') == 'base64' and encoded:
        return base64.b64decode(encoded, validate=False)
    raw_url = payload.get('download_url')
    if not raw_url:
        raise ValueError('La API GitHub no proporciono contenido ni download_url')
    raw = requests.get(raw_url, timeout=TIMEOUT, headers={'User-Agent':'dsii-pipeline-integrador'})
    raw.raise_for_status()
    return raw.content


def ingerir(source: str) -> dict:
    ensure_dirs()
    if source == 'demo':
        contenido = descargar_demo()
    elif source == 'github':
        contenido = descargar_github()
    else:
        raise ValueError('Fuente no valida. Opciones: demo, github')
    texto, n = validar_csv(contenido)
    # Escribe solo despues de validar para no sobreescribir el ultimo CSV valido.
    temporal = CSV_RAW.with_suffix('.tmp')
    temporal.write_text(texto, encoding='utf-8', newline='')
    temporal.replace(CSV_RAW)
    return {'origen': source, 'filas_api': n, 'csv': str(CSV_RAW.relative_to(DATA_DIR.parent))}
