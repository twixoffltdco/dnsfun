/**
 * Public DNS endpoints configuration.
 * Replace with your own domain / IPs when deploying.
 */
export const DNS_CONFIG = {
  // Plain DNS (example public endpoints — replace with your server)
  plain: {
    ipv4: "94.140.14.14",
    ipv6: "2a10:50c0::1:ff",
    // Secondary
    ipv4_secondary: "94.140.15.15",
    ipv6_secondary: "2a10:50c0::2:ff",
  },
  // DNS-over-HTTPS
  doh: {
    url: "https://dns.openaccess.example/dns-query",
    // Alternative popular free DoH that often works well
    fallback: "https://dns.adguard-dns.com/dns-query",
  },
  // DNS-over-TLS
  dot: {
    hostname: "dns.openaccess.example",
    port: 853,
  },
  // Display names
  name: "OpenAccess DNS",
} as const;
