"""
Value Object: PvtSolutionVO
===========================
Representa a solução de navegação PVT (Position, Velocity, Time) calculada
pelo receptor GNSS a partir de observáveis de pseudodistância.

Atributos:
    position_ecef_m: Vetor 3D da posição estimada no referencial terrestre ECEF (metros).
    geodetic: Coordenadas geodésicas equivalentes WGS-84 (Latitude °, Longitude °, Altitude km).
    receiver_clock_bias_m: Desvio do oscilador local em metros (c * δt_rx).
    receiver_clock_bias_s: Desvio do oscilador local em segundos (δt_rx).
    residuals_m: Dicionário mapeando satélite -> resíduo de pseudodistância pós-ajuste em metros.
    iterations_count: Número de iterações executadas pelo algoritmo de mínimos quadrados.
    is_converged: Flag booleana indicando se o critério de tolerância foi satisfeito.
    dop: Métricas de Diluição de Precisão Geométrica (DopResultVO) associadas à época.
    position_error_3d_m: Erro de posição 3D Euclidiano em metros (se verdade terrestre fornecida).
"""

from dataclasses import dataclass
from typing import Optional, Dict

from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.navigation_pvt.value_objects.DopResultVO import DopResultVO


@dataclass(frozen=True)
class PvtSolutionVO:
    position_ecef_m: Vector3DVO
    geodetic: GeodeticCoordinatesVO
    receiver_clock_bias_m: float
    receiver_clock_bias_s: float
    residuals_m: Dict[str, float]
    iterations_count: int
    is_converged: bool
    dop: Optional[DopResultVO] = None
    position_error_3d_m: Optional[float] = None

    def __post_init__(self) -> None:
        if self.iterations_count < 0:
            raise ValueError(f"iterations_count não pode ser negativo: {self.iterations_count}")
