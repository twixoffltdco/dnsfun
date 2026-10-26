/**
 * Public DNS endpoints configuration.
 * Замените домен/IP на свой после деплоя (см. docker-compose.yml + dns/resolver.py).
 * POC-значения ниже — реальные рабочие публичные bypass-эндпоинты,
 * лендинг работает «из коробки» до установки собственного сервера.
 */
export const DNS_CONFIG = {
  // Plain DNS (наш резолвер: dns/resolver.py слушает :53)
  plain: {
    ipv4: "94.140.14.14",
    ipv6: "2a10:50c0::1:ff",
    // Secondary
    ipv4_secondary: "94.140.15.15",
    ipv6_secondary: "2a10:50c0::2:ff",
  },
  // DNS-over-HTTPS (dns/doh_server.py за Caddy/nginx, RFC 8484 wire-format)
  doh: {
    url: "https://dns.openaccess.example/dns-query",
    // Проверенные бесплатные DoH для обхода — работают прямо сейчас:
    fallbacks: [
      "https://dns.adguard-dns.com/dns-query",
      "https://cloudflare-dns.com/dns-query",
      "https://dns.google/dns-query",
    ] as readonly string[],
    // Публичный браузерный preset (chrome://settings — «Настраиваемый»)
    browserPreset: "https://dns.adguard-dns.com/dns-query",
  },
  // DNS-over-TLS (порт 853)
  dot: {
    hostname: "dns.openaccess.example",
    port: 853,
    fallbacks: ["dns.adguard-dns.com", "security.cloudflare-dns.com", "dns.google"],
  },
  // Android Private DNS hostname (работает из коробки до своего сервера)
  androidPrivateDns: "dns.adguard-dns.com",
  // Display names
  name: "OpenAccess DNS",
} as const;
