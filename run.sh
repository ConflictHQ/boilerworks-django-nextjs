#!/usr/bin/env bash
# run.sh — Boilerworks local dev command center.
# Usage: ./run.sh [command] [args]
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "  ${CYAN}→${NC} $*"; }
ok()      { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}⚠${NC} $*"; }
die()     { echo -e "  ${RED}✗${NC} $*" >&2; exit 1; }
banner()  { echo -e "\n${BOLD}${CYAN}▶ $*${NC}"; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$REPO_DIR/backend/config/local.env"
COMPOSE="docker compose -f $REPO_DIR/docker/docker-compose.yaml"
CONTAINER="boilerworks-local"
APP_HOST="boilerworks.local"
BASE_PORT=8000

# Auto-bootstrap if env file is missing
if [[ ! -f "$ENV_FILE" ]]; then
    warn "local.env not found — running bootstrap..."
    bash "$REPO_DIR/bootstrap.sh"
    echo ""
fi

CMD="${1:-up}"
shift 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────

_require_running() {
    docker inspect "$CONTAINER" --format '{{.State.Running}}' 2>/dev/null | grep -q true \
        || die "$CONTAINER is not running. Start it with: ./run.sh up"
}

_urls() {
    echo ""
    echo -e "  Frontend         ${CYAN}http://localhost:3000${NC}"
    echo -e "  App              ${CYAN}http://localhost:$BASE_PORT/app/${NC}"
    echo -e "  Admin            ${CYAN}http://localhost:$BASE_PORT/app/admin/${NC}"
    echo -e "  Health           ${CYAN}http://localhost:$BASE_PORT/health/${NC}"
    echo -e "  GraphQL          ${CYAN}http://localhost:$BASE_PORT/app/gql/config/${NC}"
    echo -e "  Django metrics   ${CYAN}http://localhost:$BASE_PORT/metrics${NC}"
    echo -e "  Postgres metrics ${CYAN}http://localhost:9187/metrics${NC}"
    echo -e "  Redis metrics    ${CYAN}http://localhost:9121/metrics${NC}"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────

case "$CMD" in

    # ── Stack management ─────────────────────────────────────────────────────

    up|start)
        banner "Starting Boilerworks"
        $COMPOSE up -d
        info "Waiting for services to be healthy..."
        sleep 4
        echo ""
        $COMPOSE ps
        _urls
        info "Tip: ./run.sh logs   to tail the Django container"
        ;;

    stop|down)
        banner "Stopping Boilerworks"
        $COMPOSE down
        ok "Stack stopped"
        ;;

    restart)
        banner "Restarting Django container"
        $COMPOSE restart "$CONTAINER"
        ok "Restarted"
        ;;

    rebuild|build)
        banner "Rebuilding Docker images"
        $COMPOSE build --no-cache boilerworks-local ui
        ok "Images rebuilt — run ./run.sh restart to apply"
        ;;

    status|ps)
        $COMPOSE ps
        ;;

    # ── Logs ─────────────────────────────────────────────────────────────────

    logs)
        LINES="${1:-}"
        if [[ -n "$LINES" && "$LINES" =~ ^[0-9]+$ ]]; then
            $COMPOSE logs --tail="$LINES" "$CONTAINER"
        else
            $COMPOSE logs -f "$CONTAINER"
        fi
        ;;

    logs-all)
        $COMPOSE logs -f
        ;;

    # ── Health ───────────────────────────────────────────────────────────────

    health)
        banner "Health check"
        HEALTH_URL="http://localhost:$BASE_PORT/health/"
        HTML=$(curl -s -H "Host: $APP_HOST" "$HEALTH_URL" 2>/dev/null) || die "Could not reach $HEALTH_URL — is the stack running? (./run.sh up)"

        python3 - "$HTML" << 'PYEOF'
import sys, re, html as html_mod

text = sys.argv[1]
is_error = 'thead-error' in text or '🔥' in text

status_color = '\033[0;31m' if is_error else '\033[0;32m'
status_label = 'DEGRADED' if is_error else 'HEALTHY'
print(f"\n  Overall: {status_color}{status_label}\033[0m\n")

for row in re.findall(r'<tr[^>]*>(.*?)</tr>', text, re.DOTALL):
    if '<th' in row:
        continue
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    if len(cells) < 2:
        continue
    svc  = re.sub(r'<[^>]+>', '', html_mod.unescape(cells[0])).strip()
    stat = re.sub(r'<[^>]+>', '', html_mod.unescape(cells[1])).strip()
    if not svc:
        continue
    ok_svc = stat.lower() in ('working', 'ok')
    color  = '\033[0;32m' if ok_svc else '\033[0;31m'
    icon   = '✓' if ok_svc else '✗'
    print(f"  {color}{icon}\033[0m  {svc}: {stat}")
