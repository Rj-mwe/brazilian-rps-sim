"""
Data Transfer Objects (DTOs) de Entrada e Saída da Camada de Aplicação.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SimulationStepRequestDTO:
    sim_time_sec: float
    step_size_sec: float = 0.0


@dataclass
class SimulationClockTickDTO:
    """Pulso de relógio emitido por um Master Clock (ex: Gazebo /clock ou nó de temporização)."""
    sim_time_sec: float
    is_paused: bool = False
    step_size_sec: float = 0.0


@dataclass
class PauseSimulationRequestDTO:
    """Comando de pausa ou retomada da simulação."""
    paused: bool


@dataclass
class SetTimeMultiplierRequestDTO:
    """Comando de ajuste da taxa de aceleração temporal da simulação."""
    multiplier: float


@dataclass
class SimulationSessionStateDTO:
    """Estado soberano da sessão de simulação mantido no Core."""
    sim_time_sec: float
    is_paused: bool
    time_multiplier: float
    mode: str  # "MASTER_GAZEBO", "STANDALONE_AUTONOMOUS"
    elevation_mask_deg: float
    selected_station_name: str


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
    satellites: List[SatelliteTelemetryResponseDTO] = field(default_factory=list)
    sim_time_sec: float = 0.0
