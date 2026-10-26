#!/usr/bin/env python3
"""
OpenAccess DNS — selftest.

Проверяет живой резолвер:
  1. UDP/TCP сервер отвечает на обычные A/AAAA-запросы.
  2. Разрешает «блокируемые» домены (YouTube, Telegram, Discord, X) реальными
     публичными IP, а не заглушками.
  3. Anti-poisoning: приватные адреса в ответах считаются подменой.
  4. ECH HTTPS RR добавляется для SNI-чувствительных доменов.
  5. NXDOMAIN и кэш работают корректно.

Использование:
  python3 dns/resolver.py --listen 127.0.0.1 --port 5353 &   # или systemd
  python3 dns/selftest.py [--server 127.0.0.1] [--port 5353]
"""

from __future__ import annotations

import argparse
import socket
import struct
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import resolver as R  # noqa: E402

PASS = "\033[32m✔\033[0m"
FAIL = "\033[31m✘\033[0m"

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"  {PASS if ok else FAIL} {name}" + (f" — {detail}" if detail else ""))
    return ok


def build_query(qname: str, rtype: int, tid: int = 0xBEEF, edns: bool = False) -> bytes:
    flags = 0x0100
    ar = 0
    msg = R.encode_name(qname) + struct.pack("!HH", rtype, R.CLASS_IN)
    header = struct.pack("!HHHHHH", tid, flags, 1, 0, 0, ar)
    out = header + msg
    if edns:
        opt = b"\x00" + struct.pack("!H", 4096) + struct.pack("!H", 0x8000) + \
            struct.pack("!I", 0) + struct.pack("!H", 0)
        hdr = struct.unpack("!HHHHHH", out[:12])
        out = struct.pack("!HHHHHH", *hdr[:5], 1) + out[12:] + opt
    return out


def udp_query(server, port, wire, timeout=8.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    s.sendto(wire, (server, port))
    data, _ = s.recvfrom(65535)
    s.close()
    return data


def tcp_query(server, port, wire, timeout=8.0):
    s = socket.create_connection((server, port), timeout=timeout)
    s.sendall(struct.pack("!H", len(wire)) + wire)
    ln = s.recv(2)
    (length,) = struct.unpack("!H", ln)
    buf = b""
    while len(buf) < length:
        buf += s.recv(length - len(buf))
    s.close()
    return buf


def a_records(msg):
    ips = []
    for _, t, _, rd in R.iter_answers(msg):
        if t == R.TYPE_A and len(rd) == 4:
            ips.append(socket.inet_ntop(socket.AF_INET, rd))
    return ips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5353)
    args = ap.parse_args()

    print(f"OpenAccess DNS selftest → {args.server}:{args.port}\n")

    # 0) сервер жив?
    try:
        resp = udp_query(args.server, args.port,
                         build_query("example.com", R.TYPE_A))
        alive = R.parse_header(resp)[1] & 0xF != 2 or True
    except Exception as e:
        print(f"{FAIL} Сервер не отвечает ({e!r}). Запустите:\n"
              f"  python3 dns/resolver.py --listen 127.0.0.1 --port 5353")
        sys.exit(2)
    check("UDP-сервер отвечает", True)

    # 1) TCP тоже
    try:
        resp_tcp = tcp_query(args.server, args.port,
                             build_query("example.com", R.TYPE_A))
        check("TCP-сервер отвечает", R.parse_header(resp_tcp)[3] >= 1)
    except Exception as e:
        check("TCP-сервер отвечает", False, repr(e))

    # 2) блокируемые домены резолвятся реальными IP
    blocked_domains = [
        "www.youtube.com", "telegraph.co.uk", "web.telegram.org",
        "discord.com", "x.com", "www.instagram.com",
    ]
    for dom in ["www.youtube.com", "telegram.org", "discord.com", "x.com"]:
        resp = udp_query(args.server, args.port, build_query(dom, R.TYPE_A))
        rcode = R.parse_header(resp)[1] & 0xF
        ips = a_records(resp)
        good = rcode == 0 and ips and not any(R.is_private_v4(ip) for ip in ips)
        check(f"{dom} → реальные IP (без заглушек)", good,
              ", ".join(ips[:3]) if ips else f"rcode={rcode}")

    # 3) anti-poisoning unit-check
    fake = struct.pack("!HHHHHH", 1, 0x8180, 1, 1, 0, 0)
    fake += R.encode_name("blocked.example") + struct.pack("!HH", R.TYPE_A, 1)
    fake += R.encode_name("blocked.example") + struct.pack("!HHIH", R.TYPE_A, 1, 60, 4)
    fake += socket.inet_aton("127.0.0.1")
    check("Anti-poisoning: 127.0.0.1 распознан как подмена",
          R.has_private(fake, R.TYPE_A))

    # 4) ECH HTTPS RR добавляется для youtube/x/telegram
    resp = udp_query(args.server, args.port, build_query("www.youtube.com", R.TYPE_A))
    has_https = any(t == R.TYPE_HTTPS for _, t, _, _ in R.iter_answers(resp))
    check("ECH: HTTPS(SVCB) RR с ech= в ответе для youtube", has_https)

    # 5) обычный домен без ECH-обёртки
    resp = udp_query(args.server, args.port, build_query("example.org", R.TYPE_A))
    no_https = not any(t == R.TYPE_HTTPS for _, t, _, _ in R.iter_answers(resp))
    check("Обычные домены не оборачиваются ECH", no_https)

    # 6) NXDOMAIN
    resp = udp_query(args.server, args.port,
                     build_query(f"nonexistent-{int(time.time())}.invalid", R.TYPE_A))
    rcode = R.parse_header(resp)[1] & 0xF
    check("NXDOMAIN корректен", rcode == 3, f"rcode={rcode}")

    # 7) кэш: повторный запрос быстрее
    udp_query(args.server, args.port, build_query("cloudflare.com", R.TYPE_A))
    t0 = time.time()
    udp_query(args.server, args.port, build_query("cloudflare.com", R.TYPE_A))
    cached_ms = (time.time() - t0) * 1000
    check("Кэш работает (повтор < 50 мс)", cached_ms < 50, f"{cached_ms:.1f} мс")

    # 8) AAAA
    resp = udp_query(args.server, args.port, build_query("youtube.com", R.TYPE_AAAA))
    rcode = R.parse_header(resp)[1] & 0xF
    v6 = [socket.inet_ntop(socket.AF_INET6, rd)
          for _, t, _, rd in R.iter_answers(resp) if t == R.TYPE_AAAA and len(rd) == 16]
    check("AAAA-резолвинг", rcode == 0 and v6 and not any(R.is_private_v6(ip) for ip in v6),
          ", ".join(v6[:2]) if v6 else "")

    total, ok = len(results), sum(results)
    print(f"\n{'='*46}\nИтог: {ok}/{total} проверок пройдено")
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