print()
PYEOF
        ;;

    # ── Django management ────────────────────────────────────────────────────

    manage|m)
        _require_running
        docker exec -it "$CONTAINER" python manage.py "$@"
        ;;

    shell)
        banner "Django shell"
        _require_running
        docker exec -it "$CONTAINER" python manage.py shell
        ;;

    bash)
        banner "Container bash"
        _require_running
        docker exec -it "$CONTAINER" bash
        ;;

    migrate)
        banner "Running migrations"
        _require_running
        docker exec -it "$CONTAINER" python manage.py migrate "$@"
        ok "Done"
        ;;

    makemigrations|mm)
        banner "Making migrations"
        _require_running
        docker exec -it "$CONTAINER" python manage.py makemigrations "$@"
        ;;

    superuser)
        banner "Create superuser"
        _require_running
        docker exec -it "$CONTAINER" python manage.py createsuperuser
        ;;

    test)
        banner "Running tests"
        _require_running
        docker exec -it "$CONTAINER" python manage.py test "$@"
        ;;

    # ── Dev utilities ────────────────────────────────────────────────────────

    schema)
        banner "Generating GraphQL schema"
        _require_running
        docker exec -it "$CONTAINER" python manage.py dev_utils --generate_schema
        ok "Written to backend/static/gql/schema.graphql"
        ;;

    perms)
        banner "Generating permissions enum"
        _require_running
        docker exec -it "$CONTAINER" python manage.py dev_utils --gen_perms
        ok "Written to backend/config/roles_gen.py"
        ;;

    loaddata)
        banner "Loading fixtures"
        _require_running
        docker exec -it "$CONTAINER" python manage.py dev_utils --loaddata
        ok "Fixtures loaded"
        ;;

    dumpdata)
        banner "Dumping fixtures"
        _require_running
        docker exec -it "$CONTAINER" python manage.py dev_utils --dumpdata
        ok "Fixtures written"
        ;;

    seed)
        banner "Loading seed data"
        _require_running
        docker exec -it "$CONTAINER" python manage.py seed "$@"
        ok "Seed data loaded"
        ;;

    lint)
        banner "Running linters"
        _require_running
        docker exec "$CONTAINER" python -m flake8 --max-line-length=140
        docker exec "$CONTAINER" python -m isort --check-only .
        ok "All clean"
        ;;

    features)
        banner "Feature toggles"
        _require_running
        docker exec "$CONTAINER" python manage.py features
        ;;

    scaffold)
        banner "Scaffolding"
        _require_running
        docker exec -it "$CONTAINER" python manage.py scaffold "$@"
        ;;

    export-schema|platform)
        banner "Exporting platform schema"
        _require_running
        docker exec "$CONTAINER" python manage.py export_platform_schema --pretty
        ;;

    # ── Nuclear options ──────────────────────────────────────────────────────

    reset)
        banner "Reset local database"
        warn "This destroys all local data (postgres volume). Ctrl+C to cancel (5s)..."
        sleep 5
        $COMPOSE down -v
        $COMPOSE up -d
        ok "Database wiped and stack restarted"
        ;;

    # ── Help ─────────────────────────────────────────────────────────────────

    help|-h|--help)
        echo ""
        echo -e "${BOLD}Usage:${NC}  ./run.sh [command] [args]"
        echo ""
        echo -e "${BOLD}Stack${NC}"
        echo -e "  ${CYAN}up${NC}                  Start all services (default)"
        echo -e "  ${CYAN}stop${NC}                Stop all services"
        echo -e "  ${CYAN}restart${NC}             Restart the Django container"
        echo -e "  ${CYAN}rebuild${NC}             Rebuild Docker image from scratch"
        echo -e "  ${CYAN}status${NC}              Show container status"
        echo -e "  ${CYAN}health${NC}              Show per-service health"
        echo -e "  ${CYAN}logs [N]${NC}            Tail Django logs (N = last N lines)"
        echo -e "  ${CYAN}logs-all${NC}            Tail all service logs"
        echo -e "  ${CYAN}reset${NC}               Wipe DB volume and restart ${RED}(destructive)${NC}"
        echo ""
        echo -e "${BOLD}Django${NC}"
        echo -e "  ${CYAN}shell${NC}               Django Python shell"
        echo -e "  ${CYAN}bash${NC}                Container bash"
        echo -e "  ${CYAN}manage <cmd>${NC}        Run any manage.py command"
        echo -e "  ${CYAN}migrate${NC}             Apply database migrations"
        echo -e "  ${CYAN}makemigrations [app]${NC} Create new migrations"
        echo -e "  ${CYAN}superuser${NC}           Create a superuser account"
        echo -e "  ${CYAN}test [app]${NC}          Run test suite"
        echo ""
        echo -e "${BOLD}Dev utilities${NC}"
        echo -e "  ${CYAN}seed${NC}                Load dev seed fixtures"
        echo -e "  ${CYAN}lint${NC}                Run flake8 + isort checks"
        echo -e "  ${CYAN}schema${NC}              Export GraphQL schema to static/gql/schema.graphql"
        echo -e "  ${CYAN}perms${NC}               Regenerate config/roles_gen.py permissions enum"
        echo -e "  ${CYAN}features${NC}            Show feature toggles and their status"
        echo -e "  ${CYAN}scaffold <args>${NC}     Scaffold a new app (e.g. scaffold app --name=crm)"
        echo -e "  ${CYAN}loaddata${NC}            Load fixtures via dev_utils"
        echo -e "  ${CYAN}dumpdata${NC}            Dump fixtures via dev_utils"
        echo ""
        echo -e "${BOLD}URLs (local)${NC}"
        _urls
        ;;

    *)
        die "Unknown command: $CMD — run ./run.sh help"
        ;;

esac
