from __future__ import annotations

import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SpaStaticHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        path = self.translate_path(self.path)
        if self.path.startswith('/api') or self.path.startswith('/health'):
            self.send_error(404, 'API requests are served by the backend service')
            return
        if not Path(path).exists() and not Path(path).is_file():
            self.path = '/index.html'
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header('Cache-Control', 'no-cache' if self.path.endswith('index.html') else 'public, max-age=31536000, immutable')
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description='Serve built React SPA with history fallback.')
    parser.add_argument('--host', default=os.environ.get('FRONTEND_HOST', '0.0.0.0'))
    parser.add_argument('--port', type=int, default=int(os.environ.get('FRONTEND_PORT', '5173')))
    parser.add_argument('--directory', default=os.environ.get('FRONTEND_DIST_DIR', 'frontend/dist'))
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    index = root / 'index.html'
    if not index.exists():
        raise SystemExit(f'frontend build not found: {index}. Run `pnpm -C frontend build` first.')

    handler = partial(SpaStaticHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f'serving frontend: http://{args.host}:{args.port} from {root}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
