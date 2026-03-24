#!/usr/bin/env bash
# bootstrap.sh — First-time local dev setup for Boilerworks.
# Safe to re-run; skips steps already done.
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "  ${CYAN}→${NC} $*"; }
ok()      { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}⚠${NC} $*"; }
die()     { echo -e "  ${RED}✗${NC} $*" >&2; exit 1; }
banner()  { echo -e "\n${BOLD}${CYAN}▶ $*${NC}"; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$REPO_DIR/backend/config/local.env"
EXAMPLE_ENV="$REPO_DIR/backend/config/example.env"
LEGACY_ENV="$REPO_DIR/backend/config/.local.env"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║      Boilerworks Bootstrap           ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════╝${NC}"

# ── 1. Dependencies ──────────────────────────────────────────────────────────
banner "Checking dependencies"

command -v docker &>/dev/null || die "Docker not found. Install Docker Desktop: https://docs.docker.com/get-docker/"
ok "docker $(docker --version | awk '{print $3}' | tr -d ',')"

docker compose version &>/dev/null || die "docker compose (v2) not found. Upgrade Docker Desktop."
ok "docker compose $(docker compose version --short 2>/dev/null || echo 'v2')"

# ── 2. Environment file ───────────────────────────────────────────────────────
banner "Environment file"

if [[ -f "$ENV_FILE" ]]; then
    ok "backend/config/local.env already exists — skipping"
elif [[ -f "$LEGACY_ENV" ]]; then
    cp "$LEGACY_ENV" "$ENV_FILE"
    ok "Migrated .local.env → local.env"
    warn "You can delete backend/config/.local.env — it's no longer used"
else
    cp "$EXAMPLE_ENV" "$ENV_FILE"
    ok "Created backend/config/local.env from example.env"
    warn "Open backend/config/local.env and fill in any required values"
fi

# ── 3. Django secret key ──────────────────────────────────────────────────────
banner "Django secret key"

if grep -q "changeme-generate" "$ENV_FILE" 2>/dev/null; then
    if command -v python3 &>/dev/null; then
        SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
        # Portable sed for macOS and Linux
        sed -i.bak "s|changeme-generate-a-long-random-secret-key-here|$SECRET|" "$ENV_FILE"
        rm -f "$ENV_FILE.bak"
        ok "Generated DJANGO_SECRET_KEY"
    else
        warn "python3 not found — set DJANGO_SECRET_KEY manually in backend/config/local.env"
    fi
else
    ok "DJANGO_SECRET_KEY already set"
fi

# ── 4. Docker image ───────────────────────────────────────────────────────────
banner "Docker image"

cd "$REPO_DIR/docker"
if docker image inspect boilerworks-local &>/dev/null; then
    ok "Image 'boilerworks-local' exists"
    read -r -p "  Rebuild image? [y/N] " REBUILD
    if [[ "${REBUILD,,}" == "y" ]]; then
        info "Building (this takes a few minutes on first run)..."
        docker compose build boilerworks-local
        ok "Image rebuilt"
    fi
else
    info "Building Docker image (this takes a few minutes on first run)..."
    docker compose build boilerworks-local
    ok "Image built"
fi

# ── 5. Done ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}Bootstrap complete!${NC}"
echo ""
echo -e "  ${CYAN}./run.sh${NC}          Start the full stack"
echo -e "  ${CYAN}./run.sh help${NC}     Show all available commands"
echo ""
