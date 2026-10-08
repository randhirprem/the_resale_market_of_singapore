"""Local read-only API and production frontend server. Python standard library only."""
import argparse
import json
import mimetypes
import traceback
from functools import lru_cache
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from backend.data import ROOT, DEFAULT_DB, connect, dashboard, import_data, metadata, transactions, resale_sources
from backend.context import catalog, records, map_features
from backend.price_models import load_models
from backend.asking import assess


@lru_cache(maxsize=32)
def response_for(route, params):
    with closing(connect()) as con:
        functions = {'/api/meta': metadata, '/api/dashboard': dashboard, '/api/transactions': transactions, '/api/asking': assess}
        function = functions.get(route)
        if function is None:
            raise KeyError('Unknown API route')
        result = function(con) if route == '/api/meta' else function(con, dict(params))
    return json.dumps(result, allow_nan=False).encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path.startswith('/api/'):
            try:
                params = tuple(sorted((k, v[-1]) for k, v in parse_qs(url.query).items()))
                context_routes = {'/api/context/catalog': lambda _: catalog(),
                                  '/api/models': lambda _: load_models(),
                                  '/api/context/records': records, '/api/context/map': map_features}
                if url.path in context_routes:
                    body = json.dumps(context_routes[url.path](dict(params)), allow_nan=False).encode()
                else:
                    body = response_for(url.path, params)
                self.send_body(200, body, 'application/json')
            except ValueError as error:
                self.send_body(400, json.dumps({'error': str(error)}).encode(), 'application/json')
            except KeyError:
                self.send_body(404, b'{"error":"Unknown endpoint"}', 'application/json')
            except Exception:
                traceback.print_exc()
                self.send_body(500, b'{"error":"Unable to read data. Check the server terminal."}', 'application/json')
            return
        base = (ROOT / 'dist').resolve()
        requested = (base / url.path.lstrip('/')).resolve()
        if not requested.is_relative_to(base):
            self.send_error(403)
            return
        if url.path == '/':
            requested = base / 'index.html'
        if not requested.is_file():
            self.send_error(404, 'Run npm run build first' if not base.exists() else 'File not found')
            return
        self.send_body(200, requested.read_bytes(), mimetypes.guess_type(requested)[0] or 'application/octet-stream')

    def send_body(self, status, body, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8000, type=int)
    args = parser.parse_args()
    if not DEFAULT_DB.exists():
        print('Importing the source CSVs for the first launch...', flush=True)
        import_data(resale_sources())
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'HDB Atlas is running at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
