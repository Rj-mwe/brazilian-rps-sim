"""
Porta de Saída (Contrato abstrato) para publicação/despacho de telemetria orbital e dados astronômicos.
"""

from abc import ABC, abstractmethod
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.QuaternionVO import QuaternionVO

class ITelemetryOutboundPort(ABC):
    @abstractmethod
    def publish_satellite_state(self, sat_id: int, name: str, sat_type: str,
                                r_ecef: Vector3DVO, geodetic: GeodeticCoordinatesVO,
                                attitude: QuaternionVO, t_sec: float) -> None:
        """Despacha o estado cinemático e geodésico de um satélite para o mundo exterior."""
        pass

    @abstractmethod
    def publish_celestial_state(self, celestial_state: dict) -> None:
        """Despacha o estado astronômico Sol-Terra-Lua para o mundo exterior."""
        pass
