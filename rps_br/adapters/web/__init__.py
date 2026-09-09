"""
Adaptador Web do Sistema de Posicionamento Regional Brasileiro (RPS-BR).
Fornece API RESTful (FastAPI), streaming WebSocket a 1 Hz e Dashboard Web de Missão.
"""

from .server import app, run_server
from .telemetry_hub import TelemetryHub

__all__ = ["app", "run_server", "TelemetryHub"]
