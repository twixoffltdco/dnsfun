#!/usr/bin/env python3
"""
OpenAccess DNS — DoH-эндпоинт (RFC 8484).

Принимает DNS wire-format через HTTPS (GET ?dns=<base64url> и POST с
body application/dns-message) и отдаёт ответы того же рабочего резолвера
из dns/resolver.py. Это тот самый endpoint, который клиенты подключают
как «Private DNS» / DoH в браузере / iOS-профиль.

Запуск (например за nginx/caddy, проксирующим /dns-query на 127.0.0.1:8053):
  python3 dns/doh_server.py --port 8053
Тест:
  curl -sH 'content-type: application/dns-message' --data-binary \
       @query.bin http://127.0.0.1:8053/dns-query | dig +short ...
или просто: python3 dns/selftest.py
"""

from __future__ import annotations

import argparse
import base64
import http.server
import socketserver
import struct
import sys
import threading

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import resolver as R  # noqa: E402


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


class DoHHandler(http.server.BaseHTTPRequestHandler):
    server_version = "OpenAccessDNS/1.0"
    protocol_version = "HTTP/1.1"

    def _send_dns(self, resp_bytes: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "application/dns-message")
        self.send_header("Cache-Control", "max-age=60")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        dns_param = q.get("dns", [None])[0]
        if not dns_param:
            self.send_error(400, "missing ?dns= parameter")
            return
        try:
            wire = b64url_decode(dns_param)
        except Exception:
            self.send_error(400, "bad base64url")
            return
        self._send_dns(R.handle_query(wire))

    def do_POST(self):
        ctype = self.headers.get("Content-Type", "")
        if "application/dns-message" not in ctype:
            self.send_error(415, "unsupported media type")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65535:
            self.send_error(400, "bad content length")
            return
        wire = self.rfile.read(length)
        self._send_dns(R.handle_query(wire))

    def do_OPTIONS(self):
        # CORS для браузерного DoH (RFC 8484 §3)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    ap = argparse.ArgumentParser(description="OpenAccess DoH endpoint")
    ap.add_argument("--listen", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8053)
    args = ap.parse_args()
    srv = ThreadingServer((args.listen, args.port), DoHHandler)
    print(f"[openaccess-doh] http://{args.listen}:{args.port}/dns-query")
    sys.stdout.flush()
    srv.serve_forever()


if __name__ == "__main__":
    main()
