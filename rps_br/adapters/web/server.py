#!/usr/bin/env python3
"""
Servidor Web FastAPI e Streaming de Telemetria da Constelação RPS-BR.
Padrão Hexagonal: Adaptador Web de Nível 2 (Modular).
"""

import asyncio
import json
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rps_br.adapters.web.telemetry_hub import TelemetryHub
from rps_br.adapters.web.routes.telemetry import router as telemetry_router
from rps_br.adapters.web.routes.navigation import router as navigation_router
from rps_br.adapters.web.routes.atmosphere import router as atmosphere_router
from rps_br.adapters.web.routes.control import router as control_router


# Gerenciador de Ciclo de Vida (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(simulation_stepper_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# Configuração do App FastAPI
app = FastAPI(
    title="🛰️ RPS-BR Mission Control API",
    description=(
        "API REST e WebSocket de Telemetria do Sistema de Posicionamento Regional Brasileiro (7 Satélites). "
        "Permite o monitoramento contínuo de órbitas, qualidade PVT (DOP) e retardo troposférico (Saastamoinen)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Habilita CORS irrestrito para desenvolvimento e integração
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conecta os Roteadores REST
app.include_router(telemetry_router)
app.include_router(navigation_router)
app.include_router(atmosphere_router)
app.include_router(control_router)

# Diretório Frontend estático
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", summary="Dashboard Web de Controle de Missão")
async def serve_dashboard():
    """Serve a Single-Page Application (SPA) do Centro de Controle."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "RPS-BR Mission Control API Online. Acesse /docs para a documentação interativa."}


# Gerenciador de Clientes WebSocket Ativos
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str):
        disconnected = set()
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                disconnected.add(conn)
        for dead_conn in disconnected:
            self.active_connections.discard(dead_conn)


manager = ConnectionManager()


@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """Canal WebSocket bidirecional com streaming de telemetria a 1 Hz."""
    await manager.connect(websocket)
    hub = TelemetryHub.get_instance()
    
    # Envia primeiro snapshot de imediato na conexão
    try:
        initial_data = json.dumps(hub.get_snapshot())
        await websocket.send_text(initial_data)
        
        while True:
            # Escuta eventuais comandos de entrada do cliente
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                if "pause" in cmd:
                    hub.set_paused(bool(cmd["pause"]))
                if "multiplier" in cmd:
                    hub.set_time_multiplier(float(cmd["multiplier"]))
                if "mask" in cmd:
                    hub.set_elevation_mask(float(cmd["mask"]))
                if "station" in cmd:
                    hub.set_station(str(cmd["station"]))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Tarefa em segundo plano: Avança a simulação e transmite snapshots via WebSocket a 1 Hz
background_task = None

async def simulation_stepper_loop():
    hub = TelemetryHub.get_instance()
    last_time = asyncio.get_event_loop().time()
    while True:
        await asyncio.sleep(1.0)
        now = asyncio.get_event_loop().time()
        dt_wall = now - last_time
        last_time = now
        
        hub.step(dt_wall)
        
        if manager.active_connections:
            snapshot = hub.get_snapshot()
            await manager.broadcast(json.dumps(snapshot))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
