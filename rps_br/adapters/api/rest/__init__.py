"""
Roteadores RESTful do Gateway de API do RPS-BR.
"""

from .telemetry import router as telemetry_router
from .navigation import router as navigation_router
from .atmosphere import router as atmosphere_router
from .control import router as control_router
from .internal import router as internal_router

__all__ = [
    "telemetry_router",
    "navigation_router",
    "atmosphere_router",
    "control_router",
    "internal_router",
]
