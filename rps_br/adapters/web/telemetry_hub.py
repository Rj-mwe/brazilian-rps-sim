"""
Compatibilidade retroativa: rps_br.adapters.web.telemetry_hub.
A implementação canônica reside em rps_br.adapters.api.telemetry_hub.
"""

from rps_br.adapters.api.telemetry_hub import TelemetryHub, BRAZILIAN_GROUND_STATIONS

__all__ = ["TelemetryHub", "BRAZILIAN_GROUND_STATIONS"]
