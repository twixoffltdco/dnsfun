#!/usr/bin/env bash
set -euo pipefail

# OpenAccess DNS — one-command deploy on Ubuntu/Debian VPS
# Usage: curl -sSL https://raw.githubusercontent.com/your-org/openaccess-dns/main/scripts/deploy.sh | bash
# Or:   ./scripts/deploy.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║       OpenAccess DNS — Deploy Script     ║"
echo "║   Вернем интернет как в 2020 году        ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Check root
if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}Please run as root (sudo ./scripts/deploy.sh)${NC}"
  exit 1
fi

# Detect OS
if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  OS=$ID
else
  echo -e "${RED}Cannot detect OS${NC}"
  exit 1
fi

echo -e "${GREEN}→ Detected OS: $OS${NC}"

# Install Docker if missing
if ! command -v docker &> /dev/null; then
  echo -e "${CYAN}→ Installing Docker...${NC}"
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
  echo -e "${GREEN}✓ Docker installed${NC}"
else
  echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Create directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

mkdir -p config/work config/conf

# Copy default config if not exists
if [[ ! -f config/conf/AdGuardHome.yaml ]]; then
  echo -e "${CYAN}→ Using default AdGuard Home config${NC}"
fi

# Free port 53 if occupied by systemd-resolved
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
  echo -e "${CYAN}→ Disabling systemd-resolved (frees port 53)...${NC}"
  systemctl disable --now systemd-resolved
  # Point resolv.conf to a public DNS temporarily
  echo "nameserver 1.1.1.1" > /etc/resolv.conf
  echo "nameserver 8.8.8.8" >> /etc/resolv.conf
fi

# Start stack
echo -e "${CYAN}→ Starting OpenAccess DNS (AdGuard Home)...${NC}"
docker compose up -d

sleep 3

IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║           Deploy complete!               ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Web UI:  http://${IP}:3000"
echo "║  DNS:     ${IP}  (port 53)"
echo "║"
echo "║  First login: set password in the UI"
echo "║  Then configure DoH/DoT with your domain"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "Useful commands:"
echo "  docker compose logs -f"
echo "  docker compose restart"
echo "  docker compose down"
