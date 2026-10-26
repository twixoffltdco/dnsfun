import { NextResponse } from "next/server";
import { DNS_CONFIG } from "@/lib/dns-config";

/**
 * Генерирует Apple Configuration Profile (.mobileconfig) с DoH/DoT.
 *
 * Env:
 *   NEXT_PUBLIC_DOH_URL  — ваш DoH endpoint (по умолчанию рабочий публичный preset)
 *   NEXT_PUBLIC_DOT_HOST — ваш DoT hostname
 */
export async function GET() {
  const payloadUUID = crypto.randomUUID().toUpperCase();
  const profileUUID = crypto.randomUUID().toUpperCase();
  const dohUUID = crypto.randomUUID().toUpperCase();

  // Свой сервер после деплоя, иначе — проверенный рабочий fallback,
  // чтобы профиль был функциональным «из коробки».
  const dohUrl =
    process.env.NEXT_PUBLIC_DOH_URL || DNS_CONFIG.doh.browserPreset;
  const dotHost =
    process.env.NEXT_PUBLIC_DOT_HOST || DNS_CONFIG.dot.fallbacks[0];
  const serverName = DNS_CONFIG.name;

  const mobileconfig = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>PayloadContent</key>
  <array>
    <dict>
      <key>DNSSettings</key>
      <dict>
        <key>DNSProtocol</key>
        <string>HTTPS</string>
        <key>ServerURL</key>
        <string>${dohUrl}</string>
        <key>ServerName</key>
        <string>${serverName}</string>
      </dict>
      <key>PayloadDescription</key>
      <string>Configures DNS-over-HTTPS for OpenAccess DNS</string>
      <key>PayloadDisplayName</key>
      <string>OpenAccess DNS (DoH)</string>
      <key>PayloadIdentifier</key>
      <string>com.openaccess.dns.doh</string>
      <key>PayloadType</key>
      <string>com.apple.dnsSettings.managed</string>
      <key>PayloadUUID</key>
      <string>${dohUUID}</string>
      <key>PayloadVersion</key>
      <integer>1</integer>
      <key>ProhibitDisablement</key>
      <false/>
    </dict>
    <dict>
      <key>DNSSettings</key>
      <dict>
        <key>DNSProtocol</key>
        <string>TLS</string>
        <key>ServerName</key>
        <string>${dotHost}</string>
        <key>ServerPort</key>
        <integer>${DNS_CONFIG.dot.port}</integer>
      </dict>
      <key>PayloadDescription</key>
      <string>Configures DNS-over-TLS for OpenAccess DNS</string>
      <key>PayloadDisplayName</key>
      <string>OpenAccess DNS (DoT)</string>
      <key>PayloadIdentifier</key>
      <string>com.openaccess.dns.dot</string>
      <key>PayloadType</key>
      <string>com.apple.dnsSettings.managed</string>
      <key>PayloadUUID</key>
      <string>${profileUUID}</string>
      <key>PayloadVersion</key>
      <integer>1</integer>
      <key>ProhibitDisablement</key>
      <false/>
    </dict>
  </array>
  <key>PayloadDescription</key>
  <string>OpenAccess DNS — free &amp; open DNS without blocks. Returns your internet as in 2020.</string>
  <key>PayloadDisplayName</key>
  <string>OpenAccess DNS</string>
  <key>PayloadIdentifier</key>
  <string>com.openaccess.dns.profile</string>
  <key>PayloadOrganization</key>
  <string>OpenAccess DNS</string>
  <key>PayloadRemovalDisallowed</key>
  <false/>
  <key>PayloadType</key>
  <string>Configuration</string>
  <key>PayloadUUID</key>
  <string>${payloadUUID}</string>
  <key>PayloadVersion</key>
  <integer>1</integer>
</dict>
</plist>`;

  return new NextResponse(mobileconfig, {
    status: 200,
    headers: {
      "Content-Type": "application/x-apple-aspen-config",
      "Content-Disposition":
        'attachment; filename="OpenAccess-DNS.mobileconfig"',
      "Cache-Control": "no-store",
    },
  });
}
