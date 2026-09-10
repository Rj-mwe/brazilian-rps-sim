"""
Compatibilidade retroativa: rps_br.adapters.web
A arquitetura modular canônica reside em rps_br.adapters.api e rps_br.adapters.ui.
"""

from typing import Any
from rps_br.adapters.api.telemetry_hub import TelemetryHub


def __getattr__(name: str) -> Any:
    if name in ("app", "run_server"):
        from rps_br.adapters.api.server import app, run_server
        if name == "app":
            return app
        return run_server
    if name == "TelemetryHub":
        return TelemetryHub
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["app", "run_server", "TelemetryHub"]
