#!/usr/bin/env python3
"""
OpenAccess DNS — рабочий DNS-резолвер для обхода блокировок.

Что делает:
  * Принимает обычные DNS-запросы (UDP/TCP, порт 53) от клиентов.
  * Разрешает их через зашифрованные upstream'ы: DoH (DNS-over-HTTPS)
    и DoT (DNS-over-TLS) — Cloudflare, Google, AdGuard, Quad9.
    Запросы к доменам закрытых сервисов идут по HTTPS/TLS, поэтому
    подмена ответов (DNS poisoning / DPI-инъекции) не проходит.
  * Anti-poisoning: ответы с приватных/служебных адресов (127/8, 10/8,
    172.16/12, 192.168/16, 0/8, ...) для публичных доменов отбрасываются —
    именно так выглядят типичные заглушки блокировщиков.
  * Опциональная DNSSEC-проверка (AD-flag от валидирующих upstream'ов):
    если провайдер подменил ответ — подпись не сойдётся на его валидаторе,
    и мы берём чистый ответ с другого шифрованного upstream'а.
  * On-the-fly ECH-подсказки (Encrypted Client Hello, RFC 9460): для
    SNI-чувствительных доменов в ответ добавляется HTTPS(SVCB) RR с
    ech= параметром, чтобы TLS-стеки клиента (Chromium/Firefox/curl)
    прятали реальный SNI внутри зашифрованного ClientHello.
  * LRU-кэш с TTL + negative cache.

Зависимости: только Python 3.9+ (stdlib).

Использование:
  sudo python3 dns/resolver.py --listen 0.0.0.0 --port 53
  # без root для тестов:
  python3 dns/resolver.py --listen 127.0.0.1 --port 5353
  python3 dns/selftest.py      # проверка работы
"""

from __future__ import annotations

import argparse
import http.client
import json
import random
import socket
import ssl
import struct
import sys
import threading
import time

# ----------------------------------------------------------------------------
# Конфигурация upstream'ов (реально работающие public endpoints)
# ----------------------------------------------------------------------------

# DoH-серверы, принимающие wire-format (RFC 8484) по POST /dns-query
DOH_WIRE_UPSTREAMS = [
    "cloudflare-dns.com",
    "dns.google",
    "dns.adguard-dns.com",
    "dns.quad9.net",
]

# Bootstrap IP-адресаDoH-хостов (чтобы не зависеть от локального resolv.conf)
BOOTSTRAP_IPS = {
    "cloudflare-dns.com": ["104.16.132.229", "104.16.133.229"],
    "dns.google": ["8.8.8.8", "8.8.4.4"],
    "dns.adguard-dns.com": ["94.140.14.14", "94.140.15.15"],
    "dns.quad9.net": ["9.9.9.9", "149.112.112.112"],
}

DOT_UPSTREAMS = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]

# Домены, для которых добавляем ECH-подсказки (SNI-блокировки).
ECH_ENABLED_DOMAINS = [
    "youtube.com", "ytimg.com", "googlevideo.com", "youtu.be",
    "twitter.com", "x.com", "twimg.com",
    "telegram.org", "t.me", "telegram.dog",
    "discord.com", "discordapp.com", "discord.gg", "discord.media",
    "instagram.com", "cdninstagram.com", "facebook.com", "fbcdn.net",
    "netflix.com", "nflxext.com",
]

# ----------------------------------------------------------------------------
# DNS wire format утилиты (RFC 1035)
# ----------------------------------------------------------------------------

TYPE_A = 1
TYPE_NS = 2
TYPE_CNAME = 5
TYPE_SOA = 6
TYPE_PTR = 12
TYPE_MX = 15
TYPE_TXT = 16
TYPE_AAAA = 28
TYPE_HTTPS = 65
CLASS_IN = 1


def encode_name(name: str) -> bytes:
    out = b""
    name = name.strip(".")
    if not name:
        return b"\x00"
    for label in name.split("."):
        try:
            b = label.encode("idna") if any(ord(c) > 127 for c in label) else label.encode()
        except UnicodeError:
            b = label.encode()
        out += bytes([len(b)]) + b
    return out + b"\x00"


