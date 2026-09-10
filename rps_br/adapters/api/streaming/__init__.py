"""
Módulo de Streaming em Tempo Real (WebSockets).
"""

from .telemetry_ws import router as ws_router, ws_manager, simulation_stepper_loop

__all__ = ["ws_router", "ws_manager", "simulation_stepper_loop"]
