#!/usr/bin/env python3
"""Rotas REST para propagação de sinais e perturbações atmosféricas (Saastamoinen e Klobuchar)."""

from fastapi import APIRouter
from typing import Any, Dict

from rps_br.adapters.web.telemetry_hub import TelemetryHub

router = APIRouter(prefix="/api", tags=["Propagação e Atmosfera"])


@router.get("/delays", summary="Obter atrasos troposféricos e ionosféricos por satélite")
def get_atmospheric_delays() -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    snapshot = hub.get_snapshot()
    return {
        "model_troposphere": "Saastamoinen (1972) Determinístico",
        "model_ionosphere": "Klobuchar (Broadcast L1)",
        "station": snapshot["simulation"]["station_name"],
        "delays_by_satellite": snapshot["atmospheric"],
    }