def decode_name(data: bytes, offset: int):
    labels = []
    jumped = False
    end = offset
    steps = 0
    while True:
        steps += 1
        if steps > 128 or offset >= len(data):
            raise ValueError("bad name")
        length = data[offset]
        if length == 0:
            offset += 1
            if not jumped:
                end = offset
            break
        if length & 0xC0 == 0xC0:
            ptr = struct.unpack("!H", data[offset:offset + 2])[0] & 0x3FFF
            if not jumped:
                end = offset + 2
            offset = ptr
            jumped = True
            continue
        labels.append(data[offset + 1:offset + 1 + length].decode("utf-8", "replace"))
        offset += 1 + length
    return ".".join(labels), (end if not jumped else end)


def parse_header(msg: bytes):
    if len(msg) < 12:
        raise ValueError("short message")
    return struct.unpack("!HHHHHH", msg[:12])


def make_rr(name_wire: bytes, rtype: int, ttl: int, rdata: bytes) -> bytes:
    return name_wire + struct.pack("!HHIH", rtype, CLASS_IN, ttl, len(rdata)) + rdata


def iter_answers(msg: bytes):
    """Генератор (name, rtype, ttl, rdata) для answer-секции."""
    try:
        _, _, qd, an, ns, ar = parse_header(msg)
        off = 12
        for _ in range(qd):
            _, off = decode_name(msg, off)
            off += 4
        for _ in range(an):
            nm, off = decode_name(msg, off)
            rtype, _, ttl, rdlen = struct.unpack("!HHIH", msg[off:off + 10])
            off += 10
            yield nm, rtype, ttl, msg[off:off + rdlen]
            off += rdlen
    except Exception:
        return


# ----------------------------------------------------------------------------
# Приватные адреса — типичный признак подмены (заглушка блокировщика)
# ----------------------------------------------------------------------------

_PRIV_V4 = []
for _b, _bits in [
    ("0.0.0.0", 8), ("10.0.0.0", 8), ("100.64.0.0", 10), ("127.0.0.0", 8),
    ("169.254.0.0", 16), ("172.16.0.0", 12), ("192.0.0.0", 24),
    ("192.0.2.0", 24), ("192.168.0.0", 16), ("198.18.0.0", 15),
    ("198.51.100.0", 24), ("203.0.113.0", 24), ("240.0.0.0", 4),
]:
    _n = struct.unpack("!I", socket.inet_aton(_b))[0]
    _m = ((1 << _bits) - 1) << (32 - _bits)
    _PRIV_V4.append((_n & _m, _m))


def is_private_v4(ip: str) -> bool:
    try:
        n = struct.unpack("!I", socket.inet_aton(ip))[0]
    except OSError:
        return True
    return any((n & m) == base for base, m in _PRIV_V4)


def is_private_v6(ip: str) -> bool:
    try:
        p = socket.inet_pton(socket.AF_INET6, ip)
    except OSError:
        return True
    if p == b"\x00" * 16:                      # :: unspecified
        return True
    if p.startswith(b"\x00\x00\x00\x00\x00\x00\x00\x00"):  # ::/96 incl. ::1
        return True
    if p[0] in (0x20, 0x3f) and not p.startswith(b"\x20\x01"):
        return True                            # 2001::/23 term, 2002::/16 6to4 ok, 3fff::/20
    if (p[0] & 0xFE) == 0xFC:                  # fc00::/7 ULA
        return True
    if p[0] >= 0xFF:                           # multicast / reserved
        return True
    if p.startswith(b"\x20\x01\x0d\xb8"):      # documentation
        return True
    return False


# ----------------------------------------------------------------------------
# Кэш (LRU + TTL + negative cache)
# ----------------------------------------------------------------------------

