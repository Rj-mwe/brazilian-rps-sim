"""
Adaptador Web do Sistema de Posicionamento Regional Brasileiro (RPS-BR).
Fornece API RESTful (FastAPI), streaming WebSocket a 1 Hz e Dashboard Web de Missão.
Carregamento sob demanda (lazy import) para garantir compatibilidade em nós ROS 2 mínimos.
"""

from typing import Any
from .telemetry_hub import TelemetryHub


def __getattr__(name: str) -> Any:
    if name in ("app", "run_server"):
        from .server import app, run_server
        if name == "app":
            return app
        return run_server
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["app", "run_server", "TelemetryHub"]
