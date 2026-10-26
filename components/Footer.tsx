export function Footer() {
  return (
    <footer className="border-t border-white/5 px-4 py-12">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 sm:flex-row">
        <div className="text-center sm:text-left">
          <p className="text-lg font-semibold text-white">
            OpenAccess DNS
          </p>
          <p className="text-sm text-white/40">
            Децентрализованный DNS для свободного интернета
          </p>
        </div>
        <div className="flex gap-6 text-sm text-white/50">
          <a
            href="https://github.com/your-org/openaccess-dns"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-neon-cyan transition-colors"
          >
            GitHub
          </a>
          <a
            href="#connect"
            className="hover:text-neon-cyan transition-colors"
          >
            Подключиться
          </a>
          <a
            href="#self-host"
            className="hover:text-neon-cyan transition-colors"
          >
            Self-host
          </a>
        </div>
      </div>
      <p className="mt-8 text-center text-xs text-white/30">
        MIT License · Open Source · 2024–2026
      </p>
    </footer>
  );
}
