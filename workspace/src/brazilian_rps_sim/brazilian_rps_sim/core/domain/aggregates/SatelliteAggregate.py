"""
Agregado representando um Satélite da Constelação com identidade, barramento, estado cinemático e atitude Nadir.
"""

from dataclasses import dataclass, field
import numpy as np
from brazilian_rps_sim.core.domain.value_objects.KeplerianElementsVO import KeplerianElementsVO
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.value_objects.QuaternionVO import QuaternionVO
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.policies.KeplerianPropagationPolicy import KeplerianPropagationPolicy
from brazilian_rps_sim.core.domain.services.CoordinateTransformService import CoordinateTransformService

@dataclass
class SatelliteAggregate:
    sat_id: int
    name: str
    sat_type: str # "GEO" ou "IGSO"
    elements: KeplerianElementsVO
    station_lon_deg: float = 0.0

    # Estado Dinâmico Instanciado
    r_eci: Vector3DVO = field(default_factory=lambda: Vector3DVO(0.0, 0.0, 0.0))
    v_eci: Vector3DVO = field(default_factory=lambda: Vector3DVO(0.0, 0.0, 0.0))
    r_ecef: Vector3DVO = field(default_factory=lambda: Vector3DVO(0.0, 0.0, 0.0))
    geodetic: GeodeticCoordinatesVO = field(default_factory=lambda: GeodeticCoordinatesVO(0.0, 0.0, 0.0))
    attitude_nadir: QuaternionVO = field(default_factory=QuaternionVO.identity)
    last_sim_time_sec: float = -1.0

    def propagate_to(self, t_sec: float, mu: float = 398600.4418) -> None:
        """Propaga o satélite para o instante t_sec e calcula o apontamento Nadir em direção ao centro da Terra."""
        r_eci_vo, v_eci_vo = KeplerianPropagationPolicy.propagate(self.elements, t_sec, mu)
        self.r_eci = r_eci_vo
        self.v_eci = v_eci_vo

        # Converte para ECEF e coordenadas Geodésicas
        r_ecef_np = CoordinateTransformService.eci_to_ecef(r_eci_vo.to_numpy(), t_sec)
        self.r_ecef = Vector3DVO.from_numpy(r_ecef_np)
        self.geodetic = CoordinateTransformService.ecef_to_geodetic(r_ecef_np)

        # Cálculo do Apontamento Nadir (Eixo Z do satélite apontando para o centro da Terra)
        dir_to_earth = -r_ecef_np / np.linalg.norm(r_ecef_np)
        self.attitude_nadir = QuaternionVO.from_two_vectors(np.array([0.0, 0.0, 1.0]), dir_to_earth)
        self.last_sim_time_sec = t_sec
