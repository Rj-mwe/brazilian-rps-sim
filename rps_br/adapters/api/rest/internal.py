#!/usr/bin/env python3
"""
Rotas Internas de Sincronização do Adaptador Web (Gateway de Relógio Master).
Permite que o nó ROS 2 ou bridges de simulação injetem pulsos de /clock no Core.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Dict

from rps_br.core.application.services.SimulationSessionService import SimulationSessionService
from rps_br.core.application.dtos.SimulationDTOs import SimulationClockTickDTO
from rps_br.adapters.api.telemetry_hub import TelemetryHub

router = APIRouter(prefix="/api/internal", tags=["Sincronização Interna"])


class ClockTickRequest(BaseModel):
    sim_time: float = Field(..., description="Tempo de simulação atual em segundos (do /clock do Gazebo/ROS 2)")
    is_paused: bool = Field(False, description="Flag indicando se a física do Gazebo está pausada")


@router.post("/clock", summary="Ingestão de pulso do Master Clock (Gazebo Sim / ROS 2)")
def ingest_clock_tick(req: ClockTickRequest) -> Dict[str, Any]:
    session = SimulationSessionService.get_instance()
    session.ingest_clock_tick(SimulationClockTickDTO(
        sim_time_sec=req.sim_time,
        is_paused=req.is_paused
    ))
    
    # Atualiza o snapshot analítico do TelemetryHub
    hub = TelemetryHub.get_instance()
    hub.sync_with_session()
    
    return {
        "status": "synchronized",
        "sim_time": req.sim_time,
        "is_paused": req.is_paused,
        "mode": "MASTER_GAZEBO"
    }
