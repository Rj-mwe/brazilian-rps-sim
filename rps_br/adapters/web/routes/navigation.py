#!/usr/bin/env python3
"""Rotas REST para métricas de Navegação e PVT (DOP, Visibilidade)."""

from fastapi import APIRouter
from typing import Any, Dict, List

from rps_br.adapters.web.telemetry_hub import TelemetryHub

router = APIRouter(prefix="/api", tags=["Navegação e PVT"])


@router.get("/dop", summary="Obter métricas de DOP (GDOP, PDOP, HDOP, VDOP) da estação atual")
def get_current_dop() -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    snapshot = hub.get_snapshot()
    return {
        "station": snapshot["simulation"]["station_name"],
        "dop": snapshot["dop"],
        "elevation_mask_deg": snapshot["simulation"]["elevation_mask_deg"],
    }


@router.get("/stations", summary="Listar estações terrestres de monitoramento disponíveis")
def get_available_stations() -> List[str]:
    hub = TelemetryHub.get_instance()
    return hub.get_snapshot()["stations"]


@router.get("/history", summary="Obter histórico recente de DOP para plotagem de gráficos")
def get_dop_history() -> List[Dict[str, Any]]:
    hub = TelemetryHub.get_instance()
    return hub.get_snapshot()["history"]
