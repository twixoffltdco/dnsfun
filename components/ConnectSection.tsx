"use client";

import { Globe, Shield, Lock } from "lucide-react";
import { DnsCard } from "./DnsCard";
import { DNS_CONFIG } from "@/lib/dns-config";

export function ConnectSection() {
  return (
    <section id="connect" className="px-4 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Быстрое подключение
          </h2>
          <p className="text-white/50">
            Выберите протокол и скопируйте адрес. Работает на всех устройствах.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <DnsCard
            title="Обычный DNS"
            description="IPv4 / IPv6 — ваш сервер после деплоя"
            value={DNS_CONFIG.plain.ipv4}
            secondaryValue={DNS_CONFIG.plain.ipv6}
            icon={<Globe className="h-5 w-5" />}
          />
          <DnsCard
            title="DNS-over-HTTPS"
            description="DoH — шифрованный, работает прямо сейчас"
            value={DNS_CONFIG.doh.browserPreset}
            icon={<Shield className="h-5 w-5" />}
          />
          <DnsCard
            title="DNS-over-TLS"
            description="DoT — порт 853, Android Private DNS"
            value={DNS_CONFIG.dot.fallbacks[0]}
            icon={<Lock className="h-5 w-5" />}
          />
        </div>

        <p className="mt-8 text-center text-sm text-white/40">
          DoH/DoT адреса выше — готовые к использованию. «Обычный DNS» —
          пример: разверните свой сервер (секция ниже) и подставьте его IP.
        </p>
      </div>
    </section>
  );
}
