"""
Data Transfer Objects (DTOs) de Entrada e Saída da Camada de Aplicação.
"""

from dataclasses import dataclass, field

@dataclass
class SimulationStepRequestDTO:
    sim_time_sec: float
    step_size_sec: float = 0.0

@dataclass
class SatelliteTelemetryResponseDTO:
    id: int
    name: str
    type: str
    latitude_deg: float
    longitude_deg: float
    altitude_km: float
    x_ecef_km: float
    y_ecef_km: float
    z_ecef_km: float
    qx: float
    qy: float
    qz: float
    qw: float
    sim_time_sec: float

@dataclass
class ConstellationStatusResponseDTO:
    satellites: list[SatelliteTelemetryResponseDTO] = field(default_factory=list)
    sim_time_sec: float = 0.0
