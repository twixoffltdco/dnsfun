"use client";

import { useState } from "react";
import { Server, Terminal, Copy, Check } from "lucide-react";

const DOCKER_COMPOSE = `git clone https://github.com/your-org/openaccess-dns.git
cd openaccess-dns
chmod +x scripts/deploy.sh
./scripts/deploy.sh`;

const COMPOSE_ONLY = `docker compose up -d`;

export function SelfHostSection() {
  const [copied, setCopied] = useState<"full" | "compose" | null>(null);

  const copy = async (text: string, key: "full" | "compose") => {
    await navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <section id="self-host" className="px-4 py-20">
      <div className="mx-auto max-w-4xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Свой сервер
          </h2>
          <p className="text-white/50">
            Разверните личный DNS за 1 минуту на любом VPS.
          </p>
        </div>

        <div className="glass-strong rounded-2xl p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-neon-cyan/10 text-neon-cyan">
              <Server className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Развернуть за 1 минуту</h3>
              <p className="text-sm text-white/50">
                Ubuntu / Debian · Docker · AdGuard Home
              </p>
            </div>
          </div>

          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-white/60">
              <Terminal className="h-4 w-4" />
              <span>Полная установка</span>
            </div>
            <button
              onClick={() => copy(DOCKER_COMPOSE, "full")}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-neon-cyan hover:bg-neon-cyan/10"
            >
              {copied === "full" ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
              {copied === "full" ? "Скопировано" : "Копировать"}
            </button>
          </div>

          <pre className="code-block mb-6 overflow-x-auto rounded-xl p-4 text-sm text-neon-cyan">
            {DOCKER_COMPOSE}
          </pre>

          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-white/60">
              <Terminal className="h-4 w-4" />
              <span>Только Docker (если уже склонировали)</span>
            </div>
            <button
              onClick={() => copy(COMPOSE_ONLY, "compose")}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-neon-cyan hover:bg-neon-cyan/10"
            >
              {copied === "compose" ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
              {copied === "compose" ? "Скопировано" : "Копировать"}
            </button>
          </div>

          <pre className="code-block overflow-x-auto rounded-xl p-4 text-sm text-neon-cyan">
            {COMPOSE_ONLY}
          </pre>

          <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white/60">
            <p className="mb-2 font-medium text-white/80">После запуска:</p>
            <ul className="list-inside list-disc space-y-1">
              <li>
                Веб-интерфейс:{" "}
                <code className="text-neon-cyan">http://YOUR_IP:3000</code>
              </li>
              <li>Логин по умолчанию: admin / (задайте в .env)</li>
              <li>
                DNS порты: 53 (UDP/TCP), 853 (DoT), 443/8443 (DoH)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
