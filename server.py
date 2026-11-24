"""Run with python3 server.py. Only explicit public assets are served."""
import argparse
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from mimetypes import guess_type
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit
import venue

WEB = Path(__file__).parent / 'web'
ASSETS = {'/': 'index.html', '/style.css': 'style.css', '/app.js': 'app.js'}


class Handler(BaseHTTPRequestHandler):
    def reply(self, body, mime):
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ASSETS:
            resource = WEB / ASSETS[path]
            return self.reply(resource.read_bytes(), guess_type(resource)[0])
        with closing(sqlite3.connect(self.server.db_path)) as db:
            if path == '/api/shows':
                payload = venue.shows(db)
            elif (match := re.fullmatch(r'/api/shows/([1-9][0-9]{0,8})/seats', path)):
                show_id = int(match[1])
                if not db.execute('SELECT 1 FROM shows WHERE id=? AND on_sale=1', (show_id,)).fetchone():
                    return self.send_error(404)
                payload = venue.seats(db, show_id)
            else:
                return self.send_error(404)
        self.reply(json.dumps(payload, separators=(',', ':')).encode(), 'application/json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--db', type=Path, default=venue.DB)
    args = parser.parse_args()
    venue.prepare(args.db)
    with ThreadingHTTPServer((args.host, args.port), Handler) as app:
        app.db_path = args.db
        print(f'Serving Meridian Hall on {args.host}:{app.server_port}', flush=True)
        app.serve_forever()
