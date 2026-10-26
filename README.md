# OpenAccess DNS

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](docker-compose.yml)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)](https://www.typescriptlang.org/)

> **Вернем ваш интернет как в 2020 году**  
> Без блокировок. Бесплатно. Open Source.

Децентрализованный DNS-резолвер для свободного интернета.  
Стильный лендинг + готовый Docker-стек на базе AdGuard Home с предустановленными правилами.

---

## ✨ Возможности

- **Публичный DNS** — Plain (IPv4/IPv6), DNS-over-HTTPS, DNS-over-TLS
- **iOS профиль** — один клик, `.mobileconfig` генерируется на лету
- **Android Private DNS** — инструкция + hostname
- **Self-host за 1 минуту** — `docker compose up -d` + `deploy.sh`
- **Современный UI** — pure black, glassmorphism, neon accents

---

## 🖼 Скриншоты

> *Placeholders — замените на реальные скриншоты после деплоя*

| Hero | Connect | Self-host |
|------|---------|-----------|
| ![Hero](https://via.placeholder.com/400x250/000000/00f2ea?text=Hero) | ![Connect](https://via.placeholder.com/400x250/000000/00f2ea?text=Connect) | ![Self-host](https://via.placeholder.com/400x250/000000/fe2c55?text=Self-host) |

---

## 🚀 Как использовать публичный DNS

1. Откройте [лендинг](#) (после деплоя Next.js)
2. Скопируйте нужный адрес — все они ведут на **наш** сервер:
   - **Обычный DNS**: IP нашего резолвера (порт 53)
   - **DoH**: `https://dns.openaccess.example/dns-query` (наш эндпоинт)
   - **DoT**: `dns.openaccess.example` (наш сервер, порт 853)
3. Для iOS — нажмите «Скачать профиль»
4. Для Android — Settings → Network → Private DNS → введите hostname

> Сторонние публичные DNS (AdGuard Public DNS, Cloudflare, Google) клиентам
> **не выдаются** — обход блокировок РКН идёт через наш резолвер, который сам
> ходит в зашифрованные upstream'ы (DoH/DoT).
>
> Свои адреса задаются в одном месте — `lib/server-config.ts`
> (`SERVER_HOSTNAME`, `SERVER_IPV4`, `SERVER_IPV6`). После деплоя замените их
> на реальные значения вашего VPS, либо переопределите через переменные
> окружения `NEXT_PUBLIC_DOH_URL` / `NEXT_PUBLIC_DOT_HOST`.

---

## ⚡ Развернуть свой DNS за 1 минуту

### Требования
- VPS (Ubuntu 22.04+ / Debian 12+)
- Root-доступ
- Открытые порты: 53, 80, 443, 853, 3000

### Быстрый старт

```bash
git clone https://github.com/your-org/openaccess-dns.git
cd openaccess-dns
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

Или вручную:

```bash
docker compose up -d
```

После запуска:

- Веб-интерфейс: `http://YOUR_IP:3000`
- DNS: `YOUR_IP` (порт 53)
- Первый вход — задайте пароль в UI

### Что внутри

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | AdGuard Home контейнер |
| `config/conf/AdGuardHome.yaml` | Предустановки upstream + allowlist (YouTube, Telegram, Discord, X…) |
| `scripts/deploy.sh` | Автоустановка Docker + освобождение порта 53 |

---

## 🛠 Лендинг (Next.js)

```bash
cd openaccess-dns
npm install
npm run dev          # http://localhost:3000
npm run build && npm start
```

### Структура

```
app/
  page.tsx                 # Главная
  layout.tsx               # SEO meta
  api/ios-profile/route.ts # Генерация .mobileconfig
components/                # Hero, Cards, Sections
lib/dns-config.ts          # Адреса DNS (редактируйте здесь)
```

---

## 🔧 Настройка после деплоя

1. Зайдите в AdGuard Home UI → Settings → Encryption settings
2. Включите DoH / DoT, укажите домен и сертификат (Let's Encrypt)
3. Обновите `lib/dns-config.ts` и `.env` на лендинге
4. Пересоберите / задеплойте фронтенд

---

## 📜 Лицензия

MIT — делайте что хотите. Свобода интернета должна быть свободной.

---

<p align="center">
  <b>OpenAccess DNS</b> · Made for free internet
</p>
