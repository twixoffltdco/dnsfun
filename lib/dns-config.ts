/**
 * Public DNS endpoints configuration.
 *
 * ВАЖНО: здесь указаны ТОЛЬКО НАШИ собственные эндпоинты (наш сервер из
 * docker-compose.yml + dns/resolver.py). Сторонние резолверы (AdGuard Public
 * DNS, Cloudflare, Google) клиентам НЕ отдаются — обход блокировок РКН идёт
 * через наш резолвер, который сам ходит в зашифрованные upstream'ы.
 *
 * После деплоя своего сервера замените hostname/IP в lib/server-config.ts
 * (или задайте NEXT_PUBLIC_* переменные окружения) — все карточки лендинга,
 * Android-инструкция и iOS-профиль подхватят наши адреса автоматически.
 */
import {
  SERVER_HOSTNAME,
  DOH_URL,
  SERVER_IPV4,
  SERVER_IPV6,
} from "./server-config";

/** Наш собственный DoT/DoH hostname (можно переопределить через env). */
export const DOT_HOSTNAME =
  process.env.NEXT_PUBLIC_DOT_HOST || SERVER_HOSTNAME;

/** Наш собственный DoH endpoint (можно переопределить через env). */
export const OUR_DOH_URL =
  process.env.NEXT_PUBLIC_DOH_URL || DOH_URL;

export const DNS_CONFIG = {
  // Plain DNS — наш резолвер (dns/resolver.py слушает :53 на нашем сервере)
  plain: {
    ipv4: SERVER_IPV4,
    ipv6: SERVER_IPV6,
  },
  // DNS-over-HTTPS — ТОЛЬКО наш эндпоинт (dns/doh_server.py за TLS-терминатором)
  doh: {
    url: OUR_DOH_URL,
    // Публичный браузерный preset (chrome://settings — «Настраиваемый») — наш сервер
    browserPreset: OUR_DOH_URL,
  },
  // DNS-over-TLS — наш сервер (порт 853)
  dot: {
    hostname: DOT_HOSTNAME,
    port: 853,
    // Единственный DoT-хост — наш собственный
    fallbacks: [DOT_HOSTNAME] as readonly string[],
  },
  // Android Private DNS hostname — наш сервер
  androidPrivateDns: DOT_HOSTNAME,
  // Display names
  name: "OpenAccess DNS",
} as const;
