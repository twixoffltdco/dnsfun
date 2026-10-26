"use client";

import { Smartphone, Download } from "lucide-react";
import { DNS_CONFIG } from "@/lib/dns-config";

export function MobileSection() {
  return (
    <section id="mobile" className="px-4 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Мобильные устройства
          </h2>
          <p className="text-white/50">
            Один клик для iOS. Для Android — Private DNS.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* iOS */}
          <div className="glass rounded-2xl p-8">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-neon-pink/10 text-neon-pink">
                <Smartphone className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">iOS / iPadOS</h3>
                <p className="text-sm text-white/50">Конфигурационный профиль</p>
              </div>
            </div>

            <p className="mb-6 text-white/70">
              Скачайте профиль — он автоматически настроит DNS-over-HTTPS или
              DNS-over-TLS на вашем iPhone / iPad.
            </p>

            <a
              href="/api/ios-profile"
              download="OpenAccess-DNS.mobileconfig"
              className="btn-neon inline-flex w-full items-center justify-center gap-2 rounded-xl bg-neon-pink/20 border border-neon-pink/40 px-6 py-4 font-semibold text-neon-pink hover:bg-neon-pink/30"
            >
              <Download className="h-5 w-5" />
              Скачать профиль (.mobileconfig)
            </a>

            <ol className="mt-6 space-y-2 text-sm text-white/50">
              <li>1. Скачайте и откройте файл</li>
              <li>2. Перейдите в Настройки → Профиль загружен</li>
              <li>3. Установите и введите код-пароль</li>
            </ol>
          </div>

          {/* Android */}
          <div className="glass rounded-2xl p-8">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-neon-cyan/10 text-neon-cyan">
                <Smartphone className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Android</h3>
                <p className="text-sm text-white/50">Private DNS (DoT)</p>
              </div>
            </div>

            <p className="mb-6 text-white/70">
              Начиная с Android 9 можно указать hostname DNS-over-TLS в
              системных настройках.
            </p>

            <div className="code-block mb-4 rounded-xl px-4 py-3 text-sm text-neon-cyan">
              {DNS_CONFIG.androidPrivateDns}
            </div>

            <ol className="space-y-2 text-sm text-white/50">
              <li>1. Настройки → Сеть и интернет → Частный DNS</li>
              <li>2. Выберите «Имя хоста поставщика частных DNS»</li>
              <li>3. Введите hostname выше и сохраните</li>
            </ol>
          </div>
        </div>
      </div>
    </section>
  );
}
