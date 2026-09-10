#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialização do Gateway de APIs & Dashboard Web do RPS-BR
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${WEB_DASHBOARD_PORT:-8000}"
HOST="${WEB_DASHBOARD_HOST:-0.0.0.0}"

echo "===================================================================="
echo "🛰️  Iniciando RPS-BR Mission Control & API Gateway"
echo "🌐  Dashboard de Operações:    http://localhost:${PORT}"
echo "🌍  Globo 3D Cesium (WGS84):   http://localhost:${PORT}/cesium/viewer"
echo "⚡  Documentação Swagger:      http://localhost:${PORT}/docs"
echo "📡  API NMEA 0183 (u-center):   http://localhost:${PORT}/api/nmea/sentences"
echo "===================================================================="

exec python3 -m uvicorn rps_br.adapters.api.server:app --host "${HOST}" --port "${PORT}" --reload "$@"