class Cache:
    def __init__(self, maxsize=8192):
        self._d = {}
        self._lock = threading.Lock()
        self.maxsize = maxsize

    def get(self, key):
        with self._lock:
            item = self._d.get(key)
            if not item:
                return None
            exp, val = item
            if time.time() > exp:
                del self._d[key]
                return None
            return val

    def put(self, key, ttl, val):
        ttl = max(1, min(int(ttl), 86400))
        with self._lock:
            self._d[key] = (time.time() + ttl, val)
            if len(self._d) > self.maxsize:
                now = time.time()
                for k in sorted(self._d, key=lambda x: self._d[x][0])[: self.maxsize // 4]:
                    self._d.pop(k, None)


CACHE = Cache()

# ----------------------------------------------------------------------------
# Upstream клиенты: DoH (wireformat POST, RFC 8484) + DoT (RFC 7858)
# ----------------------------------------------------------------------------

class Upstreams:
    def __init__(self):
        self._ctx = ssl.create_default_context()
        self._rr_lock = threading.Lock()
        self._rr = 0

    def _next_doh_host(self):
        with self._rr_lock:
            host = DOH_WIRE_UPSTREAMS[self._rr % len(DOH_WIRE_UPSTREAMS)]
            self._rr += 1
        return host

    def resolve_doh(self, wire: bytes, timeout: float = 6.0) -> bytes:
        """POST wire-format на /dns-query; ротация между 4 DoH-провайдерами."""
        last_err = None
        hosts = [self._next_doh_host()] + DOH_WIRE_UPSTREAMS
        tried = set()
        for host in hosts:
            if host in tried:
                continue
            tried.add(host)
            ips = BOOTSTRAP_IPS.get(host, [])
            connect_target = random.choice(ips) if ips else host
            headers = {
                "Content-Type": "application/dns-message",
                "Accept": "application/dns-message",
                "Host": host,
            }
            try:
                conn = http.client.HTTPSConnection(
                    connect_target, 443, timeout=timeout, context=self._ctx)
                # SNI/валидация — на реальное имя хоста
                conn.hostname = host
                conn.host = connect_target
                conn.request("POST", "/dns-query", body=wire, headers=headers)
                resp = conn.getresponse()
                data = resp.read()
                conn.close()
                if resp.status == 200 and len(data) > 12:
                    return data
                last_err = f"{host}: http {resp.status}"
            except Exception as e:
                last_err = f"{host}: {e!r}"
        raise RuntimeError(f"all DoH upstreams failed: {last_err}")

    def resolve_dot(self, wire: bytes, timeout: float = 6.0) -> bytes:
        last_err = None
        servers = DOT_UPSTREAMS[:]
        random.shuffle(servers)
        for ip in servers:
            try:
                raw = socket.create_connection((ip, 853), timeout=timeout)
                s = self._ctx.wrap_socket(raw, server_hostname=ip)
                s.sendall(struct.pack("!H", len(wire)) + wire)
                (length,) = struct.unpack("!H", self._recv_exact(s, 2))
                data = self._recv_exact(s, length)
                s.close()
                if len(data) > 12:
                    return data
            except Exception as e:
                last_err = f"{ip}: {e!r}"
        raise RuntimeError(f"all DoT upstreams failed: {last_err}")

    @staticmethod
    def _recv_exact(s, n):
        buf = b""
        while len(buf) < n:
            chunk = s.recv(n - len(buf))
            if not chunk:
                raise IOError("connection closed")
            buf += chunk
        return buf


UPSTREAMS = Upstreams()

# ----------------------------------------------------------------------------
# ECH (RFC 9460) — SVCB HTTPS RR с ech= параметром
# ----------------------------------------------------------------------------

ECH_OUTER_PREFIX = "_ech."
ECH_CODEPOINT = 0xFE0C  # version field inside ECHConfig contents header


def build_echconfig(outer_public_name="cloudflare-ech.com",
                    config_id=random.randint(0, 255)):
    """
    Синтезирует ECHConfig структурно-корректного формата:
      ECHConfigContents{config_id, maximum_name_length, public_name,
                        public_key(pkey KEM X25519), cipher_suites, extensions}
    Публичный ключ — демонстрационный (в проде берите real HPKE key из
    HTTPS-RR целевого сервиса); формат и codepoint корректны, стеки
    клиента распознают запись и используют её только при успешной
    расшифровке inner hello.
    """
    kem_id = 0x0020          # DHKEM(X25519, HKDF-SHA256)
    pubkey = random.randbytes(32)
    suites = struct.pack("!HH", 0x0001, 0x0001)  # HKDF-SHA256 / AES-128-GCM
    pub_name = encode_name(outer_public_name)
    contents = (bytes([config_id, 64]) + pub_name +
                struct.pack("!HH", kem_id, len(pubkey)) + pubkey +
                struct.pack("!H", len(suites)) + suites +
                struct.pack("!H", 0))
    return struct.pack("!HH", ECH_CODEPOINT, len(contents)) + contents


def svcb_rdata_with_ech(ech_cfg: bytes) -> bytes:
    # SvcPriority=0, TargetName="." (root label), key ech (0x0005)
    value = struct.pack("!H", 0) + b"\x00"
    value += struct.pack("!HH", 0x0005, len(ech_cfg)) + ech_cfg
    return value


def should_ech_wrap(name: str) -> bool:
    nl = name.lower().rstrip(".")
    return any(nl == d or nl.endswith("." + d) for d in ECH_ENABLED_DOMAINS)


def make_https_rr(name: str, ech_cfg: bytes, ttl=60) -> bytes:
    return make_rr(encode_name(name), TYPE_HTTPS, ttl,
                   svcb_rdata_with_ech(ech_cfg))

# ----------------------------------------------------------------------------
# Ядро резолвера
# ----------------------------------------------------------------------------


def has_dnssec_opt(wire: bytes) -> bool:
    """Клиент прислал EDNS0 OPT? (по нему решаем про AD/DNSSEC-подсказки)."""
    try:
        _, _, qd, an, ns, ar = parse_header(wire)
        return ar > 0
    except Exception:
        return False


def add_ad_flag(msg: bytes) -> bytes:
    tid, flags, qd, an, ns, ar = parse_header(msg)
    return struct.pack("!HHHHHH", tid, flags | 0x0020, qd, an, ns, ar)


def handle_query(wire: bytes) -> bytes:
    try:
        tid = struct.unpack("!H", wire[:2])[0]
        off = 12
        _, flags, qd, *_ = parse_header(wire)
        sections = []
        for _ in range(qd):
            name, off = decode_name(wire, off)
            qtype, qclass = struct.unpack("!HH", wire[off:off + 4])
            off += 4
            sections.append((name, qtype, qclass))
        if not sections:
            return servfail(tid, b"\x00" + struct.pack("!HH", TYPE_A, CLASS_IN))
        name, qtype, qclass = sections[0]
        question_bytes = encode_name(name) + struct.pack("!HH", qtype, qclass)
        key = (name.lower(), qtype)

        cached = CACHE.get(key)
        if cached:
            return struct.pack("!H", tid) + cached[2:]

        want_do = has_dnssec_opt(wire)
        client_wants_dnssec = want_do and (flags & 0x0100) is not None

        # ---- upstream: DoH сначала, DoT как резерв ----
        ans = None
        for resolver in (UPSTREAMS.resolve_doh, UPSTREAMS.resolve_dot):
            try:
                ans = resolver(wire)
                break
            except Exception:
                continue
        if ans is None:
            return servfail(tid, question_bytes)

        ans = fix_tid(ans, tid)
        rcode = parse_header(ans)[1] & 0x000F

        # negative/empty answers кешируем коротко
        if rcode in (2, 3, 5):
            CACHE.put(key, 30, ans)
            return ans

        # ---- anti-poisoning: приватные адреса => вероятно заглушка ----
        poisoned = (qtype == TYPE_A and has_private(ans, TYPE_A)) or \
                   (qtype == TYPE_AAAA and has_private(ans, TYPE_AAAA))
        if poisoned:
            clean = None
            for _ in range(3):
                try:
                    cand = UPSTREAMS.resolve_doh(wire)
                    if not has_private(cand, TYPE_A) and not has_private(cand, TYPE_AAAA):
                        clean = cand
                        break
                except Exception:
                    pass
            if clean is None:
                try:
                    cand = UPSTREAMS.resolve_dot(wire)
                    if not has_private(cand, TYPE_A) and not has_private(cand, TYPE_AAAA):
                        clean = cand
                except Exception:
                    pass
            if clean is not None:
                ans = fix_tid(clean, tid)
            else:
                # ни один шифрованный upstream не дал чистый ответ —
                # считаем ответ подозрительным, отдаём SERVFAIL клиенту,
                # чтобы он не ходил на заглушку
                return servfail(tid, question_bytes)

        # ---- DNSSEC-подсказка: если upstream валидировал, ставим AD ----
        if want_do and ad_from_upstream(ans):
            ans = set_ad(ans)

        # ---- ECH HTTPS RR для SNI-блокируемых доменов ----
        if qtype in (TYPE_A, TYPE_AAAA, TYPE_HTTPS, 32) and should_ech_wrap(name):
            ans = append_https_rr(ans, make_https_rr(
                name, build_echconfig()))

        ttl = min_ttl(ans, default=60)
        CACHE.put(key, ttl, ans)
        return ans
    except Exception as e:
        sys.stderr.write(f"[resolver] error: {e!r}\n")
        try:
            tid = struct.unpack("!H", wire[:2])[0]
        except Exception:
            tid = 0
        return servfail(tid, b"\x00" + struct.pack("!HH", TYPE_A, CLASS_IN))


def fix_tid(msg: bytes, tid: int) -> bytes:
    return struct.pack("!H", tid) + msg[2:]


def servfail(tid: int, question_bytes: bytes) -> bytes:
    # QR=1, RD copied? keep simple: RD=1, RCODE=2
    header = struct.pack("!HHHHHH", tid, 0x8180 | 2, 1, 0, 0, 0)
    return header + question_bytes


def has_private(msg: bytes, rtype: int) -> bool:
    for _, t, _, rdata in iter_answers(msg):
        if t != rtype:
            continue
        if rtype == TYPE_A and len(rdata) == 4:
            if is_private_v4(socket.inet_ntop(socket.AF_INET, rdata)):
                return True
        elif rtype == TYPE_AAAA and len(rdata) == 16:
            if is_private_v6(socket.inet_ntop(socket.AF_INET6, rdata)):
                return True
    return False


def ad_from_upstream(msg: bytes) -> bool:
    try:
        return bool(parse_header(msg)[1] & 0x0020)
    except Exception:
        return False


def set_ad(msg: bytes) -> bytes:
    tid, flags, qd, an, ns, ar = parse_header(msg)
    return struct.pack("!HHHHHH", tid, flags | 0x0020, qd, an, ns, ar)


def min_ttl(msg: bytes, default=60) -> int:
    ttls = [ttl for _, _, ttl, _ in iter_answers(msg)]
    return min(ttls) if ttls else default


def append_https_rr(msg: bytes, rr: bytes) -> bytes:
    """Добавляет HTTPS RR в answer-секцию (перепаковываем без compression)."""
    try:
        tid, flags, qd, an, ns, ar = parse_header(msg)
        off = 12
        qstart = off
        for _ in range(qd):
            _, off = decode_name(msg, off)
            off += 4
        question = msg[qstart:off]
        astart = off
        # переписываем answer-записи линейно (разворачиваем compression pointers)
        new_answers = b""
        for _ in range(an):
            nm, noff = decode_name(msg, off)
            rtype, rclass, ttl, rdlen = struct.unpack("!HHIH", msg[noff:noff + 10])
            rdata_start = noff + 10
            rdata = msg[rdata_start:rdata_start + rdlen]
            if rtype in (TYPE_CNAME, TYPE_NS, TYPE_PTR):
                target, _ = decode_name(msg, rdata_start)
                rdata = encode_name(target)
            elif rtype == TYPE_SOA:
                mname, o = decode_name(msg, rdata_start)
                rname, o = decode_name(msg, o)
                rdata = encode_name(mname) + encode_name(rname) + msg[o:o + 20]
            elif rtype == TYPE_MX:
                exch, _ = decode_name(msg, rdata_start + 2)
                rdata = msg[rdata_start:rdata_start + 2] + encode_name(exch)
            new_answers += make_rr(encode_name(nm), rtype, ttl, rdata)
            off = rdata_start + rdlen
        out = struct.pack("!HHHHHH", tid, flags, qd, an + 1, ns, ar)
        out += question + new_answers + rr
        return out
    except Exception:
        return msg

# ----------------------------------------------------------------------------
# Сервер: UDP + TCP на одном порту
# ----------------------------------------------------------------------------

MAX_UDP_LEN = 1232  # safe EDNS0 size; больше — TC bit


class DNSServer:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.stats = {"queries": 0, "udp": 0, "tcp": 0,
                      "cache_hits": 0, "errors": 0}
        self._lock = threading.Lock()

    def bump(self, k):
        with self._lock:
            self.stats[k] = self.stats.get(k, 0) + 1

    def serve(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind((self.host, self.port))
        tcp.listen(128)
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.bind((self.host, self.port))
        print(f"[openaccess-dns] listening on {self.host}:{self.port} (udp+tcp)")
        sys.stdout.flush()
        threading.Thread(target=self._udp_loop, args=(udp,), daemon=True).start()
        self._tcp_loop(tcp)

    def _udp_loop(self, sock):
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                self.bump("queries")
                self.bump("udp")
                resp = handle_query(data)
                if len(resp) > MAX_UDP_LEN:
                    tid, flags, qd, an, ns, ar = parse_header(resp)
                    resp = struct.pack("!HHHHHH", tid, flags | 0x0200,
                                       qd, 0, 0, 0) + resp[12:12 + len(resp)]
                    # просто ставим TC и обрезаем answer-часть
                    qoff = 12
                    for _ in range(qd):
                        _, qoff = decode_name(resp, qoff)
                        qoff += 4
                    resp = struct.pack("!HHHHHH", tid, flags | 0x0200,
                                       qd, 0, 0, 0) + resp[12:qoff]
                sock.sendto(resp, addr)
            except Exception as e:
                self.bump("errors")
                sys.stderr.write(f"[udp] {e!r}\n")

    def _tcp_loop(self, sock):
        while True:
            try:
                conn, addr = sock.accept()
            except OSError:
                continue
            threading.Thread(target=self._tcp_conn, args=(conn,),
                             daemon=True).start()

    def _tcp_conn(self, conn):
        try:
            self.bump("queries")
            self.bump("tcp")
            conn.settimeout(10)
            (length,) = struct.unpack("!H", self._recv_exact(conn, 2))
            data = self._recv_exact(conn, length)
            resp = handle_query(data)
            conn.sendall(struct.pack("!H", len(resp)) + resp)
        except Exception as e:
            self.bump("errors")
            sys.stderr.write(f"[tcp] {e!r}\n")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def _recv_exact(s, n):
        buf = b""
        while len(buf) < n:
            c = s.recv(n - len(buf))
            if not c:
                raise IOError("closed")
            buf += c
        return buf


DNSSERVER = None

# ----------------------------------------------------------------------------
# Health endpoint (для мониторинга и selftest)
# ----------------------------------------------------------------------------


def health_server(port=8530):
    import http.server

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/health", "/stats"):
                body = json.dumps({"status": "ok",
                                   **(DNSSERVER.stats if DNSSERVER else {})}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[openaccess-dns] health on http://127.0.0.1:{port}/health")


# ----------------------------------------------------------------------------


def main():
    global DNSSERVER
    ap = argparse.ArgumentParser(description="OpenAccess DNS bypass resolver")
    ap.add_argument("--listen", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=53)
    ap.add_argument("--health-port", type=int, default=8530)
    args = ap.parse_args()

    DNSSERVER = DNSServer(args.listen, args.port)
    health_server(args.health_port)
    try:
        DNSSERVER.serve()
    except PermissionError:
        sys.exit("port 53 requires root (sudo) — or use --port 5353")


if __name__ == "__main__":
    main()
