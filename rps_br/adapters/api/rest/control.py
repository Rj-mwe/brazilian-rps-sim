#!/usr/bin/env python3
"""Rotas REST para controle interativo e comandos de simulação (Inbound)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from rps_br.adapters.api.telemetry_hub import TelemetryHub

router = APIRouter(prefix="/api/control", tags=["Controle da Simulação"])


class PauseRequest(BaseModel):
    paused: bool = Field(..., description="True para pausar, False para retomar")


class MultiplierRequest(BaseModel):
    multiplier: float = Field(..., ge=0.1, le=86400.0, description="Fator de aceleração do tempo")


class ElevationMaskRequest(BaseModel):
    elevation_mask_deg: Optional[float] = Field(None, ge=0.0, le=45.0, description="Ângulo de corte da máscara de elevação em graus")
    mask_deg: Optional[float] = Field(None, ge=0.0, le=45.0, description="Alias para elevation_mask_deg")

    @property
    def value(self) -> float:
        if self.elevation_mask_deg is not None:
            return self.elevation_mask_deg
        if self.mask_deg is not None:
            return self.mask_deg
        return 5.0


class StationRequest(BaseModel):
    station_name: str = Field(..., description="Nome da estação terrestre")


@router.post("/pause", summary="Pausar ou retomar a simulação")
def set_pause_state(req: PauseRequest) -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    hub.set_paused(req.paused)
    return {"message": "Estado de pausa atualizado", "paused": req.paused}


@router.post("/multiplier", summary="Definir multiplicador de velocidade temporal (1x, 10x, 3600x)")
@router.post("/speed", summary="Alias para definir multiplicador de velocidade temporal")
def set_multiplier(req: MultiplierRequest) -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    hub.set_time_multiplier(req.multiplier)
    return {"message": "Multiplicador atualizado", "multiplier": req.multiplier}


@router.post("/mask", summary="Alterar máscara de elevação da estação de solo")
def set_elevation_mask(req: ElevationMaskRequest) -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    val = req.value
    hub.set_elevation_mask(val)
    return {"message": "Máscara de elevação atualizada", "elevation_mask_deg": val}


@router.post("/station", summary="Selecionar estação terrestre de monitoramento ativa")
def select_station(req: StationRequest) -> Dict[str, Any]:
    hub = TelemetryHub.get_instance()
    success = hub.set_station(req.station_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Estação '{req.station_name}' não encontrada")
    return {"message": "Estação atualizada", "station": req.station_name}
