#!/usr/bin/env python3
"""Rotas REST para telemetria de satélites e estado da simulação."""

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from rps_br.adapters.api.telemetry_hub import TelemetryHub

router = APIRouter(prefix="/api", tags=["Telemetria"])


@router.get("/status", summary="Obter status geral da simulação")
def get_simulation_status() -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    snapshot = hub.get_snapshot()
    return {
        "status": "online",
        "simulation": snapshot["simulation"],
        "dop": snapshot["dop"],
        "active_satellites_count": len(snapshot["satellites"])
    }


@router.get("/satellites", summary="Listar telemetria dos 7 satélites da constelação")
def get_all_satellites() -> List[Dict[str, Any]]:
    hub = TelemetryHub.get_instance()
    return hub.get_snapshot()["satellites"]


@router.get("/satellites/{sat_id}", summary="Obter dados de um satélite específico (1 a 7)")
def get_satellite_by_id(sat_id: int) -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    sats = hub.get_snapshot()["satellites"]
    sat = next((s for s in sats if s["id"] == sat_id), None)
    if not sat:
        raise HTTPException(status_code=404, detail=f"Satélite PRN {sat_id} não encontrado")
    return sat
