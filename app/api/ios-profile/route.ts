import { NextResponse } from "next/server";
import { DNS_CONFIG } from "@/lib/dns-config";

/**
 * Generates an Apple Configuration Profile (.mobileconfig)
 * that configures DNS-over-HTTPS / DNS-over-TLS system-wide.
 */
export async function GET() {
  const payloadUUID = crypto.randomUUID().toUpperCase();
  const profileUUID = crypto.randomUUID().toUpperCase();
  const dohUUID = crypto.randomUUID().toUpperCase();

  const dohUrl = DNS_CONFIG.doh.url;
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
