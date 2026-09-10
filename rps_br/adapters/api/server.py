#!/usr/bin/env python3
"""
Servidor Gateway de API e Centro de Controle: server.py
======================================================
Ponto de entrada unificado para todas as interfaces de comunicação externa:
- REST API (telemetria, DOP, atrasos atmosféricos, controle de execução)
- WebSocket Streaming a 1 Hz
- NMEA 0183 ($GNGGA, $GNGSA, $GPGSV)
- Cesium 3D Geoespacial (/cesium/viewer e /cesium/constellation.czml)
- Interface de Usuário SPA (/ -> adapters/ui/index.html)
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rps_br.adapters.api.rest import (
    telemetry_router,
    navigation_router,
    atmosphere_router,
    control_router,
    internal_router,
)
from rps_br.adapters.api.streaming import ws_router, simulation_stepper_loop
from rps_br.adapters.api.nmea import nmea_router
from rps_br.adapters.cesium import cesium_router

background_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida do motor de simulação e streaming em segundo plano."""
    global background_task
    background_task = asyncio.create_task(simulation_stepper_loop())
    yield
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="🛰️ SPR-BR / RPS-BR Mission Control API Gateway",
    description=(
        "Gateway Unificado de APIs e Telemetria da Constelação Regional Brasileira (7 Satélites). "
        "Engloba rotas RESTful, streaming WebSocket, protocolo NMEA 0183 e visualização 3D Cesium/CZML."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS irrestrito para integrações
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão dos Roteadores Modulares
app.include_router(telemetry_router)
app.include_router(navigation_router)
app.include_router(atmosphere_router)
app.include_router(control_router)
app.include_router(internal_router)
app.include_router(ws_router)
app.include_router(nmea_router)
app.include_router(cesium_router)

# Diretório Frontend da Interface de Usuário (adapters/ui)
UI_DIR = Path(__file__).resolve().parent.parent / "ui"
if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


@app.get("/", summary="Dashboard Web de Controle de Missão")
async def serve_dashboard():
    """Serve a Single-Page Application (SPA) do Centro de Controle."""
    index_path = UI_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "RPS-BR Mission Control API Gateway Ativo. Acesse /docs para Swagger ou /cesium/viewer para o globo 3D."}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
