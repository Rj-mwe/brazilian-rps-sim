#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialização do Dashboard Web do RPS-BR (FastAPI + WebSockets)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${WEB_DASHBOARD_PORT:-8000}"
HOST="${WEB_DASHBOARD_HOST:-0.0.0.0}"

echo "===================================================================="
echo "🛰️  Iniciando Painel de Controle e Telemetria Web do RPS-BR"
echo "🌐  Acesse o Dashboard em: http://localhost:${PORT}"
echo "⚡  Documentação Swagger:   http://localhost:${PORT}/docs"
echo "===================================================================="

exec python3 -m uvicorn rps_br.adapters.web.server:app --host "${HOST}" --port "${PORT}" "$@"
