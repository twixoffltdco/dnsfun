"use client";

import { ArrowDown } from "lucide-react";

export function Hero() {
  return (
    <section className="relative flex min-h-[85vh] flex-col items-center justify-center px-4 text-center">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/3 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-neon-cyan/10 blur-[120px]" />
        <div className="absolute right-1/4 top-1/2 h-[300px] w-[300px] rounded-full bg-neon-pink/10 blur-[100px]" />
      </div>

      <div className="relative z-10 max-w-4xl">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-neon-cyan/30 bg-neon-cyan/5 px-4 py-1.5 text-sm text-neon-cyan">
          <span className="h-2 w-2 animate-pulse rounded-full bg-neon-cyan" />
          Open Source · MIT · Docker
        </div>

        <h1 className="mb-6 text-4xl font-black leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
          Вернем ваш интернет
          <br />
          <span className="neon-text bg-gradient-to-r from-neon-cyan to-neon-pink bg-clip-text text-transparent">
            как в 2020 году
          </span>
        </h1>

        <p className="mb-10 text-lg text-white/60 sm:text-xl md:text-2xl">
          Без блокировок. Бесплатно. Open Source.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <a
            href="#connect"
            className="btn-neon inline-flex items-center gap-2 rounded-2xl bg-neon-cyan px-8 py-4 text-base font-semibold text-black hover:bg-neon-cyan/90"
          >
            Подключиться
            <ArrowDown className="h-5 w-5" />
          </a>
          <a
            href="#self-host"
            className="btn-neon inline-flex items-center gap-2 rounded-2xl border border-white/20 bg-white/5 px-8 py-4 text-base font-semibold text-white hover:bg-white/10"
          >
            Свой сервер
          </a>
        </div>
      </div>
    </section>
  );
}
