/**
 * OUR OWN server endpoints (OpenAccess DNS self-host stack).
 *
 * Single source of truth: edit the values here after deploying your own
 * server (docker-compose.yml + dns/resolver.py + AdGuard Home), and every
 * part of the landing / iOS profile will use YOUR DNS — never a third-party
 * resolver like AdGuard Public DNS.
 */

/** Your public server hostname (DNS A/AAAA record -> VPS IP). Used for DoT / Android Private DNS. */
export const SERVER_HOSTNAME = "dns.openaccess.example";

/** Base https:// URL of your own DoH endpoint (served by dns/doh_server.py behind Caddy/nginx TLS). */
export const DOH_URL = `https://${SERVER_HOSTNAME}/dns-query`;

/** Your public IPv4 (plain DNS, port 53). */
export const SERVER_IPV4 = "203.0.113.10";

/** Your public IPv6 (plain DNS, port 53). Replace with your real address. */
export const SERVER_IPV6 = "2001:db8::10";
