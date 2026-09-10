#!/usr/bin/env python3
"""
Streaming WebSocket API: telemetry_ws
======================================
Canal de comunicação bidirecional em tempo real para envio contínuo de telemetria
e recebimento de comandos interativos de clientes web e operadores externos.
"""

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from rps_br.adapters.api.telemetry_hub import TelemetryHub

logger = logging.getLogger("rps_api.streaming")

router = APIRouter(tags=["Streaming WebSocket"])


class WebSocketConnectionManager:
    """Gerenciador thread-safe de conexões WebSocket ativas."""

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


ws_manager = WebSocketConnectionManager()


@router.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """Canal WebSocket bidirecional com streaming de telemetria e comandos de controle."""
    await ws_manager.connect(websocket)
    hub = TelemetryHub.get_instance()

    # Envia primeiro snapshot de imediato na conexão
    try:
        initial_data = json.dumps(hub.get_snapshot())
        await websocket.send_text(initial_data)

        while True:
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
            except Exception as e:
                logger.debug("Erro ao processar comando WS: %s", e)
    except (WebSocketDisconnect, Exception):
        ws_manager.disconnect(websocket)


async def simulation_stepper_loop():
    """Loop assíncrono em background para propagação contínua e broadcast (1 Hz)."""
    hub = TelemetryHub.get_instance()
    last_time = asyncio.get_event_loop().time()
    while True:
        await asyncio.sleep(1.0)
        now = asyncio.get_event_loop().time()
        dt_wall = now - last_time
        last_time = now

        hub.step(dt_wall)

        if ws_manager.active_connections:
            snapshot = hub.get_snapshot()
            await ws_manager.broadcast(json.dumps(snapshot))
